"""Configuration management for TimescaleDB MCP Server."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class TimescaleDBConfig(BaseSettings):
    """TimescaleDB connection configuration.

    Configuration is loaded from environment variables with the TIMESCALEDB_ prefix.
    Example:
        TIMESCALEDB_HOST=localhost
        TIMESCALEDB_PORT=5432
        TIMESCALEDB_DATABASE=mydb
        TIMESCALEDB_USER=postgres
        TIMESCALEDB_PASSWORD=secret
    """

    model_config = SettingsConfigDict(
        env_prefix="TIMESCALEDB_",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: str = ""

    # Connection pool settings
    min_pool_size: int = 1
    max_pool_size: int = 10

    # Query timeout in seconds
    query_timeout: Optional[float] = None


def get_config() -> TimescaleDBConfig:
    """Get TimescaleDB configuration from environment variables.

    Returns:
        TimescaleDBConfig instance with loaded configuration
    """
    return TimescaleDBConfig()
