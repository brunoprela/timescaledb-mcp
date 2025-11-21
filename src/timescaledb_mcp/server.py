"""MCP Server implementation for TimescaleDB with Resources and Prompts."""

import asyncio
import json
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    Prompt,
    PromptMessage,
    PromptArgument,
)
from pydantic import AnyUrl

from .config import get_config
from .database import TimescaleDBClient
from .exceptions import (
    TimescaleDBMCPError,
    TableNotFoundError,
    HypertableNotFoundError,
    QueryExecutionError,
)

logger = logging.getLogger(__name__)

# Initialize server
app = Server("timescaledb-mcp")

# Global database client (initialized in main)
db_client: TimescaleDBClient | None = None


async def get_db_client() -> TimescaleDBClient:
    """Get the database client, initializing if necessary."""
    global db_client
    if db_client is None:
        config = get_config()
        db_client = TimescaleDBClient(config)
        await db_client.initialize()
    return db_client


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List all available resources."""
    try:
        client = await get_db_client()
        tables = await client.list_tables()
        hypertables = await client.list_hypertables()

        resources = []

        # Add table resources
        for table in tables:
            resources.append(
                Resource(
                    uri=AnyUrl(f"timescaledb://table/{table}"),
                    name=f"Table: {table}",
                    description=f"Schema and metadata for table '{table}'",
                    mimeType="application/json",
                )
            )

        # Add hypertable resources
        for ht in hypertables:
            resources.append(
                Resource(
                    uri=AnyUrl(f"timescaledb://hypertable/{ht['hypertable_name']}"),
                    name=f"Hypertable: {ht['hypertable_name']}",
                    description=f"Schema and metadata for hypertable '{ht['hypertable_name']}'",
                    mimeType="application/json",
                )
            )

        return resources
    except Exception as e:
        logger.error(f"Error listing resources: {e}", exc_info=True)
        return []


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    try:
        client = await get_db_client()

        if uri.startswith("timescaledb://table/"):
            table_name = uri.replace("timescaledb://table/", "")
            table_info = await client.describe_table(table_name)
            return json.dumps(table_info, indent=2, default=str)

        elif uri.startswith("timescaledb://hypertable/"):
            hypertable_name = uri.replace("timescaledb://hypertable/", "")
            hypertable_info = await client.describe_hypertable(hypertable_name)
            return json.dumps(hypertable_info, indent=2, default=str)

        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    except TableNotFoundError as e:
        raise ValueError(f"Table not found: {str(e)}") from e
    except HypertableNotFoundError as e:
        raise ValueError(f"Hypertable not found: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
        raise ValueError(f"Error reading resource: {str(e)}") from e


@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List all available prompts."""
    return [
        Prompt(
            name="query_timeseries_data",
            description="Generate a query to retrieve time-series data from a hypertable",
            arguments=[
                PromptArgument(
                    name="hypertable_name",
                    description="Name of the hypertable to query",
                    required=True,
                ),
                PromptArgument(
                    name="time_range",
                    description="Time range for the query (e.g., 'last 24 hours', 'last week')",
                    required=False,
                ),
            ],
        ),
        Prompt(
            name="analyze_hypertable",
            description="Analyze a hypertable's structure, chunks, and performance metrics",
            arguments=[
                PromptArgument(
                    name="hypertable_name",
                    description="Name of the hypertable to analyze",
                    required=True,
                ),
            ],
        ),
        Prompt(
            name="explore_database_schema",
            description="Explore the database schema and get an overview of all tables and hypertables",
            arguments=[],
        ),
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, Any] | None) -> list[PromptMessage]:
    """Get a prompt by name."""
    try:
        client = await get_db_client()

        if name == "query_timeseries_data":
            hypertable_name = arguments.get("hypertable_name") if arguments else None
            time_range = arguments.get("time_range") if arguments else None

            if not hypertable_name:
                raise ValueError("hypertable_name is required")

            # Get hypertable info
            try:
                ht_info = await client.describe_hypertable(hypertable_name)
                time_column = ht_info.get("dimensions", [{}])[0].get("column_name", "time")
            except Exception:
                time_column = "time"

            prompt_text = f"""Query time-series data from the '{hypertable_name}' hypertable.

Time column: {time_column}
"""
            if time_range:
                prompt_text += f"Time range: {time_range}\n"

            prompt_text += """
Example queries:
1. Get recent data: SELECT * FROM "{hypertable_name}" ORDER BY {time_column} DESC LIMIT 100;
2. Aggregate by hour: SELECT time_bucket('1 hour', {time_column}) AS bucket, AVG(value) FROM "{hypertable_name}" GROUP BY bucket;
3. Filter by time range: SELECT * FROM "{hypertable_name}" WHERE {time_column} >= NOW() - INTERVAL '24 hours';
"""

            return [
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text),
                )
            ]

        elif name == "analyze_hypertable":
            hypertable_name = arguments.get("hypertable_name") if arguments else None

            if not hypertable_name:
                raise ValueError("hypertable_name is required")

            ht_info = await client.describe_hypertable(hypertable_name)

            analysis = f"""Analysis of hypertable '{hypertable_name}':

Dimensions: {ht_info.get('num_dimensions', 0)}
Compression: {'Enabled' if ht_info.get('compression_enabled') else 'Disabled'}

Dimensions:
{json.dumps(ht_info.get('dimensions', []), indent=2, default=str)}

Recent Chunks:
{json.dumps(ht_info.get('recent_chunks', [])[:5], indent=2, default=str)}
"""

            return [
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=analysis),
                )
            ]

        elif name == "explore_database_schema":
            tables = await client.list_tables()
            hypertables = await client.list_hypertables()

            schema_text = f"""Database Schema Overview:

Tables ({len(tables)}):
{chr(10).join(f"  - {t}" for t in tables)}

Hypertables ({len(hypertables)}):
{chr(10).join(f"  - {ht['hypertable_name']} (dimensions: {ht['num_dimensions']}, compression: {'enabled' if ht['compression_enabled'] else 'disabled'})" for ht in hypertables)}

Use the describe_table or describe_hypertable tools to get detailed information about specific tables or hypertables.
"""

            return [
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=schema_text),
                )
            ]

        else:
            raise ValueError(f"Unknown prompt: {name}")

    except Exception as e:
        logger.error(f"Error getting prompt {name}: {e}", exc_info=True)
        raise ValueError(f"Error getting prompt: {str(e)}") from e


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="execute_query",
            description="Execute a SQL query on TimescaleDB and return the results. Use this for any SQL operations including SELECT, INSERT, UPDATE, DELETE, etc. Always use parameterized queries for user input.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute. Use $1, $2, etc. for parameters.",
                    },
                    "parameters": {
                        "type": "array",
                        "description": "Optional array of parameters for parameterized queries",
                        "items": {"type": "string"},
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="describe_table",
            description="Get detailed information about a table including columns, data types, and row count",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the table to describe",
                    }
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="list_hypertables",
            description="List all TimescaleDB hypertables in the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="describe_hypertable",
            description="Get detailed information about a TimescaleDB hypertable including dimensions, chunks, and compression settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "hypertable_name": {
                        "type": "string",
                        "description": "The name of the hypertable to describe",
                    }
                },
                "required": ["hypertable_name"],
            },
        ),
        Tool(
            name="query_timeseries",
            description="Query time-series data from a hypertable with optional time-bucketing. This is optimized for TimescaleDB time-series queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hypertable_name": {
                        "type": "string",
                        "description": "The name of the hypertable to query",
                    },
                    "time_column": {
                        "type": "string",
                        "description": "The name of the time column (default: 'time')",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time for the query (ISO 8601 format or PostgreSQL timestamp)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time for the query (ISO 8601 format or PostgreSQL timestamp)",
                    },
                    "bucket_interval": {
                        "type": "string",
                        "description": "Optional time bucket interval (e.g., '1 hour', '1 day', '1 week')",
                    },
                    "aggregation": {
                        "type": "string",
                        "description": "Aggregation function to use with time buckets (e.g., 'avg', 'sum', 'count', 'min', 'max')",
                    },
                    "columns": {
                        "type": "string",
                        "description": "Comma-separated list of columns to select (default: '*')",
                    },
                    "where_clause": {
                        "type": "string",
                        "description": "Optional WHERE clause (without the WHERE keyword). Use parameterized format.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return (default: 1000)",
                    },
                },
                "required": ["hypertable_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        client = await get_db_client()

        if name == "execute_query":
            query = arguments.get("query")
            if not query:
                raise ValueError("Query parameter is required")

            params = arguments.get("parameters", [])
            results = await client.execute_query(query, *params)

            result_text = json.dumps(results, indent=2, default=str)

            return [
                TextContent(
                    type="text",
                    text=f"Query executed successfully. Returned {len(results)} row(s).\n\nResults:\n{result_text}",
                )
            ]

        elif name == "list_tables":
            tables = await client.list_tables()
            return [
                TextContent(
                    type="text",
                    text=f"Found {len(tables)} table(s):\n"
                    + "\n".join(f"- {table}" for table in tables),
                )
            ]

        elif name == "describe_table":
            table_name = arguments.get("table_name")
            if not table_name:
                raise ValueError("table_name parameter is required")

            table_info = await client.describe_table(table_name)
            info_text = json.dumps(table_info, indent=2, default=str)

            return [
                TextContent(
                    type="text",
                    text=f"Table information for '{table_name}':\n{info_text}",
                )
            ]

        elif name == "list_hypertables":
            hypertables = await client.list_hypertables()

            if not hypertables:
                return [
                    TextContent(
                        type="text",
                        text="No hypertables found in the database.",
                    )
                ]

            result_text = f"Found {len(hypertables)} hypertable(s):\n\n"
            for ht in hypertables:
                result_text += f"- {ht['hypertable_name']} "
                result_text += f"(dimensions: {ht['num_dimensions']}, "
                result_text += (
                    f"compression: {'enabled' if ht['compression_enabled'] else 'disabled'})\n"
                )

            return [TextContent(type="text", text=result_text)]

        elif name == "describe_hypertable":
            hypertable_name = arguments.get("hypertable_name")
            if not hypertable_name:
                raise ValueError("hypertable_name parameter is required")

            hypertable_info = await client.describe_hypertable(hypertable_name)
            info_text = json.dumps(hypertable_info, indent=2, default=str)

            return [
                TextContent(
                    type="text",
                    text=f"Hypertable information for '{hypertable_name}':\n{info_text}",
                )
            ]

        elif name == "query_timeseries":
            hypertable_name = arguments.get("hypertable_name")
            if not hypertable_name:
                raise ValueError("hypertable_name parameter is required")

            time_column = arguments.get("time_column", "time")
            start_time = arguments.get("start_time")
            end_time = arguments.get("end_time")
            bucket_interval = arguments.get("bucket_interval")
            aggregation = arguments.get("aggregation")
            columns = arguments.get("columns", "*")
            where_clause = arguments.get("where_clause")
            limit = arguments.get("limit", 1000)

            # Validate hypertable name (basic SQL injection prevention)
            if not hypertable_name.replace("_", "").replace(".", "").replace('"', "").isalnum():
                raise ValueError(f"Invalid hypertable name: {hypertable_name}")

            # Escape hypertable name for use in query
            escaped_hypertable = hypertable_name.replace('"', '""')

            # Build parameterized query
            query_parts = []
            params = []
            param_idx = 1

            if bucket_interval:
                if aggregation and columns != "*":
                    query_parts.append(
                        f'SELECT time_bucket(${param_idx}, {time_column}) AS bucket, {aggregation}({columns}) AS aggregated_value FROM "{escaped_hypertable}"'
                    )
                    params.append(bucket_interval)
                    param_idx += 1
                elif aggregation:
                    query_parts.append(
                        f'SELECT time_bucket(${param_idx}, {time_column}) AS bucket, COUNT(*) AS count FROM "{escaped_hypertable}"'
                    )
                    params.append(bucket_interval)
                    param_idx += 1
                else:
                    query_parts.append(
                        f'SELECT time_bucket(${param_idx}, {time_column}) AS bucket, {columns} FROM "{escaped_hypertable}"'
                    )
                    params.append(bucket_interval)
                    param_idx += 1
            else:
                query_parts.append(f'SELECT {columns} FROM "{escaped_hypertable}"')

            # Add WHERE clause
            conditions = []
            if start_time:
                conditions.append(f"{time_column} >= ${param_idx}")
                params.append(start_time)
                param_idx += 1
            if end_time:
                conditions.append(f"{time_column} <= ${param_idx}")
                params.append(end_time)
                param_idx += 1
            if where_clause:
                conditions.append(where_clause)

            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            # Add ORDER BY and LIMIT
            if bucket_interval:
                query_parts.append("GROUP BY bucket ORDER BY bucket")
            else:
                query_parts.append(f"ORDER BY {time_column}")

            query_parts.append(f"LIMIT ${param_idx}")
            params.append(limit)

            query = " ".join(query_parts)

            results = await client.execute_query(query, *params)
            result_text = json.dumps(results, indent=2, default=str)

            return [
                TextContent(
                    type="text",
                    text=f"Time-series query executed successfully. Returned {len(results)} row(s).\n\nQuery:\n{query}\n\nResults:\n{result_text}",
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except (TableNotFoundError, HypertableNotFoundError) as e:
        logger.error(f"Resource not found: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )
        ]
    except QueryExecutionError as e:
        logger.error(f"Query execution error: {e}")
        return [
            TextContent(
                type="text",
                text=f"Query execution error: {str(e)}",
            )
        ]
    except TimescaleDBMCPError as e:
        logger.error(f"TimescaleDB MCP error: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )
        ]
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"Unexpected error: {str(e)}",
            )
        ]


async def main():
    """Main entry point for the MCP server."""
    global db_client

    try:
        config = get_config()
        db_client = TimescaleDBClient(config)
        await db_client.initialize()

        if not await db_client.test_connection():
            logger.warning(
                "Failed to connect to TimescaleDB. Server will start but queries may fail."
            )
        else:
            logger.info("Successfully connected to TimescaleDB")

        # Run the server using stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    finally:
        if db_client:
            await db_client.close()


def cli():
    """CLI entry point for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    cli()
