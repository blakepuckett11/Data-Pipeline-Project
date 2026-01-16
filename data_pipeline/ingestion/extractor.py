"""
Data Extractor
Orchestrates data extraction from CDC API and prepares raw data
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from data_pipeline.ingestion.cdc_api_client import CDCAPIClient
from utils.logger import logger


class DataExtractor:
    """
    Extracts data from CDC API and prepares it for validation/transformation
    
    Responsibilities:
    - Fetch data from CDC API
    - Add metadata (ingestion timestamp, source info)
    - Structure data for downstream processing
    """
    
    def __init__(self, api_client: Optional[CDCAPIClient] = None):
        """
        Initialize data extractor
        
        Args:
            api_client: CDC API client instance (creates new one if not provided)
        """
        self.api_client = api_client or CDCAPIClient()
        logger.info("DataExtractor initialized")
    
    def extract_dataset(
        self,
        dataset_id: str,
        dataset_name: Optional[str] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract data from a CDC dataset
        
        Args:
            dataset_id: Socrata dataset ID
            dataset_name: Human-readable dataset name (for logging)
            limit: Maximum records to fetch (None = all)
            filters: Dictionary of filters to apply (e.g., {"state": "CA"})
            
        Returns:
            Dictionary containing:
            - metadata: Dataset metadata
            - records: List of extracted records with metadata
            - extraction_info: Information about the extraction run
        """
        dataset_name = dataset_name or dataset_id
        run_id = str(uuid.uuid4())
        extraction_start = datetime.utcnow()
        
        logger.info(f"Starting extraction: {dataset_name} (ID: {dataset_id}, Run: {run_id})")
        
        try:
            # Get dataset metadata
            metadata = self.api_client.get_dataset_metadata(dataset_id)
            
            # Build WHERE clause from filters
            where_clause = self._build_where_clause(filters) if filters else None
            
            # Fetch data
            if limit:
                records = self.api_client.get_dataset_data(
                    dataset_id=dataset_id,
                    limit=limit,
                    where=where_clause
                )
            else:
                records = self.api_client.get_all_dataset_data(
                    dataset_id=dataset_id,
                    where=where_clause
                )
            
            # Add extraction metadata to each record
            enriched_records = self._enrich_records(
                records=records,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                run_id=run_id
            )
            
            extraction_end = datetime.utcnow()
            extraction_duration = (extraction_end - extraction_start).total_seconds()
            
            extraction_info = {
                "run_id": run_id,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "records_extracted": len(enriched_records),
                "extraction_start": extraction_start.isoformat(),
                "extraction_end": extraction_end.isoformat(),
                "extraction_duration_seconds": extraction_duration,
                "status": "success"
            }
            
            logger.info(
                f"Extraction complete: {len(enriched_records)} records in {extraction_duration:.2f}s"
            )
            
            return {
                "metadata": metadata,
                "records": enriched_records,
                "extraction_info": extraction_info
            }
            
        except Exception as e:
            extraction_end = datetime.utcnow()
            extraction_duration = (extraction_end - extraction_start).total_seconds()
            
            logger.error(f"Extraction failed for {dataset_name}: {e}")
            
            extraction_info = {
                "run_id": run_id,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "records_extracted": 0,
                "extraction_start": extraction_start.isoformat(),
                "extraction_end": extraction_end.isoformat(),
                "extraction_duration_seconds": extraction_duration,
                "status": "failed",
                "error": str(e)
            }
            
            return {
                "metadata": {},
                "records": [],
                "extraction_info": extraction_info
            }
    
    def _enrich_records(
        self,
        records: List[Dict[str, Any]],
        dataset_id: str,
        dataset_name: str,
        run_id: str
    ) -> List[Dict[str, Any]]:
        """
        Add extraction metadata to each record
        
        Args:
            records: Raw records from API
            dataset_id: Dataset identifier
            dataset_name: Dataset name
            run_id: Extraction run ID
            
        Returns:
            Enriched records with metadata
        """
        enriched = []
        ingested_at = datetime.utcnow()
        
        for idx, record in enumerate(records):
            enriched_record = {
                **record,  # Original record data
                "_extraction_metadata": {
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name,
                    "run_id": run_id,
                    "record_index": idx,
                    "ingested_at": ingested_at.isoformat(),
                    "source": "cdc_open_data_api"
                }
            }
            enriched.append(enriched_record)
        
        return enriched
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Optional[str]:
        """
        Build SoQL WHERE clause from filter dictionary
        
        Args:
            filters: Dictionary of field: value pairs
            
        Returns:
            SoQL WHERE clause string or None
            
        Example:
            filters = {"state": "CA", "year": 2023}
            Returns: "state='CA' AND year=2023"
        """
        if not filters:
            return None
        
        conditions = []
        for field, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{field}='{value}'")
            elif isinstance(value, (int, float)):
                conditions.append(f"{field}={value}")
            elif isinstance(value, list):
                # Handle IN clause
                if all(isinstance(v, str) for v in value):
                    values = "', '".join(value)
                    conditions.append(f"{field} IN ('{values}')")
                else:
                    values = ", ".join(str(v) for v in value)
                    conditions.append(f"{field} IN ({values})")
        
        return " AND ".join(conditions) if conditions else None
