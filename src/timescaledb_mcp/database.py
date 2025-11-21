"""Async database connection and query execution for TimescaleDB."""

import asyncio
import asyncpg
from typing import List, Dict, Any, Optional
import logging
from contextlib import asynccontextmanager

from .config import TimescaleDBConfig
from .exceptions import (
    DatabaseConnectionError,
    QueryExecutionError,
    TableNotFoundError,
    HypertableNotFoundError,
)

logger = logging.getLogger(__name__)


class TimescaleDBClient:
    """Async client for interacting with TimescaleDB."""

    def __init__(self, config: TimescaleDBConfig):
        """Initialize the TimescaleDB client with configuration."""
        self.config = config
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
            )
            logger.info(
                f"Database connection pool initialized (min={self.config.min_pool_size}, "
                f"max={self.config.max_pool_size})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self._pool:
            raise DatabaseConnectionError(
                "Connection pool not initialized. Call initialize() first."
            )

        async with self._pool.acquire() as conn:
            yield conn

    async def execute_query(
        self, query: str, *args: Any, timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dictionaries.

        Args:
            query: SQL query string (use $1, $2, etc. for parameters)
            *args: Query parameters
            timeout: Optional query timeout in seconds

        Returns:
            List of dictionaries representing rows

        Raises:
            QueryExecutionError: If query execution fails
        """
        try:
            async with self.get_connection() as conn:
                if timeout is not None:
                    rows = await asyncio.wait_for(conn.fetch(query, *args), timeout=timeout)
                else:
                    rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except asyncio.TimeoutError as e:
            logger.error(f"Query timeout after {timeout} seconds: {e}")
            raise QueryExecutionError(f"Query timeout after {timeout} seconds") from e
        except asyncpg.PostgresError as e:
            logger.error(f"Query execution error: {e}")
            raise QueryExecutionError(f"Database error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise QueryExecutionError(f"Unexpected error: {str(e)}") from e

    async def execute_query_single(
        self, query: str, *args: Any, timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute a SQL query and return a single result."""
        results = await self.execute_query(query, *args, timeout=timeout)
        return results[0] if results else None

    async def execute_command(self, query: str, *args: Any, timeout: Optional[float] = None) -> str:
        """
        Execute a SQL command (INSERT, UPDATE, DELETE, etc.) and return status.

        Args:
            query: SQL command string
            *args: Query parameters
            timeout: Optional query timeout in seconds

        Returns:
            Status message
        """
        try:
            async with self.get_connection() as conn:
                if timeout is not None:
                    result = await asyncio.wait_for(conn.execute(query, *args), timeout=timeout)
                else:
                    result = await conn.execute(query, *args)
                return str(result)
        except asyncio.TimeoutError as e:
            logger.error(f"Command timeout after {timeout} seconds: {e}")
            raise QueryExecutionError(f"Command timeout after {timeout} seconds") from e
        except asyncpg.PostgresError as e:
            logger.error(f"Command execution error: {e}")
            raise QueryExecutionError(f"Database error: {str(e)}") from e

    async def list_tables(self) -> List[str]:
        """List all tables in the database."""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        results = await self.execute_query(query)
        return [row["table_name"] for row in results]

    async def describe_table(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a table.

        Args:
            table_name: Name of the table to describe

        Returns:
            Dictionary containing table information

        Raises:
            TableNotFoundError: If table doesn't exist
        """
        # Validate table name to prevent SQL injection
        if not table_name.replace("_", "").replace(".", "").isalnum():
            raise ValueError(f"Invalid table name: {table_name}")

        # Get column information
        columns_query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = $1
            ORDER BY ordinal_position;
        """
        columns = await self.execute_query(columns_query, table_name)

        if not columns:
            raise TableNotFoundError(f"Table '{table_name}' not found")

        # Get row count
        count_query = 'SELECT COUNT(*) as count FROM "' + table_name.replace('"', '""') + '";'
        count_result = await self.execute_query_single(count_query)
        row_count = count_result["count"] if count_result else 0

        return {"table_name": table_name, "columns": columns, "row_count": row_count}

    async def list_hypertables(self) -> List[Dict[str, Any]]:
        """List all TimescaleDB hypertables."""
        query = """
            SELECT 
                hypertable_schema,
                hypertable_name,
                num_dimensions,
                compression_enabled
            FROM timescaledb_information.hypertables
            ORDER BY hypertable_name;
        """
        return await self.execute_query(query)

    async def describe_hypertable(self, hypertable_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a hypertable.

        Args:
            hypertable_name: Name of the hypertable to describe

        Returns:
            Dictionary containing hypertable information

        Raises:
            HypertableNotFoundError: If hypertable doesn't exist
        """
        # Validate hypertable name
        if not hypertable_name.replace("_", "").replace(".", "").isalnum():
            raise ValueError(f"Invalid hypertable name: {hypertable_name}")

        # Get hypertable info
        # Using only columns that are available in all TimescaleDB versions
        hypertable_query = """
            SELECT 
                hypertable_schema,
                hypertable_name,
                num_dimensions,
                compression_enabled
            FROM timescaledb_information.hypertables
            WHERE hypertable_name = $1;
        """
        hypertable_info = await self.execute_query_single(hypertable_query, hypertable_name)

        if not hypertable_info:
            raise HypertableNotFoundError(f"Hypertable '{hypertable_name}' not found")

        # Get dimension information
        dimensions_query = """
            SELECT 
                dimension_type,
                column_name,
                column_type,
                time_interval,
                integer_interval,
                integer_now_func
            FROM timescaledb_information.dimensions
            WHERE hypertable_name = $1
            ORDER BY dimension_number;
        """
        dimensions = await self.execute_query(dimensions_query, hypertable_name)

        hypertable_info["dimensions"] = dimensions

        # Get chunk information
        # Using only columns that are available in all TimescaleDB versions
        chunks_query = """
            SELECT 
                chunk_schema,
                chunk_name,
                range_start,
                range_end
            FROM timescaledb_information.chunks
            WHERE hypertable_name = $1
            ORDER BY range_start DESC
            LIMIT 10;
        """
        chunks = await self.execute_query(chunks_query, hypertable_name)
        hypertable_info["recent_chunks"] = chunks

        return hypertable_info

    async def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            if not self._pool:
                return False
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
