# Release Guide

## Publishing to PyPI

### Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. API token from PyPI (Account Settings → API tokens → Add API token)

### Release Steps

1. **Bump version** in `pyproject.toml`:
   ```toml
   version = "0.3.0"  # Increment version
   ```

2. **Run release script**:
   ```bash
   ./release.sh
   ```

3. **Or manual build/upload**:
   ```bash
   # Clean
   rm -rf dist/ build/ *.egg-info/

   # Build
   .venv/bin/python -m build

   # Upload to PyPI
   .venv/bin/twine upload dist/*
   ```

4. **Verify on PyPI**: https://pypi.org/project/ez-yt-dlp/

### Delete from TestPyPI (Cleanup)

TestPyPI doesn't have an API for deletion. To remove your test upload:

1. Go to https://test.pypi.org/manage/projects/
2. Find `ez-yt-dlp` in your projects
3. Click "Settings" tab
4. Scroll down and click "Delete this project"
5. Confirm deletion

**Note**: If you can't delete (project has downloads), you can:
- Abandon the TestPyPI project (it won't affect PyPI)
- Use a different project name for testing next time (e.g., `ez-yt-dlp-test`)

### Local Testing Before Release

```bash
# Build
.venv/bin/python -m build

# Install locally to test
.venv/bin/pip install .

# Test the CLI
.venv/bin/ez-yt-dlp --version
.venv/bin/ez-yt-dlp --help
```
