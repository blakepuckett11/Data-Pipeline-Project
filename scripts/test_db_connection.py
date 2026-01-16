#!/usr/bin/env python3
"""
Test database connection and schema verification
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from dotenv import load_dotenv
except ImportError as e:
    print(f"✗ Missing required package: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

def test_connection():
    """Test database connection"""
    # Load environment variables
    env_path = project_root / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print("⚠ config/.env not found, using environment variables")
    
    # Get database credentials
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'cdc_health_data'),
        'user': os.getenv('DB_USER', os.getenv('USER', 'postgres')),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    print("Testing database connection...")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  Database: {db_config['database']}")
    print(f"  User: {db_config['user']}")
    print()
    
    try:
        # Test connection
        conn = psycopg2.connect(**db_config)
        print("✓ Database connection successful!")
        
        # Test schema
        cursor = conn.cursor()
        
        # Check if cdc schema exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = 'cdc'
            );
        """)
        schema_exists = cursor.fetchone()[0]
        
        if not schema_exists:
            print("✗ Schema 'cdc' does not exist")
            conn.close()
            return False
        
        print("✓ Schema 'cdc' exists")
        
        # Check for required tables
        required_tables = ['indicator', 'geography', 'stratifier', 'observation', 'ingestion_log']
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'cdc'
            ORDER BY table_name;
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\nFound {len(existing_tables)} tables in 'cdc' schema:")
        for table in existing_tables:
            print(f"  ✓ {table}")
        
        missing_tables = set(required_tables) - set(existing_tables)
        if missing_tables:
            print(f"\n✗ Missing tables: {', '.join(missing_tables)}")
            conn.close()
            return False
        
        # Test a simple query
        cursor.execute("SELECT COUNT(*) FROM cdc.indicator;")
        indicator_count = cursor.fetchone()[0]
        print(f"\n✓ Test query successful (indicator table has {indicator_count} records)")
        
        # Check for helper functions
        cursor.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'cdc' 
            AND routine_type = 'FUNCTION';
        """)
        functions = [row[0] for row in cursor.fetchall()]
        
        if functions:
            print(f"\n✓ Found {len(functions)} helper function(s):")
            for func in functions:
                print(f"  - {func}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*50)
        print("✓ Database setup verification complete!")
        print("="*50)
        return True
        
    except psycopg2.OperationalError as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check database credentials in config/.env")
        print("  3. Verify database 'cdc_health_data' exists")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
