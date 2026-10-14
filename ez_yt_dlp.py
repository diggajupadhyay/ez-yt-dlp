#!/usr/bin/env python3
"""ez_yt_dlp - small, focused helper around yt-dlp

This module provides a small, testable wrapper around the external
`yt-dlp` tool.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
from typing import List, Optional

__version__ = "0.2.3"


def _print_error(message: str) -> None:
    print(message, file=sys.stderr)


def resolve_yt_dlp() -> Optional[List[str]]:
    """Return the available yt-dlp command for the current environment."""
    if importlib.util.find_spec("yt_dlp") is not None:
        return [sys.executable, "-m", "yt_dlp"]

    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]

    return None


def ensure_yt_dlp_installed(allow_install: bool = True) -> bool:
    """Check if yt-dlp is installed, optionally attempt to install it."""
    if resolve_yt_dlp() is not None:
        return True

    if not allow_install:
        _print_error("yt-dlp not found. Install it manually:")
        _print_error(f"  {sys.executable} -m pip install --user yt-dlp")
        return False

    _print_error("yt-dlp not found. Attempting to install via pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "yt-dlp"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        _print_error(f"Failed to install yt-dlp: {e}")
        details = e.stderr or e.stdout or ""
        if isinstance(details, bytes):
            details = details.decode(errors="replace")
        for line in details.strip().splitlines()[-5:]:
            _print_error(f"  {line}")
        return False
    except OSError as e:
        _print_error(f"Failed to install yt-dlp: {e}")
        return False

    if resolve_yt_dlp() is None:
        _print_error("yt-dlp installation failed. Please install manually:")
        _print_error(f"  {sys.executable} -m pip install --user yt-dlp")
        return False

    return True


def prepare_output_dir(save_dir: str) -> str:
    """Expand and create the output directory."""
    save_dir = os.path.expanduser(save_dir)
    try:
        os.makedirs(save_dir, exist_ok=True)
    except OSError as e:
        raise OSError(
            f"Unable to create output directory {save_dir!r}: {e}"
        ) from e
    return save_dir


def build_command(
    mode: str,
    url: str,
    save_dir: str,
    audio_format: str = "mp3",
    playlist: bool = False,
    output_template: str = "%(title)s.%(ext)s",
    extra_opts: Optional[List[str]] = None,
    yt_dlp_command: Optional[List[str]] = None,
) -> List[str]:
    """Build yt-dlp command line for the given options."""
    if mode not in ("video", "audio"):
        raise ValueError("mode must be 'video' or 'audio'")

    save_dir = os.path.expanduser(save_dir)
    opts: List[str] = []

    if mode == "video":
        opts += ["-f", "bestvideo+bestaudio", "--merge-output-format", "mp4"]
    else:  # audio
        opts += [
            "--extract-audio",
            "--audio-format", audio_format,
            "--audio-quality", "0",
        ]

    if playlist:
        opts += ["--yes-playlist"]
    else:
        opts += ["--no-playlist"]

    if extra_opts:
        opts += extra_opts

    output_path = os.path.join(save_dir, output_template)
    command = list(yt_dlp_command or ["yt-dlp"])
    return command + opts + ["-o", output_path, url]


def run_yt_dlp(cmd: List[str], dry_run: bool = False) -> int:
    """Execute yt-dlp command. Returns 0 on success, non-zero on failure."""
    if dry_run:
        print("DRY-RUN:", shlex.join(cmd))
        return 0

    try:
        subprocess.run(cmd, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        _print_error(f"Download failed: {e}")
        return 1
    except FileNotFoundError:
        _print_error("Error: yt-dlp not found. Please install it:")
        _print_error(f"  {sys.executable} -m pip install --user yt-dlp")
        return 2
    except KeyboardInterrupt:
        _print_error("\nDownload cancelled by user.")
        return 130


def interactive_mode(allow_install: bool = True, dry_run: bool = False) -> int:
    """Run interactive mode with prompts."""
    try:
        return _interactive_loop(allow_install, dry_run)
    except (EOFError, KeyboardInterrupt):
        _print_error("\nCancelled.")
        return 130


def _interactive_loop(allow_install: bool, dry_run: bool) -> int:
    yt_dlp_command: Optional[List[str]] = None

    while True:
        print("""
