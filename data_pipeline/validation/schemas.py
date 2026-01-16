"""
Validation Schemas
Defines expected data structures and validation rules using Pydantic
"""
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator, field_validator
from enum import Enum


class ValidationStatus(str, Enum):
    """Validation status values"""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


class FieldValidationResult(BaseModel):
    """Result of validating a single field"""
    field_name: str
    is_valid: bool
    value: Any
    error_message: Optional[str] = None
    warning_message: Optional[str] = None


class RecordValidationResult(BaseModel):
    """Result of validating a single record"""
    record_index: int
    is_valid: bool
    status: ValidationStatus
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    field_results: Dict[str, FieldValidationResult] = Field(default_factory=dict)
    validated_data: Optional[Dict[str, Any]] = None


class BatchValidationResult(BaseModel):
    """Result of validating a batch of records"""
    total_records: int
    valid_records: int
    invalid_records: int
    records_with_warnings: int
    validation_results: List[RecordValidationResult] = Field(default_factory=list)
    summary_errors: List[str] = Field(default_factory=list)
    summary_warnings: List[str] = Field(default_factory=list)


class CDCDataSchema(BaseModel):
    """
    Base schema for CDC health data records
    This is a flexible schema that can be extended for specific datasets
    """
    # Common CDC fields (optional to allow flexibility)
    state: Optional[str] = None
    county: Optional[str] = None
    date: Optional[date] = None
    value: Optional[float] = None
    
    # Allow additional fields
    class Config:
        extra = "allow"  # Allow extra fields that aren't defined
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        """Ensure value is non-negative if provided"""
        if v is not None and v < 0:
            raise ValueError("Value cannot be negative")
        return v
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Ensure date is not in the future"""
        if v is not None and v > date.today():
            raise ValueError("Date cannot be in the future")
        return v
