-- Observation Fact Table
-- Core table storing actual health data observations/measurements
-- Links indicators, geography, time periods, and optional stratifiers

CREATE TABLE IF NOT EXISTS cdc.observation (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    indicator_id BIGINT NOT NULL REFERENCES cdc.indicator(id) ON DELETE RESTRICT,
    geography_id BIGINT NOT NULL REFERENCES cdc.geography(id) ON DELETE RESTRICT,
    stratifier_id BIGINT REFERENCES cdc.stratifier(id) ON DELETE SET NULL,  -- Optional demographic breakdown
    period_start DATE NOT NULL,                      -- Start of measurement period
    period_end DATE NOT NULL,                        -- End of measurement period
    value NUMERIC(15, 4) NOT NULL,                   -- The actual measurement value
    value_lower_bound NUMERIC(15, 4),                -- Optional confidence interval lower bound
    value_upper_bound NUMERIC(15, 4),                -- Optional confidence interval upper bound
    sample_size INTEGER,                              -- Sample size if applicable
    value_notes TEXT,                                 -- Notes about the value (e.g., "suppressed", "unreliable")
    data_source VARCHAR(255),                         -- Source dataset or API endpoint
    data_source_id VARCHAR(100),                     -- Original record ID from CDC API
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT observation_period_check CHECK (period_end >= period_start),
    CONSTRAINT observation_value_check CHECK (value >= 0)  -- Assuming non-negative values
);

-- Unique index to prevent duplicate observations
-- Uses COALESCE to handle NULL stratifier_id (treats NULL as -1 for uniqueness)
CREATE UNIQUE INDEX idx_observation_unique_observation ON cdc.observation (
    indicator_id, 
    geography_id, 
    COALESCE(stratifier_id, -1),
    period_start, 
    period_end
);

-- Indexes for efficient querying
CREATE INDEX idx_observation_indicator ON cdc.observation(indicator_id);
CREATE INDEX idx_observation_geography ON cdc.observation(geography_id);
CREATE INDEX idx_observation_stratifier ON cdc.observation(stratifier_id) WHERE stratifier_id IS NOT NULL;
CREATE INDEX idx_observation_period ON cdc.observation(period_start, period_end);
CREATE INDEX idx_observation_ingested ON cdc.observation(ingested_at);
CREATE INDEX idx_observation_data_source ON cdc.observation(data_source, data_source_id);

-- Composite index for common query patterns (indicator + geography + time)
CREATE INDEX idx_observation_query_pattern ON cdc.observation(indicator_id, geography_id, period_start DESC);

-- Comments
COMMENT ON TABLE cdc.observation IS 'Fact table storing health data observations linking indicators, geography, time, and stratifiers';
COMMENT ON COLUMN cdc.observation.value IS 'The measured value for the indicator';
COMMENT ON COLUMN cdc.observation.value_lower_bound IS 'Lower bound of confidence interval if available';
COMMENT ON COLUMN cdc.observation.value_upper_bound IS 'Upper bound of confidence interval if available';
COMMENT ON COLUMN cdc.observation.data_source_id IS 'Original record identifier from CDC API for traceability';
