# Publishing to PyPI

This guide explains how to publish `timescaledb-mcp` to the Python Package Index (PyPI).

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/account/register/)
2. **TestPyPI Account** (recommended): Create an account at [test.pypi.org](https://test.pypi.org/account/register/)
3. **API Token**: Generate an API token at [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)

## Step 1: Update Version

Before publishing, update the version in `pyproject.toml`:

```toml
[project]
version = "0.1.0"  # Update this
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

## Step 2: Prepare the Package

### Install Build Tools

```bash
pip install build twine
# or
uv pip install build twine
```

### Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### Build Distribution Files

```bash
python -m build
```

This creates:
- `dist/timescaledb-mcp-0.1.0.tar.gz` (source distribution)
- `dist/timescaledb_mcp-0.1.0-py3-none-any.whl` (wheel distribution)

### Verify the Build

```bash
twine check dist/*
```

This validates your package files.

## Step 3: Test on TestPyPI (Recommended)

Before publishing to production PyPI, test on TestPyPI:

### Upload to TestPyPI

```bash
twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-`)

### Test Installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ timescaledb-mcp
```

Or using `uv`:

```bash
uv pip install --index-url https://test.pypi.org/simple/ timescaledb-mcp
```

### Verify It Works

```bash
timescaledb-mcp --help
```

## Step 4: Publish to Production PyPI

Once tested on TestPyPI, publish to production:

### Upload to PyPI

```bash
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

### Verify on PyPI

Visit: https://pypi.org/project/timescaledb-mcp/

### Test Installation

```bash
pip install timescaledb-mcp
# or
uv pip install timescaledb-mcp
```

## Step 5: Create a Git Tag

After successful publication, create a git tag:

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

## Automated Publishing with GitHub Actions

You can automate publishing using GitHub Actions. See `.github/workflows/publish.yml` (if created).

### Setup Secrets

In your GitHub repository, add these secrets:
- `PYPI_API_TOKEN`: Your PyPI API token
- `TEST_PYPI_API_TOKEN`: Your TestPyPI API token (optional)

## Troubleshooting

### "Package already exists"

If the version already exists on PyPI, you must:
1. Update the version number in `pyproject.toml`
2. Rebuild and upload

### "Invalid distribution"

Run `twine check dist/*` to see specific errors.

### Authentication Issues

- Make sure you're using `__token__` as the username
- Use the full API token (including `pypi-` prefix) as the password
- For TestPyPI, use a TestPyPI-specific token

## Best Practices

1. **Always test on TestPyPI first**
2. **Update CHANGELOG.md** before each release
3. **Create a GitHub release** after publishing
4. **Use API tokens** instead of passwords
5. **Keep version numbers in sync** between git tags and PyPI

## Quick Reference

```bash
# Full publishing workflow
python -m build
twine check dist/*
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*  # Production
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

