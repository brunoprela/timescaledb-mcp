#!/bin/bash
# Script to publish timescaledb-mcp to PyPI

set -e

echo "🚀 Publishing timescaledb-mcp to PyPI"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Run this script from the project root."
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Install build tools if not already installed
echo "📦 Installing build tools..."
python -m pip install --upgrade build twine

# Build the package
echo "🔨 Building package..."
python -m build

# Check the package
echo "✅ Checking package..."
twine check dist/*

# Ask if user wants to publish to TestPyPI first
read -p "📤 Publish to TestPyPI first? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
    echo "✅ Published to TestPyPI!"
    echo "🧪 Test installation with: pip install --index-url https://test.pypi.org/simple/ timescaledb-mcp"
    read -p "📤 Continue to production PyPI? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "⏸️  Skipping production PyPI upload"
        exit 0
    fi
fi

# Publish to production PyPI
echo "📤 Uploading to PyPI..."
twine upload dist/*

echo "✅ Successfully published to PyPI!"
echo "🌐 View at: https://pypi.org/project/timescaledb-mcp/"

