"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator

from timescaledb_mcp.config import TimescaleDBConfig
from timescaledb_mcp.database import TimescaleDBClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_config() -> TimescaleDBConfig:
    """Get database configuration for testing."""
    return TimescaleDBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="",
    )


@pytest.fixture
async def db_client(db_config: TimescaleDBConfig) -> AsyncGenerator[TimescaleDBClient, None]:
    """Create a database client for testing."""
    client = TimescaleDBClient(db_config)
    try:
        await client.initialize()
        yield client
    finally:
        await client.close()

