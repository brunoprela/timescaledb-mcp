"""Custom exceptions for TimescaleDB MCP Server."""


class TimescaleDBMCPError(Exception):
    """Base exception for TimescaleDB MCP errors."""
    pass


class DatabaseConnectionError(TimescaleDBMCPError):
    """Raised when database connection fails."""
    pass


class QueryExecutionError(TimescaleDBMCPError):
    """Raised when a query execution fails."""
    pass


class ValidationError(TimescaleDBMCPError):
    """Raised when input validation fails."""
    pass


class TableNotFoundError(TimescaleDBMCPError):
    """Raised when a requested table is not found."""
    pass


class HypertableNotFoundError(TimescaleDBMCPError):
    """Raised when a requested hypertable is not found."""
    pass

