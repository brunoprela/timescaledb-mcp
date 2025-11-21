"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator

from timescaledb_mcp.config import TimescaleDBConfig, get_config
from timescaledb_mcp.database import TimescaleDBClient
from timescaledb_mcp.exceptions import DatabaseConnectionError


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_config() -> TimescaleDBConfig:
    """Get database configuration for testing."""
    # Always use get_config() which reads from environment variables
    # The Makefile sets these when running tests
    config = get_config()
    return config


@pytest.fixture
async def db_client(db_config: TimescaleDBConfig) -> AsyncGenerator[TimescaleDBClient, None]:
    """Create a database client for testing.

    Skips tests if database is not available.
    """
    client = TimescaleDBClient(db_config)
    try:
        await client.initialize()
        # Test the connection - this will fail if DB is not ready
        if not await client.test_connection():
            pytest.skip("Database not available")
        yield client
    except DatabaseConnectionError as e:
        pytest.skip(f"Database not available: {e}")
    finally:
        await client.close()
