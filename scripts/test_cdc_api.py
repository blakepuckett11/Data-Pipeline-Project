#!/usr/bin/env python3
"""
Quick test script to check if a CDC dataset ID is valid and accessible
"""
import sys
from pathlib import Path
import signal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.ingestion.cdc_api_client import CDCAPIClient
from utils.logger import logger


def timeout_handler(signum, frame):
    raise TimeoutError("API call timed out")


def test_dataset(dataset_id: str, timeout_seconds: int = 30):
    """Test if a dataset ID is valid and accessible"""
    print(f"\n🔍 Testing CDC Dataset: {dataset_id}\n")
    print(f"Timeout: {timeout_seconds} seconds\n")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        client = CDCAPIClient()
        
        print("1. Testing metadata fetch...")
        metadata = client.get_dataset_metadata(dataset_id)
        signal.alarm(0)  # Cancel timeout
        
        print(f"   ✓ Success!")
        print(f"   Dataset Name: {metadata.get('name', 'N/A')}")
        print(f"   Columns: {len(metadata.get('columns', []))}")
        print(f"   Rows: {metadata.get('rowsUpdatedAt', 'N/A')}")
        
        print("\n2. Testing data fetch (limit: 5)...")
        sample_data = client.get_dataset_data(dataset_id, limit=5)
        print(f"   ✓ Success! Retrieved {len(sample_data)} sample records")
        
        if sample_data:
            print(f"\n   Sample record fields:")
            for key in list(sample_data[0].keys())[:10]:
                print(f"     - {key}")
        
        print("\n✅ Dataset is accessible and valid!")
        return True
        
    except TimeoutError:
        signal.alarm(0)
        print(f"\n❌ API call timed out after {timeout_seconds} seconds")
        print("   The dataset may be:")
        print("   - Unavailable or slow")
        print("   - Invalid dataset ID")
        print("   - Network connectivity issues")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"\n❌ Error: {e}")
        print("\n   Possible issues:")
        print("   - Invalid dataset ID")
        print("   - Dataset no longer exists")
        print("   - API endpoint changed")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_cdc_api.py <dataset_id>")
        print("\nExample:")
        print("  python scripts/test_cdc_api.py 8xkx-amqh")
        sys.exit(1)
    
    dataset_id = sys.argv[1]
    success = test_dataset(dataset_id)
    sys.exit(0 if success else 1)
