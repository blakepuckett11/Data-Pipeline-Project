-- Triggers and Helper Functions
-- Automatically update 'updated_at' timestamps and provide utility functions

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION cdc.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for indicator table
CREATE TRIGGER update_indicator_updated_at
    BEFORE UPDATE ON cdc.indicator
    FOR EACH ROW
    EXECUTE FUNCTION cdc.update_updated_at_column();

-- Trigger for observation table
CREATE TRIGGER update_observation_updated_at
    BEFORE UPDATE ON cdc.observation
    FOR EACH ROW
    EXECUTE FUNCTION cdc.update_updated_at_column();

-- Helper function to get or create geography record
-- Useful during data loading to avoid duplicate lookups
CREATE OR REPLACE FUNCTION cdc.get_or_create_geography(
    p_state VARCHAR(2),
    p_state_name VARCHAR(100),
    p_county VARCHAR(100) DEFAULT NULL,
    p_fips_code VARCHAR(10) DEFAULT NULL,
    p_level VARCHAR(20) DEFAULT 'state'
)
RETURNS BIGINT AS $$
DECLARE
    v_geography_id BIGINT;
BEGIN
    -- Try to find existing geography
    SELECT id INTO v_geography_id
    FROM cdc.geography
    WHERE state = p_state
      AND (p_county IS NULL AND county IS NULL OR county = p_county)
      AND (p_fips_code IS NULL OR fips_code = p_fips_code);
    
    -- If not found, create it
    IF v_geography_id IS NULL THEN
        INSERT INTO cdc.geography (state, state_name, county, fips_code, level)
        VALUES (p_state, p_state_name, p_county, p_fips_code, p_level)
        RETURNING id INTO v_geography_id;
    END IF;
    
    RETURN v_geography_id;
END;
$$ LANGUAGE plpgsql;

-- Helper function to get or create indicator
CREATE OR REPLACE FUNCTION cdc.get_or_create_indicator(
    p_code VARCHAR(100),
    p_name VARCHAR(255),
    p_unit VARCHAR(50) DEFAULT NULL,
    p_description TEXT DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_indicator_id BIGINT;
BEGIN
    SELECT id INTO v_indicator_id
    FROM cdc.indicator
    WHERE code = p_code;
    
    IF v_indicator_id IS NULL THEN
        INSERT INTO cdc.indicator (code, name, unit, description)
        VALUES (p_code, p_name, p_unit, p_description)
        RETURNING id INTO v_indicator_id;
    END IF;
    
    RETURN v_indicator_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cdc.get_or_create_geography IS 'Helper function to get or create geography records during data loading';
COMMENT ON FUNCTION cdc.get_or_create_indicator IS 'Helper function to get or create indicator records during data loading';
