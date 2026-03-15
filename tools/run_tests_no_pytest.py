#!/usr/bin/env python3
"""Lightweight test runner to validate core behaviors without pytest.

This script runs a few simple checks equivalent to the pytest tests
added to `tests/test_cli.py`. It intentionally avoids external
dependencies so it can run in minimal environments.
"""
import io
import os
import sys
from contextlib import redirect_stdout

# Ensure project root is on sys.path so we can import the top-level module
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ez_yt_dlp import parse_args, build_command, run_yt_dlp


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(2)


def ok(msg: str) -> None:
    print("OK:", msg)


def test_parse_args_defaults():
    ns = parse_args(["https://example.com/watch?v=abc123"])
    assert ns.url == "https://example.com/watch?v=abc123"
    assert not ns.audio
    assert not ns.playlist
    ok("parse_args defaults")


def test_build_command_audio():
    cmd = build_command("audio", "https://example.com/v", "/tmp", audio_format="mp3", playlist=False)
    if "--extract-audio" not in cmd or "--audio-format" not in cmd:
        fail("build_command audio missing expected flags")
    ok("build_command audio")


def test_run_yt_dlp_dry_run():
    cmd = ["yt-dlp", "--version"]
    f = io.StringIO()
    with redirect_stdout(f):
        rc = run_yt_dlp(cmd, dry_run=True)
    out = f.getvalue()
    if rc != 0:
        fail("run_yt_dlp dry-run returned non-zero")
    if "DRY-RUN:" not in out:
        fail("run_yt_dlp dry-run did not print expected output")
    ok("run_yt_dlp dry-run")


def main():
    try:
        test_parse_args_defaults()
        test_build_command_audio()
        test_run_yt_dlp_dry_run()
    except AssertionError as e:
        fail(f"AssertionError: {e}")

    print("All checks passed")


if __name__ == "__main__":
    main()
