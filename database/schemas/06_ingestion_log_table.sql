-- Ingestion Log Table
-- Tracks data pipeline runs, success/failure, and metadata for observability

CREATE TABLE IF NOT EXISTS cdc.ingestion_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id VARCHAR(100) UNIQUE NOT NULL,             -- Unique identifier for this pipeline run
    data_source VARCHAR(255) NOT NULL,               -- CDC API endpoint or dataset name
    status VARCHAR(20) NOT NULL,                     -- 'running', 'completed', 'failed', 'partial'
    records_processed INTEGER DEFAULT 0,             -- Number of records processed
    records_inserted INTEGER DEFAULT 0,              -- Number of records successfully inserted
    records_failed INTEGER DEFAULT 0,                -- Number of records that failed validation/insertion
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,           -- NULL if still running
    error_message TEXT,                               -- Error details if status is 'failed'
    metadata JSONB,                                   -- Additional run metadata (API response info, etc.)
    CONSTRAINT ingestion_log_status_check CHECK (
        status IN ('running', 'completed', 'failed', 'partial')
    )
);

-- Indexes
CREATE INDEX idx_ingestion_log_status ON cdc.ingestion_log(status);
CREATE INDEX idx_ingestion_log_started ON cdc.ingestion_log(started_at DESC);
CREATE INDEX idx_ingestion_log_data_source ON cdc.ingestion_log(data_source);

-- Comments
COMMENT ON TABLE cdc.ingestion_log IS 'Audit log for data pipeline ingestion runs';
COMMENT ON COLUMN cdc.ingestion_log.run_id IS 'Unique identifier for tracking pipeline execution';
COMMENT ON COLUMN cdc.ingestion_log.metadata IS 'JSONB field for storing API response metadata, timing info, etc.';
