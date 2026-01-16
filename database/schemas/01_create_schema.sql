-- CDC Health Data Pipeline - Database Schema
-- This schema is designed to store structured CDC public health data
-- Supports various data types: indicators, geography, time periods, and stratifiers

-- Create dedicated schema for CDC data
CREATE SCHEMA IF NOT EXISTS cdc;

-- Set search path for convenience (optional, can be set per session)
-- SET search_path TO cdc, public;
