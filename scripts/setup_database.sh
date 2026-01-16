#!/bin/bash
# Database Setup Script
# This script helps set up the PostgreSQL database for the CDC Health Data Pipeline
# Usage: ./scripts/setup_database.sh [db_user] [db_name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values (can be overridden by environment variables or arguments)
DB_USER=${1:-${DB_USER:-postgres}}
DB_NAME=${2:-${DB_NAME:-cdc_health_data}}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

echo "=========================================="
echo "CDC Health Data Pipeline - Database Setup"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Database User: $DB_USER"
echo "  Database Name: $DB_NAME"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
    echo -e "${RED}✗ PostgreSQL is not running or not accessible${NC}"
    echo "Please start PostgreSQL and try again."
    echo "On macOS with Homebrew: brew services start postgresql@14"
    exit 1
fi

echo -e "${GREEN}✓ PostgreSQL is running${NC}"
echo ""

# Check if database exists (connect to postgres database for this check)
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}⚠ Database '$DB_NAME' already exists${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dropping existing database..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
        echo "Creating new database..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME WITH ENCODING='UTF8' TEMPLATE=template0;"
        echo -e "${GREEN}✓ Database created${NC}"
    else
        echo "Using existing database..."
    fi
else
    echo "Creating database '$DB_NAME'..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME WITH ENCODING='UTF8' TEMPLATE=template0;" 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database created${NC}"
    else
        echo -e "${RED}✗ Failed to create database${NC}"
        exit 1
    fi
fi

echo ""
echo "Running schema scripts..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEMA_DIR="$PROJECT_ROOT/database/schemas"

# Array of schema files in order
SCHEMA_FILES=(
    "00_init_database.sql"
    "01_create_schema.sql"
    "02_indicator_table.sql"
    "03_geography_table.sql"
    "04_stratifier_table.sql"
    "05_observation_table.sql"
    "06_ingestion_log_table.sql"
    "07_triggers_and_functions.sql"
)

# Run each schema file
for schema_file in "${SCHEMA_FILES[@]}"; do
    schema_path="$SCHEMA_DIR/$schema_file"
    if [ -f "$schema_path" ]; then
        echo "  Running $schema_file..."
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$schema_path" > /dev/null 2>&1; then
            echo -e "    ${GREEN}✓${NC} $schema_file"
        else
            echo -e "    ${RED}✗${NC} Error running $schema_file"
            echo "    Check the error above and fix any issues."
            exit 1
        fi
    else
        echo -e "    ${RED}✗${NC} File not found: $schema_path"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Database setup complete!${NC}"
echo "=========================================="
echo ""
echo "Verifying schema creation..."

# Verify tables were created
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'cdc';" | tr -d ' ')

if [ "$TABLE_COUNT" -ge 5 ]; then
    echo -e "${GREEN}✓ Found $TABLE_COUNT tables in 'cdc' schema${NC}"
    echo ""
    echo "Tables created:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt cdc.*" | cat
else
    echo -e "${YELLOW}⚠ Expected at least 5 tables, found $TABLE_COUNT${NC}"
fi

echo ""
echo "Next steps:"
echo "1. Update config/.env with your database credentials"
echo "2. Test the connection using the test script"
echo ""
