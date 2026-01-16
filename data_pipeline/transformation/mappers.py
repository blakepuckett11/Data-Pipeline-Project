"""
Field Mapping and Transformation
Maps CDC data fields to database schema fields
"""
from typing import Dict, Any, Optional, Callable
from datetime import date
from data_pipeline.transformation.cleaners import (
    clean_string,
    clean_numeric,
    clean_date,
    clean_state_code,
    clean_fips_code,
    normalize_county_name
)
from utils.logger import logger


class FieldMapper:
    """
    Maps and transforms fields from CDC data format to database schema format
    """
    
    def __init__(self):
        """Initialize field mapper"""
        self.field_mappings: Dict[str, str] = {}
        self.transformations: Dict[str, Callable] = {}
        logger.info("FieldMapper initialized")
    
    def add_mapping(self, source_field: str, target_field: str):
        """Add a simple field name mapping"""
        self.field_mappings[source_field] = target_field
        logger.debug(f"Added mapping: {source_field} -> {target_field}")
    
    def add_transformation(self, field_name: str, transform_func: Callable):
        """Add a transformation function for a field"""
        self.transformations[field_name] = transform_func
        logger.debug(f"Added transformation for field: {field_name}")
    
    def map_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a record from source format to target format
        
        Args:
            record: Source record dictionary
            
        Returns:
            Mapped record dictionary
        """
        mapped = {}
        
        # Apply field mappings
        for source_field, target_field in self.field_mappings.items():
            if source_field in record:
                mapped[target_field] = record[source_field]
        
        # Copy unmapped fields (if they exist in source)
        for key, value in record.items():
            if key not in self.field_mappings:
                mapped[key] = value
        
        # Apply transformations
        for field_name, transform_func in self.transformations.items():
            if field_name in mapped:
                try:
                    mapped[field_name] = transform_func(mapped[field_name])
                except Exception as e:
                    logger.warning(f"Transformation failed for {field_name}: {e}")
                    # Keep original value if transformation fails
                    pass
        
        return mapped


class CDCRecordMapper(FieldMapper):
    """
    Specialized mapper for CDC health data records
    Maps to our database schema structure
    """
    
    def __init__(self):
        """Initialize CDC-specific mapper with default mappings"""
        super().__init__()
        self._setup_default_mappings()
    
    def _setup_default_mappings(self):
        """Set up default field mappings for CDC data"""
        # Common CDC field mappings
        mappings = {
            # Geography fields
            "state": "state",
            "stateabbr": "state",  # BRFSS format
            "state_name": "state_name",
            "statedesc": "state_name",  # BRFSS format
            "county": "county",
            "county_name": "county",
            "locationname": "county",  # BRFSS format
            "fips": "fips_code",
            "fips_code": "fips_code",
            "locationid": "fips_code",  # BRFSS format
            "geography": "geography",
            
            # Date fields
            "date": "date",
            "report_date": "date",
            "week_ending": "date",
            "year": "year",  # BRFSS format
            "period_start": "period_start",
            "period_end": "period_end",
            
            # Value fields
            "value": "value",
            "data_value": "value",  # BRFSS format
            "cases": "value",
            "deaths": "value",
            "count": "value",
            "rate": "value",
            "percentage": "value",
            
            # BRFSS specific fields
            "measure": "measure",
            "category": "category",
            "data_value_unit": "unit",
            "low_confidence_limit": "value_lower_bound",
            "high_confidence_limit": "value_upper_bound",
            "totalpopulation": "sample_size",
            
            # Stratifier fields
            "age_group": "age_group",
            "age": "age_group",
            "gender": "gender",
            "sex": "gender",
            "race": "race",
            "ethnicity": "ethnicity",
        }
        
        for source, target in mappings.items():
            self.add_mapping(source, target)
        
        # Add transformations
        self.add_transformation("state", clean_state_code)
        self.add_transformation("fips_code", clean_fips_code)
        self.add_transformation("county", normalize_county_name)
        self.add_transformation("date", lambda v: clean_date(v) if v else None)
        self.add_transformation("period_start", lambda v: clean_date(v) if v else None)
        self.add_transformation("period_end", lambda v: clean_date(v) if v else None)
        self.add_transformation("value", clean_numeric)
    
    def map_to_observation_format(
        self,
        record: Dict[str, Any],
        indicator_code: Optional[str] = None,
        indicator_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Map CDC record to observation format for database loading
        
        Args:
            record: CDC record dictionary
            indicator_code: Indicator code (if known)
            indicator_name: Indicator name (if known)
            
        Returns:
            Dictionary in observation format
        """
        # First apply standard mapping
        mapped = self.map_record(record)
        
        # Extract extraction metadata if present
        extraction_metadata = mapped.pop("_extraction_metadata", {})
        
        # Handle year field for BRFSS data
        period_start = mapped.get("period_start") or mapped.get("date")
        period_end = mapped.get("period_end") or mapped.get("date")
        
        # If we have a year but no date, create a date from year
        if not period_start and mapped.get("year"):
            try:
                year = int(mapped["year"])
                from datetime import date
                period_start = date(year, 1, 1)
                period_end = date(year, 12, 31)
            except (ValueError, TypeError):
                pass
        
        # Build observation record
        observation = {
            # Geography fields
            "state": mapped.get("state"),
            "state_name": mapped.get("state_name"),
            "county": mapped.get("county"),
            "fips_code": mapped.get("fips_code"),
            "geography_level": self._determine_geography_level(mapped),
            
            # Time period fields
            "period_start": period_start,
            "period_end": period_end,
            
            # Value fields
            "value": mapped.get("value"),
            "value_lower_bound": mapped.get("value_lower_bound"),
            "value_upper_bound": mapped.get("value_upper_bound"),
            "sample_size": mapped.get("sample_size"),
            "value_notes": mapped.get("value_notes"),
            
            # Indicator fields
            "indicator_code": indicator_code or mapped.get("measureid") or mapped.get("indicator_code"),
            "indicator_name": indicator_name or mapped.get("measure") or mapped.get("indicator_name"),
            "indicator_unit": mapped.get("unit") or mapped.get("data_value_unit"),
            "indicator_description": mapped.get("description") or mapped.get("short_question_text"),
            "indicator_category": mapped.get("category"),
            
            # Stratifier fields
            "age_group": mapped.get("age_group"),
            "gender": mapped.get("gender"),
            "race": mapped.get("race"),
            "ethnicity": mapped.get("ethnicity"),
            
            # Metadata fields
            "data_source": extraction_metadata.get("dataset_name") or mapped.get("data_source"),
            "data_source_id": extraction_metadata.get("dataset_id") or mapped.get("data_source_id"),
            "record_id": extraction_metadata.get("record_index"),
            
            # Keep any additional fields in metadata
            "metadata": {
                k: v for k, v in mapped.items()
                if k not in [
                    "state", "state_name", "county", "fips_code",
                    "date", "period_start", "period_end",
                    "value", "value_lower_bound", "value_upper_bound",
                    "sample_size", "value_notes",
                    "indicator_code", "indicator_name", "unit", "description",
                    "age_group", "gender", "race", "ethnicity",
                    "data_source", "data_source_id"
                ]
            }
        }
        
        return observation
    
    def _determine_geography_level(self, record: Dict[str, Any]) -> str:
        """
        Determine geography level from record fields
        
        Returns:
            'nation', 'state', or 'county'
        """
        if record.get("county") or record.get("fips_code") and len(str(record.get("fips_code", ""))) == 5:
            return "county"
        elif record.get("state"):
            return "state"
        else:
            return "nation"
