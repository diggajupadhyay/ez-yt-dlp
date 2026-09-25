#!/bin/bash
# Release script for ez-yt-dlp
# Usage: ./release.sh

set -e

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

echo "=== ez-yt-dlp Release Script ==="
echo ""

# Check if version is set
VERSION=$(grep '^version = ' pyproject.toml | head -1 | cut -d'"' -f2)
echo "Current version: $VERSION"
if ! grep -q "^__version__ = \"$VERSION\"" ez_yt_dlp.py; then
    echo "Version mismatch between pyproject.toml and ez_yt_dlp.py"
    exit 1
fi
echo ""

echo "Running tests..."
"$PYTHON_BIN" -m pytest
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/
echo ""

# Build package
echo "Building package..."
"$PYTHON_BIN" -m build
echo ""

# Show built files
echo "Built files:"
ls -lh dist/
echo ""

echo "Checking package metadata..."
"$PYTHON_BIN" -m twine check dist/*
echo ""

SMOKE_DIR=$(mktemp -d)
trap 'rm -rf "$SMOKE_DIR"' EXIT
"$PYTHON_BIN" -m venv "$SMOKE_DIR/venv"
"$SMOKE_DIR/venv/bin/python" -m pip install --no-index --no-deps dist/*.whl
"$SMOKE_DIR/venv/bin/ez-yt-dlp" --version
"$SMOKE_DIR/venv/bin/ez-yt-dlp" --dry-run --no-install --output "$SMOKE_DIR/output" "https://example.com/v"
test ! -e "$SMOKE_DIR/output"
echo ""

# Upload to PyPI
echo "Upload to PyPI? (y/n)"
read -r upload
if [[ "$upload" =~ ^[Yy]$ ]]; then
    echo "Uploading to PyPI..."
    "$PYTHON_BIN" -m twine upload dist/*
    echo ""
    echo "✓ Uploaded to PyPI: https://pypi.org/project/ez-yt-dlp/$VERSION"
fi

echo ""
echo "Done!"
