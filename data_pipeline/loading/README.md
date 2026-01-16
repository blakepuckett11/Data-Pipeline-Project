# Data Loading Module

This module loads transformed data into PostgreSQL database.

## Overview

The loading module:
- **Connects to PostgreSQL**: Manages database connections efficiently
- **Loads Reference Data**: Handles indicators, geography, stratifiers
- **Loads Observations**: Inserts fact records with duplicate handling
- **Tracks Runs**: Logs ingestion runs for observability
- **Handles Errors**: Continues processing even if some records fail

## Components

### `db_connection.py`
Database connection management:
- `DatabaseConnection`: Connection pool manager
- Context manager for cursors
- Automatic connection handling

### `reference_data.py`
Reference data management:
- `ReferenceDataManager`: Handles reference tables
- `get_or_create_indicator()`: Indicator lookup/creation
- `get_or_create_geography()`: Geography lookup/creation
- `get_or_create_stratifier()`: Stratifier lookup/creation

### `loader.py`
Main data loader:
- `DataLoader`: Orchestrates data loading
- `load_batch()`: Loads batches of records
- `start_ingestion_run()` / `complete_ingestion_run()`: Run tracking
- Handles duplicates with upsert logic

## Usage Example

```python
from data_pipeline.loading.loader import DataLoader

# Create loader
loader = DataLoader()

# Load transformed records
result = loader.load_batch(
    records=transformed_records,
    data_source="COVID-19 Dataset",
    indicator_code="COVID_CASES",
    indicator_name="COVID-19 Cases"
)

# Check results
print(f"Inserted: {result['records_inserted']}")
print(f"Failed: {result['records_failed']}")
```

## Loading Flow

```
Transformed Records
       ↓
   DataLoader
       ↓
   Get/Create Indicator
       ↓
   Get/Create Geography
       ↓
   Get/Create Stratifier (if needed)
       ↓
   Insert Observation
   (with upsert on conflict)
       ↓
   Update Ingestion Log
       ↓
   Return Statistics
```

## Duplicate Handling

The loader uses PostgreSQL's `ON CONFLICT` to handle duplicates:
- If observation already exists (same indicator + geography + time + stratifier), it updates the value
- Prevents duplicate records while allowing data updates

## Error Handling

- Individual record failures don't stop the batch
- Errors are logged and tracked
- Ingestion run status reflects success/failure
- Failed records are counted and reported

## Next Steps

After loading, data is available for:
1. **FastAPI Backend**: Query data via API
2. **Analytics Dashboard**: Visualize data in Next.js frontend
