-- Initial Database Setup Script
-- Run this first to create the database and user (adjust as needed)
-- Note: This requires superuser privileges. Run as postgres user or admin.

-- Create database (uncomment if needed)
-- CREATE DATABASE cdc_health_data
--     WITH OWNER = your_db_user
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'en_US.UTF-8'
--     LC_CTYPE = 'en_US.UTF-8'
--     TEMPLATE = template0;

-- Connect to the database before running other scripts
-- \c cdc_health_data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text similarity searches if needed

-- Note: Run schema files in order:
-- 01_create_schema.sql
-- 02_indicator_table.sql
-- 03_geography_table.sql
-- 04_stratifier_table.sql
-- 05_observation_table.sql
-- 06_ingestion_log_table.sql
-- 07_triggers_and_functions.sql
