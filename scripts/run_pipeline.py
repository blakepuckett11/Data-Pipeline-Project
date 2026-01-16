#!/usr/bin/env python3
"""
Run the complete data pipeline
Example usage for processing CDC health data
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.pipeline import DataPipeline
from utils.logger import logger


def main():
    """Main entry point for pipeline execution"""
    parser = argparse.ArgumentParser(
        description="Run CDC Health Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a CDC dataset (replace with actual dataset ID)
  python scripts/run_pipeline.py \\
    --dataset-id "8xkx-amqh" \\
    --dataset-name "COVID-19 Cases" \\
    --indicator-code "COVID_CASES" \\
    --indicator-name "COVID-19 Cases"
  
  # Process with limit
  python scripts/run_pipeline.py \\
    --dataset-id "8xkx-amqh" \\
    --limit 1000
  
  # Process with filters
  python scripts/run_pipeline.py \\
    --dataset-id "8xkx-amqh" \\
    --filter state CA \\
    --filter year 2023
        """
    )
    
    parser.add_argument(
        "--dataset-id",
        required=True,
        help="CDC dataset ID (Socrata dataset ID from data.cdc.gov)"
    )
    
    parser.add_argument(
        "--dataset-name",
        help="Human-readable dataset name"
    )
    
    parser.add_argument(
        "--indicator-code",
        help="Indicator code for database (e.g., COVID_CASES)"
    )
    
    parser.add_argument(
        "--indicator-name",
        help="Indicator name for database"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of records to process"
    )
    
    parser.add_argument(
        "--filter",
        nargs=2,
        metavar=("FIELD", "VALUE"),
        action="append",
        help="Filter criteria (can be used multiple times, e.g., --filter state CA)"
    )
    
    parser.add_argument(
        "--use-resource-endpoint",
        action="store_true",
        help="Use /resource/ endpoint instead of /api/views/ (for datasets like swc5-untb)"
    )
    
    args = parser.parse_args()
    
    # Build filters dictionary
    filters = None
    if args.filter:
        filters = {field: value for field, value in args.filter}
    
    # Create pipeline
    pipeline = DataPipeline()
    
    # Run pipeline
    print("\n🚀 Starting CDC Health Data Pipeline\n")
    
    results = pipeline.run(
        dataset_id=args.dataset_id,
        dataset_name=args.dataset_name,
        indicator_code=args.indicator_code,
        indicator_name=args.indicator_name,
        limit=args.limit,
        filters=filters,
        use_resource_endpoint=args.use_resource_endpoint
    )
    
    # Print summary
    pipeline.print_summary(results)
    
    # Exit with appropriate code
    if results.get("status") == "completed":
        sys.exit(0)
    elif results.get("status") == "partial":
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Failed


if __name__ == "__main__":
    main()
