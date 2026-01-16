#!/usr/bin/env python3
"""
Check what data exists in PostgreSQL database
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.loading.db_connection import DatabaseConnection
from utils.logger import logger


def check_table_counts(db):
    """Check record counts in all tables"""
    print("=" * 60)
    print("Database Record Counts")
    print("=" * 60)
    
    tables = [
        ("indicator", "cdc.indicator"),
        ("geography", "cdc.geography"),
        ("stratifier", "cdc.stratifier"),
        ("observation", "cdc.observation"),
        ("ingestion_log", "cdc.ingestion_log"),
    ]
    
    with db.get_cursor() as cursor:
        for table_name, full_name in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {full_name}")
            result = cursor.fetchone()
            count = result['count']
            status = "✓" if count > 0 else "○"
            print(f"{status} {table_name:20s}: {count:6d} records")
    
    print()


def check_recent_observations(db, limit=5):
    """Check recent observations"""
    print("=" * 60)
    print(f"Recent Observations (last {limit})")
    print("=" * 60)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                o.id,
                i.code as indicator_code,
                i.name as indicator_name,
                g.state,
                g.county,
                o.period_start,
                o.value,
                o.data_source
            FROM cdc.observation o
            JOIN cdc.indicator i ON o.indicator_id = i.id
            JOIN cdc.geography g ON o.geography_id = g.id
            ORDER BY o.ingested_at DESC
            LIMIT %s
        """, (limit,))
        
        observations = cursor.fetchall()
        
        if observations:
            print(f"\nFound {len(observations)} observations:\n")
            for obs in observations:
                print(f"  ID: {obs['id']}")
                print(f"    Indicator: {obs['indicator_code']} ({obs['indicator_name']})")
                print(f"    Location: {obs['state']}" + (f", {obs['county']}" if obs['county'] else ""))
                print(f"    Date: {obs['period_start']}")
                print(f"    Value: {obs['value']}")
                print(f"    Source: {obs['data_source']}")
                print()
        else:
            print("\n  No observations found in database")
    
    print()


def check_indicators(db):
    """Check indicators"""
    print("=" * 60)
    print("Indicators")
    print("=" * 60)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT code, name, unit, category
            FROM cdc.indicator
            ORDER BY code
        """)
        
        indicators = cursor.fetchall()
        
        if indicators:
            print(f"\nFound {len(indicators)} indicators:\n")
            for ind in indicators:
                print(f"  {ind['code']}")
                print(f"    Name: {ind['name']}")
                if ind['unit']:
                    print(f"    Unit: {ind['unit']}")
                if ind['category']:
                    print(f"    Category: {ind['category']}")
                print()
        else:
            print("\n  No indicators found")
    
    print()


def check_geography(db):
    """Check geography records"""
    print("=" * 60)
    print("Geography Records")
    print("=" * 60)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT level, COUNT(*) as count
            FROM cdc.geography
            GROUP BY level
            ORDER BY level
        """)
        
        geography = cursor.fetchall()
        
        if geography:
            print("\nGeography by level:\n")
            for geo in geography:
                print(f"  {geo['level']:10s}: {geo['count']:4d} records")
        else:
            print("\n  No geography records found")
    
    print()


def check_ingestion_logs(db, limit=5):
    """Check recent ingestion runs"""
    print("=" * 60)
    print(f"Recent Ingestion Runs (last {limit})")
    print("=" * 60)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                run_id,
                data_source,
                status,
                records_processed,
                records_inserted,
                records_failed,
                started_at,
                completed_at
            FROM cdc.ingestion_log
            ORDER BY started_at DESC
            LIMIT %s
        """, (limit,))
        
        logs = cursor.fetchall()
        
        if logs:
            print(f"\nFound {len(logs)} ingestion runs:\n")
            for log in logs:
                print(f"  Run ID: {log['run_id']}")
                print(f"    Source: {log['data_source']}")
                print(f"    Status: {log['status']}")
                print(f"    Processed: {log['records_processed']}")
                print(f"    Inserted: {log['records_inserted']}")
                print(f"    Failed: {log['records_failed']}")
                print(f"    Started: {log['started_at']}")
                if log['completed_at']:
                    print(f"    Completed: {log['completed_at']}")
                print()
        else:
            print("\n  No ingestion logs found")
    
    print()


def main():
    """Run all checks"""
    print("\n🔍 Checking PostgreSQL Database Contents\n")
    
    try:
        db = DatabaseConnection()
        
        if not db.test_connection():
            print("❌ Cannot connect to database")
            return
        
        # Check table counts
        check_table_counts(db)
        
        # Check indicators
        check_indicators(db)
        
        # Check geography
        check_geography(db)
        
        # Check observations
        check_recent_observations(db)
        
        # Check ingestion logs
        check_ingestion_logs(db)
        
        print("=" * 60)
        print("✅ Database check complete!")
        print("=" * 60)
        
        # Cleanup
        db.close_pool()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
