#!/usr/bin/env python3
"""
Debug script to check actual API response format
"""
import sys
import requests
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

dataset_id = sys.argv[1] if len(sys.argv) > 1 else "8xkx-amqh"

print(f"\n🔍 Debugging API Response Format for Dataset: {dataset_id}\n")

# Test metadata
print("1. Testing metadata endpoint...")
try:
    metadata_url = f"https://data.cdc.gov/api/views/{dataset_id}.json"
    response = requests.get(metadata_url, timeout=30)
    metadata = response.json()
    print(f"   ✓ Metadata retrieved")
    print(f"   Name: {metadata.get('name', 'N/A')}")
    print(f"   Columns: {len(metadata.get('columns', []))}")
    
    # Show column names
    if metadata.get('columns'):
        print(f"\n   Column names:")
        for col in metadata['columns'][:10]:
            print(f"     - {col.get('name', 'N/A')} ({col.get('dataTypeName', 'N/A')})")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test data endpoint
print(f"\n2. Testing data endpoint (limit=5)...")
try:
    data_url = f"https://data.cdc.gov/api/views/{dataset_id}/rows.json"
    params = {"$limit": 5}
    response = requests.get(data_url, params=params, timeout=60)
    print(f"   Status: {response.status_code}")
    
    data = response.json()
    print(f"\n   Response type: {type(data)}")
    
    if isinstance(data, list):
        print(f"   List length: {len(data)}")
        if len(data) > 0:
            print(f"   First item type: {type(data[0])}")
            if isinstance(data[0], dict):
                print(f"   First item keys: {list(data[0].keys())}")
                print(f"\n   First item sample:")
                print(json.dumps(data[0], indent=2)[:500])
    elif isinstance(data, dict):
        print(f"   Dictionary keys: {list(data.keys())}")
        print(f"\n   Dictionary sample:")
        print(json.dumps({k: str(v)[:100] for k, v in list(data.items())[:5]}, indent=2))
    
    print(f"\n   Full response (first 1000 chars):")
    print(json.dumps(data, indent=2)[:1000])
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
