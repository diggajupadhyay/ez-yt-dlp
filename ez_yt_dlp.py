#!/usr/bin/env python3
"""ez_yt_dlp - small, focused helper around yt-dlp

This module provides a small, testable wrapper around the external
`yt-dlp` tool.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from typing import List, Optional

__version__ = "0.2.0"


def ensure_yt_dlp_installed(allow_install: bool = True) -> bool:
    """Check if yt-dlp is installed, optionally attempt to install it."""
    exe = shutil.which("yt-dlp")
    if exe:
        return True

    if not allow_install:
        return False

    print("yt-dlp not found. Attempting to install via pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "yt-dlp"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to install yt-dlp: {e}")
        return False

    if shutil.which("yt-dlp") is None:
        print("yt-dlp installation failed. Please install manually:")
        print("  python3 -m pip install --user yt-dlp")
        return False

    return True


def build_command(
    mode: str,
    url: str,
    save_dir: str,
    audio_format: str = "mp3",
    playlist: bool = False,
    output_template: str = "%(title)s.%(ext)s",
    extra_opts: Optional[List[str]] = None,
) -> List[str]:
    """Build yt-dlp command line for the given options."""
    if mode not in ("video", "audio"):
        raise ValueError("mode must be 'video' or 'audio'")

    os.makedirs(save_dir, exist_ok=True)

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
    cmd = ["yt-dlp"] + opts + ["-o", output_path, url]
    return cmd


def run_yt_dlp(cmd: List[str], dry_run: bool = False) -> int:
    """Execute yt-dlp command. Returns 0 on success, non-zero on failure."""
    if dry_run:
        print("DRY-RUN:", " ".join(cmd))
        return 0

    try:
        subprocess.run(cmd, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e}")
        return 1
    except FileNotFoundError:
        print("Error: yt-dlp not found. Please install it:")
        print("  python3 -m pip install --user yt-dlp")
        return 2
    except KeyboardInterrupt:
        print("\nDownload cancelled by user.")
        return 130


def interactive_mode(allow_install: bool = True) -> int:
    """Run interactive mode with prompts."""
    if not ensure_yt_dlp_installed(allow_install=allow_install):
        return 2

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

        save_dir = input(f"Enter Save directory [$HOME/Videos]: ").strip() or os.path.expanduser("~/Videos")

        if option in ("v", "vp"):
            mode = "video"
        else:
            mode = "audio"

        playlist = option in ("vp", "ap")
        cmd = build_command(mode, url, save_dir, playlist=playlist)

        rc = run_yt_dlp(cmd)
        if rc == 0:
            print(f"Finished. Files saved to {save_dir}")
        elif rc == 130:
            # User cancelled, return to menu
            continue
        else:
            print("Download failed. Please check your URL and try again.")


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
        print("Error: --format is only valid with --audio")
        return 1

    if not args.url:
        return interactive_mode(allow_install=not args.no_install)

    mode = "audio" if args.audio else "video"
    playlist = bool(args.playlist)
    audio_fmt = args.format if args.format else "mp3"

    if not ensure_yt_dlp_installed(allow_install=not args.no_install):
        return 2

    cmd = build_command(mode, args.url, args.output, audio_format=audio_fmt, playlist=playlist)
    return run_yt_dlp(cmd, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        raise SystemExit(130)
