#!/usr/bin/env python3
"""
Example script showing how to run the pipeline programmatically
This demonstrates the pipeline API usage
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.pipeline import DataPipeline
from utils.logger import logger


def example_basic_pipeline():
    """Example: Run pipeline with basic parameters"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Pipeline Run")
    print("=" * 60)
    
    pipeline = DataPipeline()
    
    # Note: Replace with actual CDC dataset ID
    # Find datasets at: https://data.cdc.gov/browse
    results = pipeline.run(
        dataset_id="8xkx-amqh",  # Example dataset ID - replace with real one
        dataset_name="Example CDC Dataset",
        indicator_code="EXAMPLE_INDICATOR",
        indicator_name="Example Indicator",
        limit=10  # Process only 10 records for testing
    )
    
    pipeline.print_summary(results)
    return results


def example_pipeline_with_filters():
    """Example: Run pipeline with filters"""
    print("\n" + "=" * 60)
    print("Example 2: Pipeline with Filters")
    print("=" * 60)
    
    pipeline = DataPipeline()
    
    results = pipeline.run(
        dataset_id="8xkx-amqh",  # Example dataset ID
        dataset_name="Filtered Dataset",
        indicator_code="FILTERED_INDICATOR",
        indicator_name="Filtered Indicator",
        filters={
            "state": "CA",  # Filter by state
            "year": 2023    # Filter by year
        },
        limit=100
    )
    
    pipeline.print_summary(results)
    return results


def example_custom_components():
    """Example: Run pipeline with custom components"""
    print("\n" + "=" * 60)
    print("Example 3: Pipeline with Custom Components")
    print("=" * 60)
    
    from data_pipeline.validation.validator import DataValidator
    from data_pipeline.validation.presets import get_cdc_covid_rules
    
    # Create custom validator with COVID-specific rules
    validator = DataValidator()
    validator.add_rules(get_cdc_covid_rules())
    
    # Create pipeline with custom validator
    pipeline = DataPipeline(validator=validator)
    
    results = pipeline.run(
        dataset_id="8xkx-amqh",
        dataset_name="COVID-19 Dataset",
        indicator_code="COVID_CASES",
        indicator_name="COVID-19 Cases",
        limit=50
    )
    
    pipeline.print_summary(results)
    return results


def main():
    """Run examples"""
    print("\n📚 Pipeline Usage Examples\n")
    print("Note: These examples use placeholder dataset IDs.")
    print("Replace with actual CDC dataset IDs from https://data.cdc.gov/browse\n")
    
    try:
        # Example 1: Basic usage
        example_basic_pipeline()
        
        # Uncomment to run other examples:
        # example_pipeline_with_filters()
        # example_custom_components()
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
