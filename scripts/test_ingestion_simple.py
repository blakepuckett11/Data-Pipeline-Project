#!/usr/bin/env python3
"""
Simple test script for data ingestion module
Tests module structure and imports without making API calls
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    try:
        from utils.config import db_config, cdc_api_config, app_config
        print("✓ Configuration module imported")
        print(f"  Database: {db_config.name}")
        print(f"  CDC API URL: {cdc_api_config.base_url}")
        print(f"  Environment: {app_config.environment}")
    except Exception as e:
        print(f"✗ Configuration import failed: {e}")
        return False
    
    try:
        from utils.logger import logger
        print("✓ Logger module imported")
        logger.info("Test log message")
        print("  Logger is working")
    except Exception as e:
        print(f"✗ Logger import failed: {e}")
        return False
    
    try:
        from data_pipeline.ingestion.cdc_api_client import CDCAPIClient, RateLimiter
        print("✓ CDC API Client module imported")
    except Exception as e:
        print(f"✗ CDC API Client import failed: {e}")
        return False
    
    try:
        from data_pipeline.ingestion.extractor import DataExtractor
        print("✓ Data Extractor module imported")
    except Exception as e:
        print(f"✗ Data Extractor import failed: {e}")
        return False
    
    return True


def test_rate_limiter():
    """Test rate limiter functionality"""
    print("\n" + "=" * 60)
    print("Testing Rate Limiter")
    print("=" * 60)
    
    try:
        from data_pipeline.ingestion.cdc_api_client import RateLimiter
        import time
        
        limiter = RateLimiter(max_requests=5, period_seconds=1)
        print("✓ Rate limiter created")
        
        # Test that it doesn't block for first requests
        start = time.time()
        for i in range(3):
            limiter.wait_if_needed()
        elapsed = time.time() - start
        print(f"✓ Rate limiter allows requests (3 requests in {elapsed:.3f}s)")
        
        if elapsed < 0.1:
            print("  Rate limiter working correctly")
        else:
            print("  Rate limiter may be too slow")
        
        return True
    except Exception as e:
        print(f"✗ Rate limiter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_client_initialization():
    """Test client initialization without API calls"""
    print("\n" + "=" * 60)
    print("Testing Client Initialization")
    print("=" * 60)
    
    try:
        from data_pipeline.ingestion.cdc_api_client import CDCAPIClient
        
        client = CDCAPIClient()
        print("✓ CDC API Client initialized")
        print(f"  Base URL: {client.base_url}")
        print(f"  Timeout: {client.timeout}s")
        print(f"  Rate limit: {client.rate_limiter.max_requests} requests/{client.rate_limiter.period_seconds}s")
        
        return True
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extractor_initialization():
    """Test extractor initialization"""
    print("\n" + "=" * 60)
    print("Testing Extractor Initialization")
    print("=" * 60)
    
    try:
        from data_pipeline.ingestion.extractor import DataExtractor
        
        extractor = DataExtractor()
        print("✓ Data Extractor initialized")
        print(f"  API Client: {type(extractor.api_client).__name__}")
        
        # Test helper method
        where_clause = extractor._build_where_clause({"state": "CA", "year": 2023})
        print(f"✓ WHERE clause builder works: {where_clause}")
        
        return True
    except Exception as e:
        print(f"✗ Extractor initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    try:
        from utils.config import db_config, cdc_api_config
        
        print("✓ Configuration loaded")
        print(f"  DB Host: {db_config.host}")
        print(f"  DB Port: {db_config.port}")
        print(f"  DB Name: {db_config.name}")
        print(f"  CDC API Base URL: {cdc_api_config.base_url}")
        print(f"  CDC API Timeout: {cdc_api_config.timeout}s")
        
        # Test connection string generation
        conn_str = db_config.connection_string
        # Mask password in output
        safe_conn_str = conn_str.split('@')[0].split(':')[0] + ':***@' + '@'.join(conn_str.split('@')[1:])
        print(f"  Connection string: {safe_conn_str}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🧪 Testing Data Ingestion Module (Structure Only)\n")
    print("Note: This test does not make actual API calls\n")
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Rate Limiter", test_rate_limiter()))
    results.append(("Client Init", test_client_initialization()))
    results.append(("Extractor Init", test_extractor_initialization()))
    results.append(("Configuration", test_configuration()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ All structure tests passed!")
        print("\nThe ingestion module is properly set up.")
        print("To test with actual API calls, use scripts/test_ingestion.py")
        print("(Note: Requires valid CDC dataset IDs)")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
