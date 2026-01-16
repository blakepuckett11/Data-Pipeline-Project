-- Geography Reference Table
-- Stores geographic locations (country, state, county) with FIPS codes
-- Normalized to avoid duplication and enable efficient geographic queries

CREATE TABLE IF NOT EXISTS cdc.geography (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country VARCHAR(3) NOT NULL DEFAULT 'USA',      -- ISO country code
    state VARCHAR(2),                                -- US state abbreviation (e.g., 'CA', 'NY')
    state_name VARCHAR(100),                        -- Full state name
    county VARCHAR(100),                             -- County name (nullable for state/national level)
    fips_code VARCHAR(10) UNIQUE,                   -- FIPS code (Federal Information Processing Standard)
    level VARCHAR(20) NOT NULL,                     -- Geographic level: 'nation', 'state', 'county'
    region VARCHAR(50),                              -- US Census region (e.g., 'Northeast', 'South')
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT geography_level_check CHECK (level IN ('nation', 'state', 'county', 'metro')),
    CONSTRAINT geography_state_check CHECK (
        (level = 'nation' AND state IS NULL) OR
        (level IN ('state', 'county', 'metro') AND state IS NOT NULL)
    )
);

-- Indexes for geographic queries
CREATE INDEX idx_geography_state ON cdc.geography(state);
CREATE INDEX idx_geography_level ON cdc.geography(level);
CREATE INDEX idx_geography_fips ON cdc.geography(fips_code);
CREATE INDEX idx_geography_state_county ON cdc.geography(state, county) WHERE county IS NOT NULL;

-- Comments
COMMENT ON TABLE cdc.geography IS 'Reference table for geographic locations in CDC data';
COMMENT ON COLUMN cdc.geography.fips_code IS 'FIPS code for precise geographic identification';
COMMENT ON COLUMN cdc.geography.level IS 'Geographic aggregation level: nation, state, county, or metro area';
