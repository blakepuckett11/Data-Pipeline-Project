"""
Main Validator Class
Orchestrates validation of records using defined rules
"""
from typing import List, Dict, Any, Optional
from data_pipeline.validation.schemas import (
    ValidationStatus,
    FieldValidationResult,
    RecordValidationResult,
    BatchValidationResult
)
from data_pipeline.validation.validators import ValidationRule
from utils.logger import logger


class DataValidator:
    """
    Validates data records against defined rules
    
    Usage:
        validator = DataValidator()
        validator.add_rule(ValidationRule(...))
        results = validator.validate_batch(records)
    """
    
    def __init__(self):
        """Initialize validator with empty rule set"""
        self.rules: List[ValidationRule] = []
        logger.info("DataValidator initialized")
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule"""
        self.rules.append(rule)
        logger.debug(f"Added validation rule for field: {rule.field_name}")
    
    def add_rules(self, rules: List[ValidationRule]):
        """Add multiple validation rules"""
        for rule in rules:
            self.add_rule(rule)
    
    def validate_record(
        self,
        record: Dict[str, Any],
        record_index: int = 0
    ) -> RecordValidationResult:
        """
        Validate a single record against all rules
        
        Args:
            record: Dictionary containing record data
            record_index: Index of record in batch (for error reporting)
            
        Returns:
            RecordValidationResult with validation status and details
        """
        errors = []
        warnings = []
        field_results = {}
        validated_data = record.copy()
        
        # Apply all validation rules
        for rule in self.rules:
            field_value = record.get(rule.field_name)
            is_valid, error_msg = rule.validate(field_value)
            
            # Store field result
            field_result = FieldValidationResult(
                field_name=rule.field_name,
                is_valid=is_valid,
                value=field_value,
                error_message=error_msg if not is_valid else None
            )
            field_results[rule.field_name] = field_result
            
            # Collect errors/warnings
            if not is_valid:
                if rule.warning_only:
                    warnings.append(f"{rule.field_name}: {error_msg}")
                else:
                    errors.append(f"{rule.field_name}: {error_msg}")
                    # Remove invalid field from validated data
                    validated_data.pop(rule.field_name, None)
        
        # Determine overall status
        if errors:
            status = ValidationStatus.INVALID
            is_valid = False
        elif warnings:
            status = ValidationStatus.WARNING
            is_valid = True
        else:
            status = ValidationStatus.VALID
            is_valid = True
        
        return RecordValidationResult(
            record_index=record_index,
            is_valid=is_valid,
            status=status,
            errors=errors,
            warnings=warnings,
            field_results=field_results,
            validated_data=validated_data if is_valid else None
        )
    
    def validate_batch(
        self,
        records: List[Dict[str, Any]],
        stop_on_first_error: bool = False
    ) -> BatchValidationResult:
        """
        Validate a batch of records
        
        Args:
            records: List of record dictionaries
            stop_on_first_error: If True, stop validation after first invalid record
            
        Returns:
            BatchValidationResult with summary statistics
        """
        logger.info(f"Validating batch of {len(records)} records")
        
        validation_results = []
        valid_count = 0
        invalid_count = 0
        warning_count = 0
        all_errors = []
        all_warnings = []
        
        for idx, record in enumerate(records):
            result = self.validate_record(record, record_index=idx)
            validation_results.append(result)
            
            if result.status == ValidationStatus.VALID:
                valid_count += 1
            elif result.status == ValidationStatus.INVALID:
                invalid_count += 1
                all_errors.extend(result.errors)
            elif result.status == ValidationStatus.WARNING:
                warning_count += 1
                all_warnings.extend(result.warnings)
            
            # Stop early if requested and found invalid record
            if stop_on_first_error and result.status == ValidationStatus.INVALID:
                logger.warning(f"Stopping validation after invalid record at index {idx}")
                break
        
        # Create summary
        summary_errors = list(set(all_errors))  # Unique errors
        summary_warnings = list(set(all_warnings))  # Unique warnings
        
        logger.info(
            f"Validation complete: {valid_count} valid, {invalid_count} invalid, "
            f"{warning_count} with warnings"
        )
        
        return BatchValidationResult(
            total_records=len(records),
            valid_records=valid_count,
            invalid_records=invalid_count,
            records_with_warnings=warning_count,
            validation_results=validation_results,
            summary_errors=summary_errors,
            summary_warnings=summary_warnings
        )
    
    def get_valid_records(
        self,
        batch_result: BatchValidationResult
    ) -> List[Dict[str, Any]]:
        """
        Extract only valid records from batch result
        
        Args:
            batch_result: BatchValidationResult from validate_batch()
            
        Returns:
            List of validated record dictionaries
        """
        valid_records = []
        for result in batch_result.validation_results:
            if result.is_valid and result.validated_data:
                valid_records.append(result.validated_data)
        return valid_records
    
    def get_invalid_records(
        self,
        batch_result: BatchValidationResult
    ) -> List[Dict[str, Any]]:
        """
        Extract invalid records with error details
        
        Args:
            batch_result: BatchValidationResult from validate_batch()
            
        Returns:
            List of invalid records with error information
        """
        invalid_records = []
        for result in batch_result.validation_results:
            if not result.is_valid:
                invalid_records.append({
                    "record_index": result.record_index,
                    "record": result.validated_data or {},
                    "errors": result.errors,
                    "field_results": {
                        field: {
                            "is_valid": fr.is_valid,
                            "error": fr.error_message
                        }
                        for field, fr in result.field_results.items()
                    }
                })
        return invalid_records
