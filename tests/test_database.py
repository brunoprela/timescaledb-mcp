"""Tests for database client.

These tests require a running TimescaleDB instance.
Set TIMESCALEDB_* environment variables or they will be skipped.
"""

import pytest
from timescaledb_mcp.database import TimescaleDBClient
from timescaledb_mcp.exceptions import (
    TableNotFoundError,
    HypertableNotFoundError,
)

pytestmark = pytest.mark.asyncio


async def test_connection_pool_initialization(db_client: TimescaleDBClient):
    """Test that connection pool initializes correctly."""
    assert db_client._pool is not None
    assert await db_client.test_connection()


async def test_execute_query(db_client: TimescaleDBClient):
    """Test executing a simple query."""
    results = await db_client.execute_query("SELECT 1 as test")
    assert len(results) == 1
    assert results[0]["test"] == 1


async def test_execute_query_with_params(db_client: TimescaleDBClient):
    """Test executing a parameterized query."""
    # Use type cast to ensure asyncpg handles the integer correctly
    results = await db_client.execute_query("SELECT $1::int as value", 42)
    assert len(results) == 1
    assert results[0]["value"] == 42


async def test_list_tables(db_client: TimescaleDBClient):
    """Test listing tables."""
    tables = await db_client.list_tables()
    assert isinstance(tables, list)
    # Should at least have information_schema tables or be empty


async def test_describe_table_not_found(db_client: TimescaleDBClient):
    """Test describing a non-existent table raises error."""
    with pytest.raises(TableNotFoundError):
        await db_client.describe_table("nonexistent_table_xyz123")


async def test_list_hypertables(db_client: TimescaleDBClient):
    """Test listing hypertables."""
    hypertables = await db_client.list_hypertables()
    assert isinstance(hypertables, list)


async def test_describe_hypertable_not_found(db_client: TimescaleDBClient):
    """Test describing a non-existent hypertable raises error."""
    with pytest.raises(HypertableNotFoundError):
        await db_client.describe_hypertable("nonexistent_hypertable_xyz123")
