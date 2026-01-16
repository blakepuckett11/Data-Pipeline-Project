"""
Main Transformer Class
Orchestrates data transformation pipeline
"""
from typing import List, Dict, Any, Optional
from data_pipeline.transformation.mappers import CDCRecordMapper
from data_pipeline.transformation.cleaners import (
    clean_string,
    clean_numeric,
    clean_date
)
from utils.logger import logger


class DataTransformer:
    """
    Transforms validated data for database loading
    
    Responsibilities:
    - Clean and normalize values
    - Map fields to database schema
    - Derive computed fields
    - Prepare data for loading
    """
    
    def __init__(self, mapper: Optional[CDCRecordMapper] = None):
        """
        Initialize data transformer
        
        Args:
            mapper: Field mapper instance (creates default if not provided)
        """
        self.mapper = mapper or CDCRecordMapper()
        logger.info("DataTransformer initialized")
    
    def transform_record(
        self,
        record: Dict[str, Any],
        indicator_code: Optional[str] = None,
        indicator_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform a single validated record
        
        Args:
            record: Validated record dictionary
            indicator_code: Indicator code (if known from dataset)
            indicator_name: Indicator name (if known from dataset)
            
        Returns:
            Transformed record ready for database loading
        """
        try:
            # Map to observation format
            transformed = self.mapper.map_to_observation_format(
                record=record,
                indicator_code=indicator_code,
                indicator_name=indicator_name
            )
            
            # Ensure required fields have defaults
            transformed = self._apply_defaults(transformed)
            
            return transformed
            
        except Exception as e:
            logger.error(f"Transformation failed for record: {e}")
            raise
    
    def transform_batch(
        self,
        records: List[Dict[str, Any]],
        indicator_code: Optional[str] = None,
        indicator_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform a batch of validated records
        
        Args:
            records: List of validated record dictionaries
            indicator_code: Indicator code (applied to all records)
            indicator_name: Indicator name (applied to all records)
            
        Returns:
            List of transformed records
        """
        logger.info(f"Transforming batch of {len(records)} records")
        
        transformed_records = []
        failed_count = 0
        
        for idx, record in enumerate(records):
            try:
                transformed = self.transform_record(
                    record=record,
                    indicator_code=indicator_code,
                    indicator_name=indicator_name
                )
                transformed_records.append(transformed)
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to transform record {idx}: {e}")
                # Continue with other records
        
        logger.info(
            f"Transformation complete: {len(transformed_records)} successful, "
            f"{failed_count} failed"
        )
        
        return transformed_records
    
    def _apply_defaults(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default values for required fields
        
        Args:
            record: Transformed record
            
        Returns:
            Record with defaults applied
        """
        # Ensure period_end is set if period_start exists but period_end doesn't
        if record.get("period_start") and not record.get("period_end"):
            record["period_end"] = record["period_start"]
        
        # Ensure geography_level is set
        if not record.get("geography_level"):
            record["geography_level"] = self.mapper._determine_geography_level(record)
        
        return record
    
    def enrich_with_metadata(
        self,
        records: List[Dict[str, Any]],
        dataset_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich records with dataset metadata
        
        Args:
            records: Transformed records
            dataset_metadata: Dataset metadata from CDC API
            
        Returns:
            Enriched records
        """
        if not dataset_metadata:
            return records
        
        # Extract indicator info from metadata if available
        indicator_name = dataset_metadata.get("name", "")
        indicator_description = dataset_metadata.get("description", "")
        
        # Enrich each record
        for record in records:
            if not record.get("indicator_name") and indicator_name:
                record["indicator_name"] = indicator_name
            
            if not record.get("indicator_description") and indicator_description:
                record["indicator_description"] = indicator_description
            
            # Store full metadata in metadata field
            if "metadata" not in record:
                record["metadata"] = {}
            
            record["metadata"]["dataset_metadata"] = dataset_metadata
        
        return records
