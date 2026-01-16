-- Indicator Reference Table
-- Stores metadata about health indicators/metrics (e.g., COVID cases, vaccination rates)
-- This is a dimension table that reduces duplication and enables consistent filtering

CREATE TABLE IF NOT EXISTS cdc.indicator (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,              -- Unique identifier (e.g., "COVID_CASES_PER100K", CDC dataset ID)
    name VARCHAR(255) NOT NULL,                     -- Human-readable name
    description TEXT,                                -- Detailed description of the indicator
    unit VARCHAR(50),                                -- Unit of measurement (e.g., "cases per 100,000", "percentage")
    category VARCHAR(100),                           -- Category grouping (e.g., "Infectious Disease", "Mortality")
    data_type VARCHAR(50) DEFAULT 'numeric',        -- Type: numeric, percentage, count, etc.
    metadata JSONB,                                  -- Flexible storage for additional CDC-specific fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT indicator_code_check CHECK (code ~ '^[A-Z0-9_]+$')  -- Enforce code format
);

-- Indexes for common queries
CREATE INDEX idx_indicator_code ON cdc.indicator(code);
CREATE INDEX idx_indicator_category ON cdc.indicator(category);

-- Comments for documentation
COMMENT ON TABLE cdc.indicator IS 'Reference table for health indicators/metrics from CDC data';
COMMENT ON COLUMN cdc.indicator.code IS 'Unique code identifier for the indicator (uppercase, alphanumeric, underscores)';
COMMENT ON COLUMN cdc.indicator.metadata IS 'JSONB field for storing CDC-specific metadata and additional fields';
