#!/usr/bin/env python3
"""
Test script for data validation module
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.validation.validator import DataValidator
from data_pipeline.validation.presets import get_cdc_basic_rules
from data_pipeline.validation.schemas import ValidationStatus
from utils.logger import logger


def test_basic_validation():
    """Test basic validation functionality"""
    print("=" * 60)
    print("Testing Basic Validation")
    print("=" * 60)
    
    # Create validator with basic rules
    validator = DataValidator()
    validator.add_rules(get_cdc_basic_rules())
    
    # Test records (mix of valid and invalid)
    test_records = [
        # Valid record
        {
            "state": "CA",
            "date": "2023-01-15",
            "value": 100.5,
            "fips_code": "06001"
        },
        # Invalid: future date
        {
            "state": "NY",
            "date": "2025-12-31",  # Future date
            "value": 50
        },
        # Invalid: negative value
        {
            "state": "TX",
            "date": "2023-06-01",
            "value": -10  # Negative value
        },
        # Invalid: bad state code
        {
            "state": "XX",  # Invalid state
            "date": "2023-01-01",
            "value": 75
        },
        # Valid: missing optional fields
        {
            "state": "FL",
            "value": 200
        }
    ]
    
    print(f"\nValidating {len(test_records)} test records...")
    results = validator.validate_batch(test_records)
    
    print(f"\n✓ Validation Results:")
    print(f"  Total records: {results.total_records}")
    print(f"  Valid: {results.valid_records}")
    print(f"  Invalid: {results.invalid_records}")
    print(f"  With warnings: {results.records_with_warnings}")
    
    if results.summary_errors:
        print(f"\n  Errors found:")
        for error in results.summary_errors[:5]:  # Show first 5
            print(f"    - {error}")
    
    if results.summary_warnings:
        print(f"\n  Warnings:")
        for warning in results.summary_warnings[:5]:  # Show first 5
            print(f"    - {warning}")
    
    # Get valid records
    valid_records = validator.get_valid_records(results)
    print(f"\n✓ Extracted {len(valid_records)} valid records")
    
    # Get invalid records
    invalid_records = validator.get_invalid_records(results)
    print(f"✓ Found {len(invalid_records)} invalid records")
    
    return results.valid_records >= 2 and results.invalid_records >= 2


def test_field_validation():
    """Test individual field validation"""
    print("\n" + "=" * 60)
    print("Testing Field-Level Validation")
    print("=" * 60)
    
    validator = DataValidator()
    validator.add_rules(get_cdc_basic_rules())
    
    # Test single record
    record = {
        "state": "CA",
        "date": "2023-01-01",
        "value": 100
    }
    
    result = validator.validate_record(record, record_index=0)
    
    print(f"\n✓ Record validation:")
    print(f"  Status: {result.status}")
    print(f"  Is valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    if result.field_results:
        print(f"\n  Field results:")
        for field_name, field_result in result.field_results.items():
            status = "✓" if field_result.is_valid else "✗"
            print(f"    {status} {field_name}: {field_result.value}")
            if field_result.error_message:
                print(f"      Error: {field_result.error_message}")
    
    return result.is_valid


def main():
    """Run all tests"""
    print("\n🧪 Testing Data Validation Module\n")
    
    test1_ok = test_basic_validation()
    test2_ok = test_field_validation()
    
    print("\n" + "=" * 60)
    if test1_ok and test2_ok:
        print("✅ All validation tests passed!")
    else:
        print("⚠ Some tests had issues")
    print("=" * 60)


if __name__ == "__main__":
    main()
