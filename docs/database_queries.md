# Database Query Examples

Quick reference for checking data in PostgreSQL.

## Connect to Database

```bash
psql -U blakepuckett -d cdc_health_data
```

## Check Table Counts

```sql
-- Count records in each table
SELECT 'indicator' as table_name, COUNT(*) FROM cdc.indicator
UNION ALL
SELECT 'geography', COUNT(*) FROM cdc.geography
UNION ALL
SELECT 'stratifier', COUNT(*) FROM cdc.stratifier
UNION ALL
SELECT 'observation', COUNT(*) FROM cdc.observation
UNION ALL
SELECT 'ingestion_log', COUNT(*) FROM cdc.ingestion_log;
```

## View Recent Observations

```sql
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
LIMIT 10;
```

## View All Indicators

```sql
SELECT code, name, unit, category
FROM cdc.indicator
ORDER BY code;
```

## View Geography Records

```sql
SELECT level, COUNT(*) as count
FROM cdc.geography
GROUP BY level
ORDER BY level;
```

## View Recent Ingestion Runs

```sql
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
LIMIT 10;
```

## Check Specific Indicator Data

```sql
SELECT 
    g.state_name,
    g.county,
    o.period_start,
    o.value
FROM cdc.observation o
JOIN cdc.indicator i ON o.indicator_id = i.id
JOIN cdc.geography g ON o.geography_id = g.id
WHERE i.code = 'TEST_INDICATOR'
ORDER BY o.period_start DESC;
```

## View Table Structure

```sql
-- View observation table structure
\d cdc.observation

-- View indicator table structure
\d cdc.indicator

-- View geography table structure
\d cdc.geography
```

## Useful Commands

```sql
-- List all tables in cdc schema
\dt cdc.*

-- View table with more details
\d+ cdc.observation

-- Exit psql
\q
```
