-- Stratifier Reference Table
-- Stores demographic and categorical breakdowns (age groups, gender, race/ethnicity, etc.)
-- Enables filtering and analysis by various dimensions

CREATE TABLE IF NOT EXISTS cdc.stratifier (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dimension VARCHAR(50) NOT NULL,                 -- Dimension type: 'age_group', 'gender', 'race', 'ethnicity', etc.
    value VARCHAR(100) NOT NULL,                    -- Dimension value (e.g., '18-24', 'Male', 'White')
    display_order INTEGER,                           -- Optional ordering for UI display
    parent_id BIGINT REFERENCES cdc.stratifier(id), -- For hierarchical stratifiers
    metadata JSONB,                                 -- Additional metadata if needed
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stratifier_dimension_check CHECK (
        dimension IN ('age_group', 'gender', 'race', 'ethnicity', 'education', 'income', 'other')
    ),
    CONSTRAINT stratifier_unique_value UNIQUE (dimension, value)
);

-- Indexes
CREATE INDEX idx_stratifier_dimension ON cdc.stratifier(dimension);
CREATE INDEX idx_stratifier_parent ON cdc.stratifier(parent_id) WHERE parent_id IS NOT NULL;

-- Comments
COMMENT ON TABLE cdc.stratifier IS 'Reference table for demographic and categorical breakdowns';
COMMENT ON COLUMN cdc.stratifier.dimension IS 'Type of stratification dimension (age_group, gender, race, etc.)';
COMMENT ON COLUMN cdc.stratifier.value IS 'Specific value within the dimension';
