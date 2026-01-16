# Database Schema Documentation

This directory contains SQL schema definitions for the CDC Health Data Pipeline database.

## Schema Overview

The database uses a **star schema** design with:
- **Dimension tables**: `indicator`, `geography`, `stratifier` (reference data)
- **Fact table**: `observation` (actual measurements)
- **Audit table**: `ingestion_log` (pipeline tracking)

## Schema Execution Order

Run the SQL files in this order:

1. `00_init_database.sql` - Database initialization and extensions
2. `01_create_schema.sql` - Create the `cdc` schema
3. `02_indicator_table.sql` - Indicator reference table
4. `03_geography_table.sql` - Geography reference table
5. `04_stratifier_table.sql` - Stratifier (demographic breakdown) table
6. `05_observation_table.sql` - Main observation fact table
7. `06_ingestion_log_table.sql` - Ingestion audit log table
8. `07_triggers_and_functions.sql` - Triggers and helper functions

## Quick Setup

```bash
# Connect to PostgreSQL
psql -U your_db_user -d cdc_health_data

# Run all schemas in order
\i database/schemas/00_init_database.sql
\i database/schemas/01_create_schema.sql
\i database/schemas/02_indicator_table.sql
\i database/schemas/03_geography_table.sql
\i database/schemas/04_stratifier_table.sql
\i database/schemas/05_observation_table.sql
\i database/schemas/06_ingestion_log_table.sql
\i database/schemas/07_triggers_and_functions.sql
```

Or use a single command:
```bash
psql -U your_db_user -d cdc_health_data -f database/schemas/00_init_database.sql
# ... repeat for each file
```

## Schema Design Decisions

### 1. Normalized Reference Tables
- **Why**: Reduces data duplication, ensures consistency, enables efficient filtering
- **Trade-off**: Requires joins for queries, but improves data integrity

### 2. Identity Columns (not SERIAL)
- **Why**: SQL standard compliant, better for replication, more explicit
- **PostgreSQL 10+**: Uses `GENERATED ALWAYS AS IDENTITY`

### 3. JSONB for Metadata
- **Why**: Flexible storage for CDC-specific fields that may vary by dataset
- **Benefit**: Can query JSONB fields while maintaining structured core data

### 4. Unique Constraints
- **Why**: Prevents duplicate observations (same indicator + geography + time + stratifier)
- **Implementation**: Uses `COALESCE` to handle NULL stratifier_id in unique constraint

### 5. Check Constraints
- **Why**: Enforces data quality at database level
- **Examples**: Non-negative values, valid status values, period validation

## Key Tables

### `cdc.indicator`
Stores metadata about health metrics (e.g., "COVID-19 Cases per 100,000", "Vaccination Rate").

### `cdc.geography`
Stores geographic locations (nation, state, county) with FIPS codes for precise identification.

### `cdc.stratifier`
Stores demographic breakdowns (age groups, gender, race/ethnicity) for filtering data.

### `cdc.observation`
**Core fact table** linking indicators, geography, time periods, and optional stratifiers with actual measurement values.

### `cdc.ingestion_log`
Tracks pipeline runs for observability and debugging.

## Example Queries

### Get COVID cases by state for 2023
```sql
SELECT 
    g.state_name,
    o.period_start,
    o.value
FROM cdc.observation o
JOIN cdc.indicator i ON o.indicator_id = i.id
JOIN cdc.geography g ON o.geography_id = g.id
WHERE i.code = 'COVID_CASES_PER100K'
  AND g.level = 'state'
  AND o.period_start >= '2023-01-01'
ORDER BY g.state_name, o.period_start;
```

### Get latest observation for each indicator
```sql
SELECT DISTINCT ON (i.code)
    i.code,
    i.name,
    o.value,
    o.period_start
FROM cdc.observation o
JOIN cdc.indicator i ON o.indicator_id = i.id
ORDER BY i.code, o.period_start DESC;
```

## Migration Management

For production, use **Alembic** (included in requirements) for version-controlled migrations:
- Schema changes go in `database/migrations/`
- Alembic tracks version history
- Enables rollback and team collaboration
