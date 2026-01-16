"""
Reference Data Management
Handles loading and retrieval of reference data (indicators, geography, stratifiers)
"""
from typing import Dict, Any, Optional
from data_pipeline.loading.db_connection import DatabaseConnection
from utils.logger import logger


class ReferenceDataManager:
    """
    Manages reference data (indicators, geography, stratifiers)
    Uses database helper functions for efficient lookups/inserts
    """
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize reference data manager
        
        Args:
            db: DatabaseConnection instance
        """
        self.db = db
        logger.info("ReferenceDataManager initialized")
    
    def get_or_create_indicator(
        self,
        code: str,
        name: str,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Get or create an indicator record
        
        Args:
            code: Indicator code (unique identifier)
            name: Indicator name
            unit: Unit of measurement
            description: Description
            category: Category
            metadata: Additional metadata (JSONB)
            
        Returns:
            Indicator ID
        """
        with self.db.get_cursor() as cursor:
            # Try to get existing indicator
            cursor.execute(
                "SELECT id FROM cdc.indicator WHERE code = %s",
                (code,)
            )
            result = cursor.fetchone()
            
            if result:
                indicator_id = result['id']
                logger.debug(f"Found existing indicator: {code} (ID: {indicator_id})")
                return indicator_id
            
            # Create new indicator
            import json
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO cdc.indicator (code, name, unit, description, category, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (code, name, unit, description, category, metadata_json))
            
            indicator_id = cursor.fetchone()['id']
            logger.info(f"Created new indicator: {code} (ID: {indicator_id})")
            return indicator_id
    
    def get_or_create_geography(
        self,
        state: Optional[str] = None,
        state_name: Optional[str] = None,
        county: Optional[str] = None,
        fips_code: Optional[str] = None,
        level: str = "state",
        region: Optional[str] = None
    ) -> int:
        """
        Get or create a geography record
        
        Args:
            state: State code (2 letters)
            state_name: Full state name
            county: County name
            fips_code: FIPS code
            level: Geography level ('nation', 'state', 'county')
            region: US Census region
            
        Returns:
            Geography ID
        """
        with self.db.get_cursor() as cursor:
            # Build query to find existing geography
            conditions = []
            params = []
            
            if level == "nation":
                conditions.append("level = 'nation' AND state IS NULL")
            elif level == "state":
                if state:
                    conditions.append("level = 'state' AND state = %s")
                    params.append(state)
                if fips_code and len(fips_code) == 2:
                    conditions.append("fips_code = %s")
                    params.append(fips_code)
            elif level == "county":
                if state:
                    conditions.append("state = %s")
                    params.append(state)
                if county:
                    conditions.append("county = %s")
                    params.append(county)
                if fips_code:
                    conditions.append("fips_code = %s")
                    params.append(fips_code)
            
            if conditions:
                query = f"SELECT id FROM cdc.geography WHERE {' AND '.join(conditions)} LIMIT 1"
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result:
                    geography_id = result['id']
                    logger.debug(f"Found existing geography: {level} (ID: {geography_id})")
                    return geography_id
            
            # Create new geography
            cursor.execute("""
                INSERT INTO cdc.geography (country, state, state_name, county, fips_code, level, region)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ("USA", state, state_name, county, fips_code, level, region))
            
            geography_id = cursor.fetchone()['id']
            logger.info(f"Created new geography: {level} (ID: {geography_id})")
            return geography_id
    
    def get_or_create_stratifier(
        self,
        dimension: str,
        value: str,
        display_order: Optional[int] = None,
        parent_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Get or create a stratifier record
        
        Args:
            dimension: Dimension type ('age_group', 'gender', 'race', etc.)
            value: Dimension value
            display_order: Display order
            parent_id: Parent stratifier ID (for hierarchies)
            metadata: Additional metadata
            
        Returns:
            Stratifier ID or None if dimension/value is invalid
        """
        if not dimension or not value:
            return None
        
        with self.db.get_cursor() as cursor:
            # Try to get existing stratifier
            cursor.execute("""
                SELECT id FROM cdc.stratifier
                WHERE dimension = %s AND value = %s
            """, (dimension, value))
            
            result = cursor.fetchone()
            if result:
                stratifier_id = result['id']
                logger.debug(f"Found existing stratifier: {dimension}={value} (ID: {stratifier_id})")
                return stratifier_id
            
            # Create new stratifier
            import json
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO cdc.stratifier (dimension, value, display_order, parent_id, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (dimension, value, display_order, parent_id, metadata_json))
            
            stratifier_id = cursor.fetchone()['id']
            logger.info(f"Created new stratifier: {dimension}={value} (ID: {stratifier_id})")
            return stratifier_id
