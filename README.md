# TimescaleDB MCP Server

A Python-based Model Context Protocol (MCP) server for TimescaleDB that enables AI assistants to interact with your time-series database.

## Features

- **Async Database Operations**: Built on `asyncpg` for high-performance async database access
- **Connection Pooling**: Efficient connection pool management with configurable pool sizes
- **MCP Resources**: Schema introspection via MCP resources for tables and hypertables
- **MCP Prompts**: Pre-built prompts for common operations (query time-series, analyze hypertables, explore schema)
- **SQL Injection Prevention**: Parameterized queries throughout for security
- **Comprehensive Error Handling**: Custom exceptions with clear error messages
- **Type Safety**: Full type hints and TypedDict support
- **6 MCP Tools**: Execute queries, list/describe tables and hypertables, query time-series data
- **Structured Logging**: Comprehensive logging for debugging and monitoring

## Installation

### From PyPI

```bash
pip install timescaledb-mcp
```

Or using `uv` (faster):

```bash
uv pip install timescaledb-mcp
```

The package is available on [PyPI](https://pypi.org/project/timescaledb-mcp/).

### From Source

1. Clone this repository:
```bash
git clone https://github.com/brunoprela/timescaledb-mcp.git
cd timescaledb-mcp
```

2. Install using pip:
```bash
pip install -e .
```

Or using `uv`:
```bash
uv pip install -e .
```

For development with additional tools:
```bash
pip install -e ".[dev]"
# or
uv pip install -e ".[dev]"
```

## Configuration

Configuration is managed via environment variables with the `TIMESCALEDB_` prefix.

### Required Settings

```env
TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5432
TIMESCALEDB_DATABASE=your_database
TIMESCALEDB_USER=your_user
TIMESCALEDB_PASSWORD=your_password
```

### Optional Settings

```env
TIMESCALEDB_MIN_POOL_SIZE=1        # Minimum connection pool size (default: 1)
TIMESCALEDB_MAX_POOL_SIZE=10       # Maximum connection pool size (default: 10)
TIMESCALEDB_QUERY_TIMEOUT=30.0     # Query timeout in seconds (default: None)
```

You can set these as environment variables or create a `.env` file in the project root.

## Usage

### Running the Server

After installation, you can run the MCP server in several ways:

**Using the console script:**
```bash
timescaledb-mcp
```

**As a Python module:**
```bash
python -m timescaledb_mcp
```

The server will start and be ready to accept MCP protocol requests via stdio.

### MCP Client Configuration

To use this server with an MCP client (like Claude Desktop), add it to your MCP configuration.

**Option 1: Using the installed console script (recommended):**
```json
{
  "mcpServers": {
    "timescaledb": {
      "command": "timescaledb-mcp",
      "env": {
        "TIMESCALEDB_HOST": "localhost",
        "TIMESCALEDB_PORT": "5432",
        "TIMESCALEDB_DATABASE": "your_database",
        "TIMESCALEDB_USER": "your_user",
        "TIMESCALEDB_PASSWORD": "your_password"
      }
    }
  }
}
```

**Option 2: Using Python module:**
```json
{
  "mcpServers": {
    "timescaledb": {
      "command": "python",
      "args": ["-m", "timescaledb_mcp"],
      "env": {
        "TIMESCALEDB_HOST": "localhost",
        "TIMESCALEDB_PORT": "5432",
        "TIMESCALEDB_DATABASE": "your_database",
        "TIMESCALEDB_USER": "your_user",
        "TIMESCALEDB_PASSWORD": "your_password"
      }
    }
  }
}
```

**Option 3: Using uv (if installed via uv):**
```json
{
  "mcpServers": {
    "timescaledb": {
      "command": "uv",
      "args": ["run", "timescaledb-mcp"],
      "env": {
        "TIMESCALEDB_HOST": "localhost",
        "TIMESCALEDB_PORT": "5432",
        "TIMESCALEDB_DATABASE": "your_database",
        "TIMESCALEDB_USER": "your_user",
        "TIMESCALEDB_PASSWORD": "your_password"
      }
    }
  }
}
```

## MCP Tools

The server provides the following tools:

- **`execute_query`**: Execute a SQL query with parameterized support and return results
- **`list_tables`**: List all tables in the database
- **`describe_table`**: Get detailed information about a table (columns, types, row counts)
- **`list_hypertables`**: List all TimescaleDB hypertables
- **`describe_hypertable`**: Get detailed information about a hypertable (dimensions, chunks, compression)
- **`query_timeseries`**: Query time-series data with optional time-bucketing and aggregation

## MCP Resources

The server exposes database schema as MCP resources:

- **Table Resources**: `timescaledb://table/{table_name}` - Access table schemas and metadata
- **Hypertable Resources**: `timescaledb://hypertable/{hypertable_name}` - Access hypertable schemas and metadata

Resources are automatically discovered and listed, making it easy for AI assistants to explore your database structure.

## MCP Prompts

Pre-built prompts for common operations:

- **`query_timeseries_data`**: Generate queries for time-series data retrieval
- **`analyze_hypertable`**: Analyze hypertable structure, chunks, and performance metrics
- **`explore_database_schema`**: Get an overview of all tables and hypertables in the database

## Development

This project uses the official MCP Python SDK to implement the Model Context Protocol.

### Project Structure

The project follows modern Python packaging standards with a `src-layout`:

```
timescaledb-mcp/
├── src/
│   └── timescaledb_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py          # Configuration management (Pydantic v2)
│       ├── database.py        # Async TimescaleDB client (asyncpg)
│       ├── exceptions.py      # Custom exceptions
│       └── server.py          # MCP server with tools, resources, prompts
├── tests/                      # Pytest test suite
│   ├── conftest.py
│   ├── test_config.py
│   └── test_database.py
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
├── pyproject.toml             # Modern Python package configuration
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Runtime dependencies
├── README.md
└── LICENSE
```

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/brunoprela/timescaledb-mcp.git
   cd timescaledb-mcp
   ```

2. Install in editable mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   # or
   uv pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Run tests with coverage:
   ```bash
   pytest --cov=timescaledb_mcp --cov-report=html
   ```

5. Format code:
   ```bash
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

### Testing

The test suite requires a running TimescaleDB instance. You can use Docker:

```bash
docker run -d --name timescaledb \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  timescale/timescaledb:latest-pg16
```

Then set environment variables:
```bash
export TIMESCALEDB_HOST=localhost
export TIMESCALEDB_PORT=5432
export TIMESCALEDB_DATABASE=postgres
export TIMESCALEDB_USER=postgres
export TIMESCALEDB_PASSWORD=postgres
```

Run tests:
```bash
pytest -v
```

### Code Quality

The project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking
- **Pytest** for testing with async support

All checks run automatically in CI via GitHub Actions.

## Security

- **SQL Injection Prevention**: All queries use parameterized statements
- **Input Validation**: Table and hypertable names are validated
- **Connection Security**: Supports SSL connections (configure via connection string)
- **Error Handling**: Sensitive information is not exposed in error messages

## Performance

- **Async Operations**: Built on `asyncpg` for non-blocking I/O
- **Connection Pooling**: Efficient connection reuse with configurable pool sizes
- **Query Timeouts**: Configurable timeouts to prevent long-running queries
- **Resource Management**: Proper cleanup of connections and resources

## Publishing

The package is automatically published to PyPI via GitHub Actions when you create a GitHub Release. See [.github/SETUP_PUBLISHING.md](.github/SETUP_PUBLISHING.md) for setup instructions.

**Quick setup:**
1. Set up [PyPI Trusted Publishing](https://pypi.org/manage/account/publishing/) (recommended)
   - Or add `PYPI_API_TOKEN` as a GitHub secret
2. Update version in `pyproject.toml`
3. Create a GitHub Release with matching tag (e.g., `v0.1.0`)
4. The workflow will automatically build and publish to PyPI

## License

MIT

