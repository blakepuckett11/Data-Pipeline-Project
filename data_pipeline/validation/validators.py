"""
Validation Rules and Validators
Contains reusable validation functions for common data quality checks
"""
from typing import Any, Optional, List, Dict, Callable
from datetime import date, datetime
import re
from utils.logger import logger


class ValidationRule:
    """Represents a single validation rule"""
    
    def __init__(
        self,
        field_name: str,
        validator_func: Callable,
        error_message: str,
        is_required: bool = False,
        warning_only: bool = False
    ):
        """
        Initialize validation rule
        
        Args:
            field_name: Name of the field to validate
            validator_func: Function that takes value and returns (is_valid, error_msg)
            error_message: Default error message if validation fails
            is_required: Whether field is required
            warning_only: If True, failures are warnings not errors
        """
        self.field_name = field_name
        self.validator_func = validator_func
        self.error_message = error_message
        self.is_required = is_required
        self.warning_only = warning_only
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value
        
        Returns:
            (is_valid, error_message)
        """
        # Check if required field is missing
        if self.is_required and (value is None or value == ""):
            return False, f"{self.field_name} is required but missing"
        
        # If not required and missing, skip validation
        if not self.is_required and (value is None or value == ""):
            return True, None
        
        # Run validator function
        try:
            is_valid, error_msg = self.validator_func(value)
            if not is_valid:
                return False, error_msg or self.error_message
            return True, None
        except Exception as e:
            logger.warning(f"Validator function error for {self.field_name}: {e}")
            return False, f"Validation error: {str(e)}"


# Common validator functions
def validate_not_empty(value: Any) -> tuple[bool, Optional[str]]:
    """Check if value is not empty"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return False, "Value cannot be empty"
    return True, None


def validate_not_null(value: Any) -> tuple[bool, Optional[str]]:
    """Check if value is not None"""
    if value is None:
        return False, "Value cannot be null"
    return True, None


def validate_numeric(value: Any) -> tuple[bool, Optional[str]]:
    """Check if value is numeric"""
    try:
        float(value)
        return True, None
    except (ValueError, TypeError):
        return False, f"Value '{value}' is not numeric"


def validate_positive(value: Any) -> tuple[bool, Optional[str]]:
    """Check if numeric value is positive"""
    try:
        num = float(value)
        if num < 0:
            return False, f"Value {num} must be positive"
        return True, None
    except (ValueError, TypeError):
        return False, f"Value '{value}' is not numeric"


def validate_non_negative(value: Any) -> tuple[bool, Optional[str]]:
    """Check if numeric value is non-negative"""
    try:
        num = float(value)
        if num < 0:
            return False, f"Value {num} cannot be negative"
        return True, None
    except (ValueError, TypeError):
        return False, f"Value '{value}' is not numeric"


def validate_date_format(value: Any, format: str = "%Y-%m-%d") -> tuple[bool, Optional[str]]:
    """Check if value matches date format"""
    if isinstance(value, (date, datetime)):
        return True, None
    
    if not isinstance(value, str):
        return False, f"Date value must be string or date object"
    
    try:
        datetime.strptime(value, format)
        return True, None
    except ValueError:
        return False, f"Date '{value}' does not match format {format}"


def validate_date_not_future(value: Any) -> tuple[bool, Optional[str]]:
    """Check if date is not in the future"""
    if isinstance(value, str):
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return False, f"Invalid date format: {value}"
    elif isinstance(value, date):
        date_obj = value
    elif isinstance(value, datetime):
        date_obj = value.date()
    else:
        return False, f"Value must be a date, got {type(value)}"
    
    if date_obj > date.today():
        return False, f"Date {date_obj} cannot be in the future"
    return True, None


def validate_in_list(value: Any, allowed_values: List[Any]) -> tuple[bool, Optional[str]]:
    """Check if value is in allowed list"""
    if value not in allowed_values:
        return False, f"Value '{value}' not in allowed values: {allowed_values}"
    return True, None


def validate_regex(value: Any, pattern: str) -> tuple[bool, Optional[str]]:
    """Check if value matches regex pattern"""
    if not isinstance(value, str):
        return False, f"Value must be string for regex validation"
    
    if not re.match(pattern, value):
        return False, f"Value '{value}' does not match pattern {pattern}"
    return True, None


def validate_state_code(value: Any) -> tuple[bool, Optional[str]]:
    """Validate US state code (2 letters)"""
    us_states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    ]
    return validate_in_list(value.upper() if isinstance(value, str) else value, us_states)


def validate_fips_code(value: Any) -> tuple[bool, Optional[str]]:
    """Validate FIPS code format (5 digits for county, 2 for state)"""
    if not isinstance(value, str):
        return False, "FIPS code must be a string"
    
    # Remove leading zeros for validation
    try:
        fips_int = int(value)
        if len(value) not in [2, 5]:
            return False, f"FIPS code must be 2 (state) or 5 (county) digits, got {len(value)}"
        return True, None
    except ValueError:
        return False, f"FIPS code must be numeric, got '{value}'"
