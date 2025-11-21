# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added
- Initial release of TimescaleDB MCP Server
- Async database operations using `asyncpg`
- Connection pooling with configurable pool sizes
- 6 MCP tools for database operations:
  - `execute_query`: Execute SQL queries with parameterized support
  - `list_tables`: List all tables in the database
  - `describe_table`: Get detailed table information
  - `list_hypertables`: List all TimescaleDB hypertables
  - `describe_hypertable`: Get detailed hypertable information
  - `query_timeseries`: Query time-series data with time-bucketing
- MCP Resources for schema introspection:
  - Table resources: `timescaledb://table/{table_name}`
  - Hypertable resources: `timescaledb://hypertable/{hypertable_name}`
- MCP Prompts for common operations:
  - `query_timeseries_data`: Generate time-series queries
  - `analyze_hypertable`: Analyze hypertable structure and performance
  - `explore_database_schema`: Explore database schema overview
- Comprehensive error handling with custom exceptions
- Full type hints and type safety
- SQL injection prevention via parameterized queries
- Structured logging
- Pytest test suite with async support
- GitHub Actions CI/CD workflow
- Modern Python packaging with `src-layout` and `pyproject.toml`
- Support for both `pip` and `uv` package managers

### Security
- Parameterized queries throughout to prevent SQL injection
- Input validation for table and hypertable names
- Secure error handling that doesn't expose sensitive information

### Performance
- Async I/O operations for high performance
- Connection pooling for efficient resource usage
- Configurable query timeouts

