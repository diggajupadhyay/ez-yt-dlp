#!/bin/bash
# Release script for ez-yt-dlp
# Usage: ./release.sh

set -e

echo "=== ez-yt-dlp Release Script ==="
echo ""

# Check if version is set
VERSION=$(grep '^version = ' pyproject.toml | head -1 | cut -d'"' -f2)
echo "Current version: $VERSION"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/
echo ""

# Build package
echo "Building package..."
.venv/bin/python -m build
echo ""

# Show built files
echo "Built files:"
ls -lh dist/
echo ""

# Upload to PyPI
echo "Upload to PyPI? (y/n)"
read -r upload
if [[ "$upload" =~ ^[Yy]$ ]]; then
    echo "Uploading to PyPI..."
    .venv/bin/twine upload dist/*
    echo ""
    echo "✓ Uploaded to PyPI: https://pypi.org/project/ez-yt-dlp/$VERSION"
fi

echo ""
echo "Done!"
