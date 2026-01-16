#!/usr/bin/env python3
"""
Test script for data loading module
Tests database connection and loading functionality
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.loading.db_connection import DatabaseConnection
from data_pipeline.loading.reference_data import ReferenceDataManager
from data_pipeline.loading.loader import DataLoader
from utils.logger import logger


def test_db_connection():
    """Test database connection"""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    try:
        db = DatabaseConnection()
        print("✓ DatabaseConnection created")
        
        # Test connection
        if db.test_connection():
            print("✓ Database connection successful")
            return db
        else:
            print("✗ Database connection failed")
            return None
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return None


def test_reference_data(db):
    """Test reference data management"""
    print("\n" + "=" * 60)
    print("Testing Reference Data Management")
    print("=" * 60)
    
    try:
        ref_manager = ReferenceDataManager(db)
        print("✓ ReferenceDataManager created")
        
        # Test indicator creation
        indicator_id = ref_manager.get_or_create_indicator(
            code="TEST_INDICATOR",
            name="Test Indicator",
            unit="cases",
            description="Test indicator for validation"
        )
        print(f"✓ Indicator created/retrieved (ID: {indicator_id})")
        
        # Test geography creation
        geography_id = ref_manager.get_or_create_geography(
            state="CA",
            state_name="California",
            level="state"
        )
        print(f"✓ Geography created/retrieved (ID: {geography_id})")
        
        # Test stratifier creation
        stratifier_id = ref_manager.get_or_create_stratifier(
            dimension="age_group",
            value="18-24"
        )
        print(f"✓ Stratifier created/retrieved (ID: {stratifier_id})")
        
        return {
            "indicator_id": indicator_id,
            "geography_id": geography_id,
            "stratifier_id": stratifier_id
        }
    except Exception as e:
        print(f"✗ Reference data test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_data_loading(db, ref_ids):
    """Test data loading"""
    print("\n" + "=" * 60)
    print("Testing Data Loading")
    print("=" * 60)
    
    try:
        loader = DataLoader(db)
        print("✓ DataLoader created")
        
        # Create test observation records
        test_records = [
            {
                "state": "CA",
                "state_name": "California",
                "period_start": date(2023, 1, 15),
                "period_end": date(2023, 1, 15),
                "value": 100.5,
                "data_source": "Test Dataset",
                "data_source_id": "test-001",
                "indicator_code": "TEST_INDICATOR",
                "indicator_name": "Test Indicator",
                "geography_level": "state"
            },
            {
                "state": "NY",
                "state_name": "New York",
                "period_start": date(2023, 1, 16),
                "period_end": date(2023, 1, 16),
                "value": 250.0,
                "data_source": "Test Dataset",
                "data_source_id": "test-002",
                "indicator_code": "TEST_INDICATOR",
                "indicator_name": "Test Indicator",
                "geography_level": "state"
            }
        ]
        
        print(f"\nLoading {len(test_records)} test records...")
        
        result = loader.load_batch(
            records=test_records,
            data_source="Test Dataset",
            indicator_code="TEST_INDICATOR",
            indicator_name="Test Indicator"
        )
        
        print(f"\n✓ Loading Results:")
        print(f"  Run ID: {result['run_id']}")
        print(f"  Records Processed: {result['records_processed']}")
        print(f"  Records Inserted: {result['records_inserted']}")
        print(f"  Records Failed: {result['records_failed']}")
        print(f"  Status: {result['status']}")
        
        if result['errors']:
            print(f"\n  Errors:")
            for error in result['errors'][:5]:
                print(f"    - {error}")
        
        # Verify records were inserted
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM cdc.observation o
                JOIN cdc.indicator i ON o.indicator_id = i.id
                WHERE i.code = 'TEST_INDICATOR'
            """)
            count = cursor.fetchone()['count']
            print(f"\n✓ Verified {count} observations in database")
        
        return result['status'] == "completed" and result['records_inserted'] > 0
        
    except Exception as e:
        print(f"✗ Data loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ingestion_log(db):
    """Test ingestion log"""
    print("\n" + "=" * 60)
    print("Testing Ingestion Log")
    print("=" * 60)
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT run_id, data_source, status, records_inserted, records_failed
                FROM cdc.ingestion_log
                WHERE data_source = 'Test Dataset'
                ORDER BY started_at DESC
                LIMIT 1
            """)
            log_entry = cursor.fetchone()
            
            if log_entry:
                print(f"✓ Found ingestion log entry:")
                print(f"  Run ID: {log_entry['run_id']}")
                print(f"  Status: {log_entry['status']}")
                print(f"  Inserted: {log_entry['records_inserted']}")
                print(f"  Failed: {log_entry['records_failed']}")
                return True
            else:
                print("⚠ No ingestion log entry found")
                return False
    except Exception as e:
        print(f"✗ Ingestion log test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🧪 Testing Data Loading Module\n")
    
    # Test database connection
    db = test_db_connection()
    if not db:
        print("\n❌ Cannot proceed without database connection")
        return
    
    # Test reference data
    ref_ids = test_reference_data(db)
    if not ref_ids:
        print("\n⚠ Reference data tests had issues")
    
    # Test data loading
    loading_ok = test_data_loading(db, ref_ids)
    
    # Test ingestion log
    log_ok = test_ingestion_log(db)
    
    print("\n" + "=" * 60)
    if loading_ok and log_ok:
        print("✅ All loading tests passed!")
    else:
        print("⚠ Some tests had issues")
    print("=" * 60)
    
    # Cleanup
    try:
        db.close_pool()
    except:
        pass


if __name__ == "__main__":
    main()
