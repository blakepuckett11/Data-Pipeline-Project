"""
Predefined Validation Rule Sets
Common validation configurations for CDC health data
"""
from data_pipeline.validation.validators import (
    ValidationRule,
    validate_not_empty,
    validate_numeric,
    validate_non_negative,
    validate_date_format,
    validate_date_not_future,
    validate_state_code,
    validate_fips_code
)


def get_cdc_basic_rules() -> list[ValidationRule]:
    """
    Basic validation rules for common CDC health data fields
    
    Returns:
        List of ValidationRule objects for common fields
    """
    rules = [
        # State code validation
        ValidationRule(
            field_name="state",
            validator_func=lambda v: validate_state_code(v) if v else (True, None),
            error_message="Invalid US state code",
            is_required=False,
            warning_only=False
        ),
        
        # Date validation
        ValidationRule(
            field_name="date",
            validator_func=lambda v: validate_date_format(v) if v else (True, None),
            error_message="Invalid date format (expected YYYY-MM-DD)",
            is_required=False,
            warning_only=False
        ),
        
        ValidationRule(
            field_name="date",
            validator_func=lambda v: validate_date_not_future(v) if v else (True, None),
            error_message="Date cannot be in the future",
            is_required=False,
            warning_only=True  # Warning, not error
        ),
        
        # Value validation (for numeric measurements)
        ValidationRule(
            field_name="value",
            validator_func=lambda v: validate_numeric(v) if v is not None else (True, None),
            error_message="Value must be numeric",
            is_required=False,
            warning_only=False
        ),
        
        ValidationRule(
            field_name="value",
            validator_func=lambda v: validate_non_negative(v) if v is not None else (True, None),
            error_message="Value cannot be negative",
            is_required=False,
            warning_only=False
        ),
        
        # FIPS code validation
        ValidationRule(
            field_name="fips_code",
            validator_func=lambda v: validate_fips_code(v) if v else (True, None),
            error_message="Invalid FIPS code format",
            is_required=False,
            warning_only=False
        ),
    ]
    
    return rules


def get_cdc_covid_rules() -> list[ValidationRule]:
    """
    Validation rules specific to COVID-19 datasets
    
    Returns:
        List of ValidationRule objects for COVID-19 data
    """
    rules = get_cdc_basic_rules()
    
    # Add COVID-specific rules
    covid_rules = [
        ValidationRule(
            field_name="cases",
            validator_func=lambda v: validate_non_negative(v) if v is not None else (True, None),
            error_message="Cases cannot be negative",
            is_required=False,
            warning_only=False
        ),
        
        ValidationRule(
            field_name="deaths",
            validator_func=lambda v: validate_non_negative(v) if v is not None else (True, None),
            error_message="Deaths cannot be negative",
            is_required=False,
            warning_only=False
        ),
    ]
    
    rules.extend(covid_rules)
    return rules


def get_cdc_mortality_rules() -> list[ValidationRule]:
    """
    Validation rules for mortality datasets
    
    Returns:
        List of ValidationRule objects for mortality data
    """
    rules = get_cdc_basic_rules()
    
    # Add mortality-specific rules
    mortality_rules = [
        ValidationRule(
            field_name="deaths",
            validator_func=lambda v: validate_non_negative(v) if v is not None else (True, None),
            error_message="Deaths cannot be negative",
            is_required=False,
            warning_only=False
        ),
        
        ValidationRule(
            field_name="population",
            validator_func=lambda v: validate_non_negative(v) if v is not None else (True, None),
            error_message="Population cannot be negative",
            is_required=False,
            warning_only=False
        ),
    ]
    
    rules.extend(mortality_rules)
    return rules