Please choose Media Download Option:

      v  - Download Single Video
      vp - Download Video Playlist
      a  - Download Single Audio
      ap - Download Audio Playlist
      q  - Quit
""")

        option = input("Enter your choice (v, vp, a, ap, q): ").strip().lower()
        if option == "q":
            print("Quitting...")
            return 0

        if option not in ("v", "vp", "a", "ap"):
            print("Invalid option. Please try again.")
            continue

        url = input("Enter the YouTube/Facebook/Odysee URL: ").strip()
        if not url.startswith(("http://", "https://")):
            print("Invalid URL. Please enter a valid URL starting with http:// or https://")
            continue

        save_dir = os.path.expanduser(
            input(f"Enter Save directory [$HOME/Videos]: ").strip() or "~/Videos"
        )

        if option in ("v", "vp"):
            mode = "video"
        else:
            mode = "audio"

        playlist = option in ("vp", "ap")
        if yt_dlp_command is None:
            if not dry_run and not ensure_yt_dlp_installed(allow_install=allow_install):
                return 2
            yt_dlp_command = resolve_yt_dlp() or ["yt-dlp"]

        try:
            if not dry_run:
                save_dir = prepare_output_dir(save_dir)
            cmd = build_command(
                mode,
                url,
                save_dir,
                playlist=playlist,
                yt_dlp_command=yt_dlp_command,
            )
        except OSError as e:
            _print_error(f"Error: {e}")
            continue

        rc = run_yt_dlp(cmd, dry_run=dry_run)
        if rc == 0:
            if dry_run:
                print("Dry-run complete. No files were downloaded.")
            else:
                print(f"Finished. Files saved to {save_dir}")
        elif rc == 130:
            # User cancelled, return to menu
            continue
        else:
            _print_error("Download failed. Please check your URL and try again.")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    p = argparse.ArgumentParser(
        prog="ez-yt-dlp",
        description="Small wrapper around yt-dlp for common downloads.",
    )
    p.add_argument(
        "url",
        nargs="?",
        help="URL to download (if omitted, interactive mode is started)",
    )
    group = p.add_mutually_exclusive_group()
    group.add_argument(
        "--video", "-v",
        action="store_true",
        help="Download video (default)",
    )
    group.add_argument(
        "--audio", "-a",
        action="store_true",
        help="Extract audio",
    )
    p.add_argument(
        "--playlist", "-p",
        action="store_true",
        help="Allow playlists (if omitted single item is assumed)",
    )
    p.add_argument(
        "--output", "-o",
        default=os.path.expanduser("~/Videos"),
        help="Save directory (default: $HOME/Videos)",
    )
    p.add_argument(
        "--format", "-f",
        default=None,
        help="Audio format when extracting audio (e.g. mp3, m4a). Only valid with --audio",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command instead of executing it",
    )
    p.add_argument(
        "--no-install",
        action="store_true",
        help="Do not attempt to auto-install yt-dlp if missing",
    )
    p.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    args = parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    # Validate --format is only used with --audio
    if args.format and not args.audio:
        _print_error("Error: --format is only valid with --audio")
        return 1

    if not args.url:
        return interactive_mode(
            allow_install=not args.no_install,
            dry_run=args.dry_run,
        )

    mode = "audio" if args.audio else "video"
    playlist = bool(args.playlist)
    audio_fmt = args.format if args.format else "mp3"

    if not args.dry_run and not ensure_yt_dlp_installed(allow_install=not args.no_install):
        return 2

    yt_dlp_command = resolve_yt_dlp() or ["yt-dlp"]
    save_dir = args.output
    try:
        if not args.dry_run:
            save_dir = prepare_output_dir(save_dir)
        cmd = build_command(
            mode,
            args.url,
            save_dir,
            audio_format=audio_fmt,
            playlist=playlist,
            yt_dlp_command=yt_dlp_command,
        )
    except OSError as e:
        _print_error(f"Error: {e}")
        return 1

    return run_yt_dlp(cmd, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
