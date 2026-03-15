# ez-yt-dlp

Small, focused wrapper around yt-dlp to make common downloads easier.

This is a single-file Python module that provides a clean CLI for downloading
videos and audio from YouTube and other sites supported by yt-dlp.

## Features

- **Simple CLI** - argparse-based with sensible defaults
- **Interactive mode** - Run without arguments for guided prompts
- **Video/Audio modes** - Download video (mp4) or extract audio (mp3, m4a, etc.)
- **Playlist support** - Download single items or entire playlists
- **Dry-run** - Preview commands before executing
- **Auto-install** - Attempts to install yt-dlp if missing (can be disabled)

## Install

### From source

```bash
# Install dependency (optional if you already have yt-dlp)
python3 -m pip install --user -r requirements.txt

# Run directly
python3 ez_yt_dlp.py --help

# Or install as a package
python3 -m pip install --user .
```

### Make executable (optional)

```bash
chmod +x bin/ez-yt-dlp
cp bin/ez-yt-dlp ~/bin/
```

## Usage

### Interactive mode

```bash
ez-yt-dlp
# or
python3 ez_yt_dlp.py
```

### Command-line mode

```bash
# Download video (default)
ez-yt-dlp "https://www.youtube.com/watch?v=..."

# Download audio (mp3)
ez-yt-dlp --audio "https://www.youtube.com/watch?v=..."

# Download audio playlist as m4a
ez-yt-dlp --audio --format m4a --playlist "https://..."

# Custom output directory
ez-yt-dlp --output ~/Downloads "https://..."

# Dry-run (preview command)
ez-yt-dlp --dry-run --audio "https://..."

# Don't auto-install yt-dlp
ez-yt-dlp --no-install "https://..."
```

### Options

```
positional arguments:
  url                   URL to download (if omitted, interactive mode starts)

optional arguments:
  -h, --help            Show help message
  -v, --video           Download video (default)
  -a, --audio           Extract audio
  -p, --playlist        Download entire playlist
  -o, --output DIR      Save directory (default: ~/Videos)
  -f, --format FMT      Audio format with --audio (e.g., mp3, m4a)
  --dry-run             Print command without executing
  --no-install          Don't auto-install yt-dlp
  --version             Show version and exit
```

## Development

### Run tests

```bash
python3 -m pytest -v
# or without pytest
python3 tools/run_tests_no_pytest.py
```

### Project structure

```
ez-yt-dlp/
├── ez_yt_dlp.py        # Main module
├── bin/ez-yt-dlp       # Executable wrapper
├── tests/test_cli.py   # Test suite
├── pyproject.toml      # Package config
└── README.md           # This file
```

## Requirements

- Python 3.8+
- yt-dlp (auto-installed if missing)

## Release (for maintainers)

```bash
# 1. Bump version in pyproject.toml

# 2. Run release script
./release.sh

# 3. Follow prompts to build and upload to PyPI
```

Requires: `pip install build twine` (handled by `.venv` setup)

## License

MIT
