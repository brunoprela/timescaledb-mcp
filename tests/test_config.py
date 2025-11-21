"""Tests for configuration management."""

import os
import pytest
from timescaledb_mcp.config import TimescaleDBConfig, get_config


def test_default_config():
    """Test default configuration values."""
    config = TimescaleDBConfig()
    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "postgres"
    assert config.user == "postgres"
    assert config.min_pool_size == 1
    assert config.max_pool_size == 10


def test_config_from_env(monkeypatch):
    """Test configuration loading from environment variables."""
    monkeypatch.setenv("TIMESCALEDB_HOST", "testhost")
    monkeypatch.setenv("TIMESCALEDB_PORT", "5433")
    monkeypatch.setenv("TIMESCALEDB_DATABASE", "testdb")
    monkeypatch.setenv("TIMESCALEDB_USER", "testuser")
    monkeypatch.setenv("TIMESCALEDB_PASSWORD", "testpass")
    
    config = get_config()
    assert config.host == "testhost"
    assert config.port == 5433
    assert config.database == "testdb"
    assert config.user == "testuser"
    assert config.password == "testpass"

