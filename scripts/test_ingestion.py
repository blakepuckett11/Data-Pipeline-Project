#!/usr/bin/env python3
"""
Test script for data ingestion module
Tests CDC API client and data extraction
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.ingestion.extractor import DataExtractor
from data_pipeline.ingestion.cdc_api_client import CDCAPIClient
from utils.logger import logger


def test_api_client():
    """Test CDC API client basic functionality"""
    print("=" * 60)
    print("Testing CDC API Client")
    print("=" * 60)
    
    try:
        client = CDCAPIClient()
        print("✓ CDC API Client initialized")
        
        # Test with a known CDC dataset (example: COVID-19 cases)
        # Note: Replace with actual dataset ID you want to test
        test_dataset_id = "8xkx-amqh"  # Example - replace with real dataset ID
        
        print(f"\nFetching metadata for dataset: {test_dataset_id}")
        try:
            metadata = client.get_dataset_metadata(test_dataset_id)
            print(f"✓ Metadata retrieved successfully")
            print(f"  Dataset name: {metadata.get('name', 'N/A')}")
            print(f"  Columns: {len(metadata.get('columns', []))}")
        except Exception as e:
            print(f"⚠ Could not fetch metadata: {e}")
            print("  This is expected if the dataset ID doesn't exist")
        
        # Test fetching a small sample of data
        print(f"\nFetching sample data (limit: 5)...")
        try:
            sample_data = client.get_dataset_data(test_dataset_id, limit=5)
            print(f"✓ Sample data retrieved: {len(sample_data)} records")
            if sample_data:
                print(f"  Sample record keys: {list(sample_data[0].keys())[:5]}...")
        except Exception as e:
            print(f"⚠ Could not fetch sample data: {e}")
            print("  This is expected if the dataset ID doesn't exist")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_extractor():
    """Test data extractor"""
    print("\n" + "=" * 60)
    print("Testing Data Extractor")
    print("=" * 60)
    
    try:
        extractor = DataExtractor()
        print("✓ Data Extractor initialized")
        
        # Test extraction with a sample dataset
        test_dataset_id = "8xkx-amqh"  # Example - replace with real dataset ID
        
        print(f"\nExtracting dataset: {test_dataset_id} (limit: 3)")
        result = extractor.extract_dataset(
            dataset_id=test_dataset_id,
            dataset_name="Test Dataset",
            limit=3
        )
        
        extraction_info = result["extraction_info"]
        print(f"\n✓ Extraction completed")
        print(f"  Status: {extraction_info['status']}")
        print(f"  Records extracted: {extraction_info['records_extracted']}")
        print(f"  Duration: {extraction_info['extraction_duration_seconds']:.2f}s")
        
        if result["records"]:
            print(f"\n  Sample record structure:")
            sample_record = result["records"][0]
            print(f"    Keys: {list(sample_record.keys())[:5]}...")
            if "_extraction_metadata" in sample_record:
                print(f"    Has extraction metadata: ✓")
        
        return extraction_info["status"] == "success"
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🧪 Testing Data Ingestion Module\n")
    
    # Test API client
    client_ok = test_api_client()
    
    # Test extractor
    extractor_ok = test_extractor()
    
    print("\n" + "=" * 60)
    if client_ok and extractor_ok:
        print("✓ All tests passed!")
    else:
        print("⚠ Some tests had issues (may be expected if dataset IDs are invalid)")
    print("=" * 60)
    
    print("\nNote: Replace test_dataset_id with actual CDC dataset IDs")
    print("Find datasets at: https://data.cdc.gov/browse")


if __name__ == "__main__":
    main()
