"""
End-to-End Data Pipeline
Orchestrates the complete ETL process: Ingestion → Validation → Transformation → Loading
"""
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.ingestion.extractor import DataExtractor
from data_pipeline.validation.validator import DataValidator
from data_pipeline.validation.presets import get_cdc_basic_rules
from data_pipeline.transformation.transformer import DataTransformer
from data_pipeline.loading.loader import DataLoader
from utils.logger import logger


class DataPipeline:
    """
    End-to-end data pipeline orchestrator
    
    Processes CDC health data through the complete ETL pipeline:
    1. Ingestion: Extract data from CDC API
    2. Validation: Validate data quality
    3. Transformation: Clean and transform data
    4. Loading: Load into PostgreSQL
    """
    
    def __init__(
        self,
        extractor: Optional[DataExtractor] = None,
        validator: Optional[DataValidator] = None,
        transformer: Optional[DataTransformer] = None,
        loader: Optional[DataLoader] = None
    ):
        """
        Initialize pipeline with optional custom components
        
        Args:
            extractor: DataExtractor instance (creates default if not provided)
            validator: DataValidator instance (creates default if not provided)
            transformer: DataTransformer instance (creates default if not provided)
            loader: DataLoader instance (creates default if not provided)
        """
        self.extractor = extractor or DataExtractor()
        self.validator = validator or DataValidator()
        self.transformer = transformer or DataTransformer()
        self.loader = loader or DataLoader()
        
        # Add default validation rules
        if not self.validator.rules:
            self.validator.add_rules(get_cdc_basic_rules())
        
        logger.info("DataPipeline initialized")
    
    def run(
        self,
        dataset_id: str,
        dataset_name: Optional[str] = None,
        indicator_code: Optional[str] = None,
        indicator_name: Optional[str] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_resource_endpoint: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete ETL pipeline
        
        Args:
            dataset_id: CDC dataset ID (Socrata dataset ID)
            dataset_name: Human-readable dataset name
            indicator_code: Indicator code for database (e.g., "COVID_CASES")
            indicator_name: Indicator name for database
            limit: Maximum records to process (None = all)
            filters: Dictionary of filters for extraction (e.g., {"state": "CA"})
            
        Returns:
            Dictionary with pipeline execution results and statistics
        """
        dataset_name = dataset_name or dataset_id
        logger.info(f"Starting pipeline for dataset: {dataset_name}")
        
        results = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "indicator_code": indicator_code,
            "indicator_name": indicator_name,
            "stages": {}
        }
        
        try:
            # Stage 1: Ingestion
            logger.info("=" * 60)
            logger.info("STAGE 1: INGESTION")
            logger.info("=" * 60)
            
            extraction_result = self.extractor.extract_dataset(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                limit=limit,
                filters=filters,
                use_resource_endpoint=use_resource_endpoint
            )
            
            extraction_info = extraction_result["extraction_info"]
            records = extraction_result["records"]
            
            results["stages"]["ingestion"] = {
                "status": extraction_info["status"],
                "records_extracted": extraction_info["records_extracted"],
                "duration_seconds": extraction_info["extraction_duration_seconds"],
                "run_id": extraction_info["run_id"]
            }
            
            if extraction_info["status"] != "success":
                logger.error(f"Ingestion failed: {extraction_info.get('error')}")
                results["status"] = "failed"
                results["error"] = extraction_info.get("error")
                return results
            
            logger.info(f"✓ Ingestion complete: {len(records)} records extracted")
            
            if not records:
                logger.warning("No records extracted, stopping pipeline")
                results["status"] = "completed"
                results["message"] = "No records to process"
                return results
            
            # Stage 2: Validation
            logger.info("=" * 60)
            logger.info("STAGE 2: VALIDATION")
            logger.info("=" * 60)
            
            # Remove extraction metadata for validation (keep it for later)
            records_for_validation = [
                {k: v for k, v in record.items() if k != "_extraction_metadata"}
                for record in records
            ]
            
            validation_result = self.validator.validate_batch(records_for_validation)
            
            results["stages"]["validation"] = {
                "total_records": validation_result.total_records,
                "valid_records": validation_result.valid_records,
                "invalid_records": validation_result.invalid_records,
                "records_with_warnings": validation_result.records_with_warnings,
                "errors": validation_result.summary_errors[:10],  # Limit errors
                "warnings": validation_result.summary_warnings[:10]
            }
            
            valid_records = self.validator.get_valid_records(validation_result)
            invalid_records = self.validator.get_invalid_records(validation_result)
            
            logger.info(
                f"✓ Validation complete: {validation_result.valid_records} valid, "
                f"{validation_result.invalid_records} invalid"
            )
            
            if not valid_records:
                logger.error("No valid records after validation, stopping pipeline")
                results["status"] = "failed"
                results["error"] = "All records failed validation"
                return results
            
            # Re-attach extraction metadata to valid records
            valid_records_with_metadata = []
            for idx, valid_record in enumerate(valid_records):
                # Find original record with metadata
                original_record = records[validation_result.validation_results[idx].record_index]
                if "_extraction_metadata" in original_record:
                    valid_record["_extraction_metadata"] = original_record["_extraction_metadata"]
                valid_records_with_metadata.append(valid_record)
            
            # Stage 3: Transformation
            logger.info("=" * 60)
            logger.info("STAGE 3: TRANSFORMATION")
            logger.info("=" * 60)
            
            transformed_records = self.transformer.transform_batch(
                records=valid_records_with_metadata,
                indicator_code=indicator_code,
                indicator_name=indicator_name
            )
            
            results["stages"]["transformation"] = {
                "records_transformed": len(transformed_records)
            }
            
            logger.info(f"✓ Transformation complete: {len(transformed_records)} records transformed")
            
            if not transformed_records:
                logger.error("No records after transformation, stopping pipeline")
                results["status"] = "failed"
                results["error"] = "Transformation produced no records"
                return results
            
            # Stage 4: Loading
            logger.info("=" * 60)
            logger.info("STAGE 4: LOADING")
            logger.info("=" * 60)
            
            loading_result = self.loader.load_batch(
                records=transformed_records,
                data_source=dataset_name,
                indicator_code=indicator_code,
                indicator_name=indicator_name,
                run_id=extraction_info["run_id"]  # Use same run_id for traceability
            )
            
            results["stages"]["loading"] = {
                "run_id": loading_result["run_id"],
                "records_processed": loading_result["records_processed"],
                "records_inserted": loading_result["records_inserted"],
                "records_failed": loading_result["records_failed"],
                "status": loading_result["status"]
            }
            
            logger.info(
                f"✓ Loading complete: {loading_result['records_inserted']} inserted, "
                f"{loading_result['records_failed']} failed"
            )
            
            # Overall pipeline status
            if loading_result["status"] == "completed" and loading_result["records_inserted"] > 0:
                results["status"] = "completed"
                results["records_loaded"] = loading_result["records_inserted"]
            elif loading_result["records_inserted"] > 0:
                results["status"] = "partial"
                results["records_loaded"] = loading_result["records_inserted"]
            else:
                results["status"] = "failed"
                results["error"] = "No records loaded"
            
            logger.info("=" * 60)
            logger.info("PIPELINE COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Status: {results['status']}")
            logger.info(f"Records loaded: {results.get('records_loaded', 0)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            import traceback
            traceback.print_exc()
            results["status"] = "failed"
            results["error"] = str(e)
            return results
    
    def print_summary(self, results: Dict[str, Any]):
        """
        Print a human-readable summary of pipeline results
        
        Args:
            results: Results dictionary from run() method
        """
        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 60)
        print(f"\nDataset: {results.get('dataset_name', 'N/A')}")
        print(f"Status: {results.get('status', 'unknown')}")
        
        if "stages" in results:
            stages = results["stages"]
            
            if "ingestion" in stages:
                ing = stages["ingestion"]
                print(f"\n📥 Ingestion:")
                print(f"   Records extracted: {ing.get('records_extracted', 0)}")
                print(f"   Duration: {ing.get('duration_seconds', 0):.2f}s")
            
            if "validation" in stages:
                val = stages["validation"]
                print(f"\n✅ Validation:")
                print(f"   Valid: {val.get('valid_records', 0)}")
                print(f"   Invalid: {val.get('invalid_records', 0)}")
                if val.get('errors'):
                    print(f"   Errors: {len(val['errors'])} unique")
            
            if "transformation" in stages:
                trans = stages["transformation"]
                print(f"\n🔄 Transformation:")
                print(f"   Records transformed: {trans.get('records_transformed', 0)}")
            
            if "loading" in stages:
                load = stages["loading"]
                print(f"\n💾 Loading:")
                print(f"   Inserted: {load.get('records_inserted', 0)}")
                print(f"   Failed: {load.get('records_failed', 0)}")
                print(f"   Run ID: {load.get('run_id', 'N/A')}")
        
        if results.get("error"):
            print(f"\n❌ Error: {results['error']}")
        
        print("=" * 60 + "\n")
