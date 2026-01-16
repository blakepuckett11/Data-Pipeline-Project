"""
Configuration management utility
Loads environment variables and provides typed configuration access
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from config/.env
project_root = Path(__file__).parent.parent
env_path = project_root / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to environment variables
    load_dotenv()


class DatabaseConfig:
    """Database configuration"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "cdc_health_data")
    user: str = os.getenv("DB_USER", os.getenv("USER", "postgres"))  # Use current user as default
    password: str = os.getenv("DB_PASSWORD", "")
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class CDCAPIConfig:
    """CDC API configuration"""
    base_url: str = os.getenv("CDC_API_BASE_URL", "https://data.cdc.gov/api/views")
    timeout: int = int(os.getenv("CDC_API_TIMEOUT", "30"))
    rate_limit_requests: int = int(os.getenv("CDC_API_RATE_LIMIT_REQUESTS", "100"))
    rate_limit_period: int = int(os.getenv("CDC_API_RATE_LIMIT_PERIOD", "60"))  # seconds


class AppConfig:
    """Application configuration"""
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


class APIConfig:
    """FastAPI configuration"""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"


# Global configuration instances
db_config = DatabaseConfig()
cdc_api_config = CDCAPIConfig()
app_config = AppConfig()
api_config = APIConfig()
