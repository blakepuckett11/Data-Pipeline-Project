# Data Pipeline Project

End-to-end data pipeline for ingesting, processing, and serving CDC public health data.

## Project Structure

```
Data-Pipeline-Project/
├── data_pipeline/          # ETL pipeline components
│   ├── ingestion/          # Data extraction from CDC API
│   ├── validation/         # Data quality checks and validation
│   ├── transformation/     # Data cleaning and transformation logic
│   └── loading/            # Data loading into PostgreSQL
│
├── backend/                # FastAPI backend service
│   ├── api/                # API route handlers and endpoints
│   ├── models/             # Pydantic models and data schemas
│   └── services/           # Business logic and data access layer
│
├── database/               # Database-related files
│   ├── migrations/         # Alembic migration scripts
│   └── schemas/            # SQL schema definitions
│
├── frontend/               # Next.js frontend (initialized separately)
│
├── config/                 # Configuration files and environment management
│
├── tests/                  # Test suites
│   ├── unit/               # Unit tests for individual components
│   └── integration/        # Integration tests for pipeline flows
│
├── scripts/                # Utility scripts (deployment, maintenance, etc.)
│
├── utils/                  # Shared utility functions and helpers
│
├── docs/                   # Project documentation
│   ├── architecture/       # System architecture diagrams and docs
│   ├── api/                # API documentation
│   └── deployment/         # Deployment guides and runbooks
│
└── .github/workflows/      # CI/CD pipeline definitions

```

## Directory Purposes

### `data_pipeline/`
Core ETL pipeline components following a modular design:
- **ingestion/**: Handles API connections, rate limiting, error handling, and raw data extraction from CDC Open Data API
- **validation/**: Implements data quality checks, schema validation, and anomaly detection before transformation
- **transformation/**: Contains data cleaning, normalization, aggregation, and business rule application logic
- **loading/**: Manages database connections, batch inserts, upserts, and loading strategies into PostgreSQL

### `backend/`
FastAPI application serving analytics endpoints:
- **api/**: RESTful API route definitions, request/response handling, and endpoint documentation
- **models/**: Pydantic models for request/response validation and data serialization
- **services/**: Business logic layer that queries the database and processes data for API responses

### `database/`
Database schema and migration management:
- **migrations/**: Alembic migration scripts for version-controlled schema changes
- **schemas/**: SQL DDL files defining table structures, indexes, and constraints

### `frontend/`
Next.js dashboard application (to be initialized separately or linked)

### `config/`
Configuration management:
- Environment-specific config files
- Database connection settings
- API keys and secrets (via environment variables)

### `tests/`
Comprehensive testing:
- **unit/**: Tests for individual functions, classes, and modules
- **integration/**: End-to-end tests for complete pipeline flows and API endpoints

### `scripts/`
Operational scripts:
- Data pipeline orchestration
- Database maintenance tasks
- Deployment helpers

### `utils/`
Shared utilities:
- Common helper functions
- Logging configuration
- Error handling utilities

### `docs/`
Project documentation:
- **architecture/**: System design, data flow diagrams, component interactions
- **api/**: API endpoint documentation, request/response examples
- **deployment/**: Deployment procedures, environment setup guides

### `.github/workflows/`
CI/CD automation:
- Automated testing on pull requests
- Deployment workflows
- Code quality checks

## Next Steps

1. Set up Python virtual environment and dependencies
2. Configure PostgreSQL database connection
3. Implement data ingestion module
4. Design database schema
5. Build validation and transformation layers
6. Create FastAPI backend endpoints
7. Set up testing framework
