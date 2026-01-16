"""
Data Loader
Loads transformed data into PostgreSQL database
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from data_pipeline.loading.db_connection import DatabaseConnection
from data_pipeline.loading.reference_data import ReferenceDataManager
from utils.logger import logger


class DataLoader:
    """
    Loads transformed data into PostgreSQL database
    
    Responsibilities:
    - Load reference data (indicators, geography, stratifiers)
    - Load observation records
    - Handle duplicates (upsert logic)
    - Track ingestion runs
    - Provide loading statistics
    """
    
    def __init__(self, db: Optional[DatabaseConnection] = None):
        """
        Initialize data loader
        
        Args:
            db: DatabaseConnection instance (creates new if not provided)
        """
        self.db = db or DatabaseConnection()
        self.reference_manager = ReferenceDataManager(self.db)
        logger.info("DataLoader initialized")
    
    def start_ingestion_run(
        self,
        data_source: str,
        run_id: Optional[str] = None
    ) -> str:
        """
        Start a new ingestion run and log it
        
        Args:
            data_source: Source dataset name/identifier
            run_id: Optional run ID (generates UUID if not provided)
            
        Returns:
            Run ID
        """
        if not run_id:
            run_id = str(uuid.uuid4())
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO cdc.ingestion_log (
                    run_id, data_source, status, started_at, records_processed, records_inserted, records_failed
                )
                VALUES (%s, %s, 'running', CURRENT_TIMESTAMP, 0, 0, 0)
                ON CONFLICT (run_id) DO UPDATE SET
                    status = 'running',
                    started_at = CURRENT_TIMESTAMP,
                    records_processed = 0,
                    records_inserted = 0,
                    records_failed = 0
            """, (run_id, data_source))
        
        logger.info(f"Started ingestion run: {run_id} for {data_source}")
        return run_id
    
    def complete_ingestion_run(
        self,
        run_id: str,
        records_processed: int,
        records_inserted: int,
        records_failed: int,
        status: str = "completed",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Complete an ingestion run and update log
        
        Args:
            run_id: Run ID
            records_processed: Number of records processed
            records_inserted: Number of records successfully inserted
            records_failed: Number of records that failed
            status: Final status ('completed', 'failed', 'partial')
            error_message: Error message if failed
            metadata: Additional metadata
        """
        import json
        metadata_json = json.dumps(metadata) if metadata else None
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE cdc.ingestion_log
                SET status = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    records_processed = %s,
                    records_inserted = %s,
                    records_failed = %s,
                    error_message = %s,
                    metadata = %s
                WHERE run_id = %s
            """, (status, records_processed, records_inserted, records_failed,
                  error_message, metadata_json, run_id))
        
        logger.info(
            f"Completed ingestion run: {run_id} - "
            f"{records_inserted} inserted, {records_failed} failed"
        )
    
    def load_observation(
        self,
        observation: Dict[str, Any],
        indicator_id: int,
        geography_id: int,
        stratifier_id: Optional[int] = None
    ) -> bool:
        """
        Load a single observation record
        
        Args:
            observation: Observation data dictionary
            indicator_id: Indicator ID
            geography_id: Geography ID
            stratifier_id: Optional stratifier ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db.get_cursor() as cursor:
                # Prepare metadata JSON
                metadata = observation.get("metadata", {})
                metadata_json = json.dumps(metadata) if metadata else None
                
                # Insert observation (using ON CONFLICT for upsert)
                # Note: Using the unique index name for conflict resolution
                cursor.execute("""
                    INSERT INTO cdc.observation (
                        indicator_id, geography_id, stratifier_id,
                        period_start, period_end,
                        value, value_lower_bound, value_upper_bound,
                        sample_size, value_notes,
                        data_source, data_source_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (indicator_id, geography_id, COALESCE(stratifier_id, -1), period_start, period_end)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        value_lower_bound = EXCLUDED.value_lower_bound,
                        value_upper_bound = EXCLUDED.value_upper_bound,
                        sample_size = EXCLUDED.sample_size,
                        value_notes = EXCLUDED.value_notes,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    indicator_id,
                    geography_id,
                    stratifier_id,
                    observation.get("period_start"),
                    observation.get("period_end"),
                    observation.get("value"),
                    observation.get("value_lower_bound"),
                    observation.get("value_upper_bound"),
                    observation.get("sample_size"),
                    observation.get("value_notes"),
                    observation.get("data_source"),
                    observation.get("data_source_id")
                ))
                
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Loaded observation (ID: {result['id']})")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to load observation: {e}")
            return False
    
    def load_batch(
        self,
        records: List[Dict[str, Any]],
        data_source: str,
        indicator_code: Optional[str] = None,
        indicator_name: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load a batch of transformed records
        
        Args:
            records: List of transformed observation records
            data_source: Source dataset identifier
            indicator_code: Indicator code (if known)
            indicator_name: Indicator name (if known)
            run_id: Optional run ID
            
        Returns:
            Dictionary with loading statistics
        """
        if not records:
            logger.warning("No records to load")
            return {
                "run_id": run_id,
                "records_processed": 0,
                "records_inserted": 0,
                "records_failed": 0,
                "status": "completed"
            }
        
        # Start ingestion run
        run_id = self.start_ingestion_run(data_source, run_id)
        
        records_processed = 0
        records_inserted = 0
        records_failed = 0
        errors = []
        
        # Get or create indicator
        indicator_id = None
        if indicator_code:
            indicator_id = self.reference_manager.get_or_create_indicator(
                code=indicator_code,
                name=indicator_name or indicator_code,
                unit=records[0].get("indicator_unit") if records else None,
                description=records[0].get("indicator_description") if records else None
            )
        
        logger.info(f"Loading batch of {len(records)} records (run_id: {run_id})")
        
        # Process each record
        for idx, record in enumerate(records):
            try:
                records_processed += 1
                
                # Get or create geography
                geography_id = self.reference_manager.get_or_create_geography(
                    state=record.get("state"),
                    state_name=record.get("state_name"),
                    county=record.get("county"),
                    fips_code=record.get("fips_code"),
                    level=record.get("geography_level", "state")
                )
                
                # Get or create stratifier if present
                stratifier_id = None
                if record.get("age_group"):
                    stratifier_id = self.reference_manager.get_or_create_stratifier(
                        dimension="age_group",
                        value=record["age_group"]
                    )
                elif record.get("gender"):
                    stratifier_id = self.reference_manager.get_or_create_stratifier(
                        dimension="gender",
                        value=record["gender"]
                    )
                elif record.get("race"):
                    stratifier_id = self.reference_manager.get_or_create_stratifier(
                        dimension="race",
                        value=record["race"]
                    )
                
                # Load observation
                if self.load_observation(record, indicator_id, geography_id, stratifier_id):
                    records_inserted += 1
                else:
                    records_failed += 1
                    errors.append(f"Record {idx}: Failed to insert")
                    
            except Exception as e:
                records_failed += 1
                error_msg = f"Record {idx}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        # Determine final status
        if records_failed == 0:
            status = "completed"
        elif records_inserted > 0:
            status = "partial"
        else:
            status = "failed"
        
        # Complete ingestion run
        self.complete_ingestion_run(
            run_id=run_id,
            records_processed=records_processed,
            records_inserted=records_inserted,
            records_failed=records_failed,
            status=status,
            error_message="; ".join(errors[:10]) if errors else None,  # Limit error message length
            metadata={"total_errors": len(errors)}
        )
        
        logger.info(
            f"Batch loading complete: {records_inserted} inserted, "
            f"{records_failed} failed out of {records_processed} processed"
        )
        
        return {
            "run_id": run_id,
            "records_processed": records_processed,
            "records_inserted": records_inserted,
            "records_failed": records_failed,
            "status": status,
            "errors": errors[:10]  # Return first 10 errors
        }
