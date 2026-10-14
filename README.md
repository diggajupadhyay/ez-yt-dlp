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

### From PyPI

```bash
python3 -m pip install --user ez-yt-dlp
ez-yt-dlp --help
```

### From source

```bash
# Install yt-dlp for direct use
python3 -m pip install --user -r requirements.txt

# Run directly
python3 ez_yt_dlp.py --help

# Or install as a package
python3 -m pip install --user .
```

Installing the package provides the `ez-yt-dlp` command.

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

### Interactive mode keys

- `v` / `vp` — download a video or video playlist
- `a` / `ap` — extract audio from a track or playlist
- `q` — quit

### Exit codes

- `0` — success or user quit
- `1` — invalid arguments or output path
- `2` — yt-dlp is unavailable
- `130` — cancelled by the user

### Options

```text
usage: ez-yt-dlp [-h] [--video | --audio] [--playlist] [--output OUTPUT]
                 [--format FORMAT] [--dry-run] [--no-install] [--version]
                 [url]

positional arguments:
  url                  URL to download (if omitted, interactive mode is
                       started)

options:
  -h, --help           show this help message and exit
  --video, -v          Download video (default)
  --audio, -a          Extract audio
  --playlist, -p       Allow playlists (if omitted single item is assumed)
  --output, -o OUTPUT  Save directory (default: $HOME/Videos)
  --format, -f FORMAT  Audio format when extracting audio (e.g. mp3, m4a).
                       Only valid with --audio
  --dry-run            Print the command instead of executing it
  --no-install         Do not attempt to auto-install yt-dlp if missing
  --version            Print version and exit
```

## Development

### Run tests

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -v
# or without pytest
python3 tools/run_tests_no_pytest.py
```

### Project structure

```
ez-yt-dlp/
├── ez_yt_dlp.py             # Main module
├── bin/ez-yt-dlp            # Checkout launcher
├── tests/test_cli.py        # Test suite
├── tools/                   # Lightweight test runner
├── .github/workflows/       # CI
├── pyproject.toml           # Package config
├── release.sh               # Release automation
├── RELEASE.md               # Release guide
└── README.md                # This file
```

## Requirements

- Python 3.10+
- yt-dlp
- ffmpeg and ffprobe for video merging and audio extraction

## Release (for maintainers)

```bash
# 1. Bump version in pyproject.toml and ez_yt_dlp.py

# 2. Run release script
./release.sh

# 3. Follow prompts to build and upload to PyPI
```

Requires: `python3 -m pip install -e ".[dev]"`. Set `PYTHON_BIN` to override the release interpreter.

## License

MIT
