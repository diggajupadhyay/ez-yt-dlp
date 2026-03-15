"""Tests for ez_yt_dlp module."""
import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from ez_yt_dlp import (
    parse_args,
    build_command,
    run_yt_dlp,
    ensure_yt_dlp_installed,
    main,
    __version__,
)


class TestParseArgs:
    """Tests for argument parsing."""

    def test_parse_args_defaults(self):
        """Test default argument values."""
        ns = parse_args(["https://example.com/watch?v=abc123"])
        assert ns.url == "https://example.com/watch?v=abc123"
        assert ns.video is False
        assert ns.audio is False
        assert ns.playlist is False
        assert ns.dry_run is False
        assert ns.no_install is False

    def test_parse_args_audio_flag(self):
        """Test --audio flag."""
        ns = parse_args(["--audio", "https://example.com/v"])
        assert ns.audio is True
        assert ns.video is False

    def test_parse_args_video_flag(self):
        """Test --video flag."""
        ns = parse_args(["--video", "https://example.com/v"])
        assert ns.video is True
        assert ns.audio is False

    def test_parse_args_playlist_flag(self):
        """Test --playlist flag."""
        ns = parse_args(["--playlist", "https://example.com/v"])
        assert ns.playlist is True

    def test_parse_args_output_dir(self):
        """Test --output flag."""
        ns = parse_args(["--output", "/custom/dir", "https://example.com/v"])
        assert ns.output == "/custom/dir"

    def test_parse_args_format(self):
        """Test --format flag."""
        ns = parse_args(["--format", "m4a", "--audio", "https://example.com/v"])
        assert ns.format == "m4a"

    def test_parse_args_dry_run(self):
        """Test --dry-run flag."""
        ns = parse_args(["--dry-run", "https://example.com/v"])
        assert ns.dry_run is True

    def test_parse_args_no_install(self):
        """Test --no-install flag."""
        ns = parse_args(["--no-install", "https://example.com/v"])
        assert ns.no_install is True

    def test_parse_args_version(self):
        """Test --version flag."""
        ns = parse_args(["--version"])
        assert ns.version is True

    def test_parse_args_no_url_interactive(self):
        """Test no URL triggers interactive mode."""
        ns = parse_args([])
        assert ns.url is None

    def test_parse_args_mutually_exclusive_video_audio(self):
        """Test that --video and --audio are mutually exclusive."""
        with pytest.raises(SystemExit):
            parse_args(["--video", "--audio", "https://example.com/v"])


class TestBuildCommand:
    """Tests for command building."""

    def test_build_command_video_mode(self):
        """Test video mode command."""
        cmd = build_command("video", "https://example.com/v", "/tmp")
        assert "yt-dlp" in cmd
        assert "-f" in cmd
        assert "bestvideo+bestaudio" in cmd
        assert "--merge-output-format" in cmd
        assert "mp4" in cmd
        assert "--no-playlist" in cmd

    def test_build_command_audio_mode(self):
        """Test audio mode command."""
        cmd = build_command("audio", "https://example.com/v", "/tmp", audio_format="mp3")
        assert "--extract-audio" in cmd
        assert "--audio-format" in cmd
        assert "mp3" in cmd
        assert "--audio-quality" in cmd
        assert "0" in cmd

    def test_build_command_audio_format_m4a(self):
        """Test audio mode with m4a format."""
        cmd = build_command("audio", "https://example.com/v", "/tmp", audio_format="m4a")
        assert "--audio-format" in cmd
        idx = cmd.index("--audio-format")
        assert cmd[idx + 1] == "m4a"

    def test_build_command_playlist(self):
        """Test playlist option."""
        cmd = build_command("video", "https://example.com/v", "/tmp", playlist=True)
        assert "--yes-playlist" in cmd
        assert "--no-playlist" not in cmd

    def test_build_command_no_playlist(self):
        """Test no playlist option (default)."""
        cmd = build_command("video", "https://example.com/v", "/tmp", playlist=False)
        assert "--no-playlist" in cmd
        assert "--yes-playlist" not in cmd

    def test_build_command_extra_opts(self):
        """Test extra options."""
        cmd = build_command(
            "video", "https://example.com/v", "/tmp",
            extra_opts=["--rate-limit", "1M"],
        )
        assert "--rate-limit" in cmd
        assert "1M" in cmd

    def test_build_command_invalid_mode(self):
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="mode must be"):
            build_command("invalid", "https://example.com/v", "/tmp")

    def test_build_command_output_template(self):
        """Test custom output template."""
        cmd = build_command(
            "video", "https://example.com/v", "/tmp",
            output_template="%(title)s-%(id)s.%(ext)s",
        )
        assert "-o" in cmd
        idx = cmd.index("-o")
        assert "%(title)s-%(id)s.%(ext)s" in cmd[idx + 1]

    def test_build_command_creates_directory(self):
        """Test that build_command creates the save directory."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new", "nested", "dir")
            assert not os.path.exists(new_dir)
            build_command("video", "https://example.com/v", new_dir)
            assert os.path.exists(new_dir)


class TestRunYtDlp:
    """Tests for command execution."""

    def test_run_yt_dlp_dry_run(self, capsys):
        """Test dry-run prints command and returns 0."""
        cmd = ["yt-dlp", "--version"]
        rc = run_yt_dlp(cmd, dry_run=True)
        captured = capsys.readouterr()
        assert rc == 0
        assert "DRY-RUN:" in captured.out
        assert "yt-dlp" in captured.out

    def test_run_yt_dlp_success(self):
        """Test successful execution returns 0."""
        cmd = ["echo", "test"]
        rc = run_yt_dlp(cmd)
        assert rc == 0

    def test_run_yt_dlp_failure(self, capsys):
        """Test failed execution returns non-zero."""
        cmd = ["false"]  # Command that always fails
        rc = run_yt_dlp(cmd)
        assert rc != 0
        captured = capsys.readouterr()
        assert "Download failed" in captured.err or "Download failed" in captured.out

    def test_run_yt_dlp_not_found(self, capsys):
        """Test FileNotFoundError handling."""
        cmd = ["nonexistent_command_xyz"]
        rc = run_yt_dlp(cmd)
        assert rc == 2
        captured = capsys.readouterr()
        assert "yt-dlp not found" in captured.out


class TestEnsureYtDlpInstalled:
    """Tests for yt-dlp installation check."""

    def test_ensure_yt_dlp_installed_with_shutil(self):
        """Test when yt-dlp is already in PATH."""
        with patch('ez_yt_dlp.shutil.which', return_value='/usr/bin/yt-dlp'):
            result = ensure_yt_dlp_installed(allow_install=False)
            assert result is True

    def test_ensure_yt_dlp_not_installed_no_install(self):
        """Test when yt-dlp is missing and install is disabled."""
        with patch('ez_yt_dlp.shutil.which', return_value=None):
            result = ensure_yt_dlp_installed(allow_install=False)
            assert result is False

    def test_ensure_yt_dlp_install_success(self):
        """Test successful installation via pip."""
        with patch('ez_yt_dlp.shutil.which') as mock_which:
            mock_which.side_effect = [None, '/usr/bin/yt-dlp']  # First call: not found, second: found
            with patch('ez_yt_dlp.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = ensure_yt_dlp_installed(allow_install=True)
                assert result is True

    def test_ensure_yt_dlp_install_failure(self, capsys):
        """Test failed installation via pip."""
        with patch('ez_yt_dlp.shutil.which', return_value=None):
            with patch('ez_yt_dlp.subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, ['pip'])
                result = ensure_yt_dlp_installed(allow_install=True)
                assert result is False
                captured = capsys.readouterr()
                assert "Failed to install" in captured.out


class TestMain:
    """Tests for main entry point."""

    def test_main_version(self, capsys):
        """Test --version flag."""
        rc = main(["--version"])
        captured = capsys.readouterr()
        assert rc == 0
        assert __version__ in captured.out

    def test_main_format_without_audio(self, capsys):
        """Test --format without --audio shows error."""
        rc = main(["--format", "mp3", "https://example.com/v"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "--format is only valid with --audio" in captured.out

    def test_main_no_url_interactive(self):
        """Test no URL starts interactive mode."""
        with patch('ez_yt_dlp.interactive_mode') as mock_interactive:
            mock_interactive.return_value = 0
            rc = main([])
            assert rc == 0
            mock_interactive.assert_called_once()

    def test_main_with_url_no_yt_dlp(self, capsys):
        """Test with URL but yt-dlp not installed."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=False):
            rc = main(["https://example.com/v"])
            assert rc == 2

    def test_main_dry_run(self, capsys):
        """Test dry-run mode."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=True):
            rc = main(["--dry-run", "https://example.com/v"])
            assert rc == 0
            captured = capsys.readouterr()
            assert "DRY-RUN:" in captured.out

    def test_main_audio_mode(self, capsys):
        """Test audio mode."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=True):
            rc = main(["--audio", "--dry-run", "https://example.com/v"])
            assert rc == 0
            captured = capsys.readouterr()
            assert "--extract-audio" in captured.out

    def test_main_playlist_mode(self, capsys):
        """Test playlist mode."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=True):
            rc = main(["--playlist", "--dry-run", "https://example.com/v"])
            assert rc == 0
            captured = capsys.readouterr()
            assert "--yes-playlist" in captured.out


class TestInteractiveMode:
    """Tests for interactive mode."""

    def test_interactive_mode_no_yt_dlp(self, capsys):
        """Test interactive mode when yt-dlp is not installed."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=False):
            rc = interactive_mode(allow_install=False)
            assert rc == 2

    def test_interactive_mode_quit(self, capsys):
        """Test quitting interactive mode."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=True):
            with patch('ez_yt_dlp.input', side_effect=['q']):
                rc = interactive_mode()
                assert rc == 0
                captured = capsys.readouterr()
                assert "Quitting" in captured.out

    def test_interactive_mode_invalid_option(self, capsys):
        """Test invalid option in interactive mode."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=True):
            with patch('ez_yt_dlp.input', side_effect=['x', 'q']):
                rc = interactive_mode()
                captured = capsys.readouterr()
                assert "Invalid option" in captured.out

    def test_interactive_mode_invalid_url(self, capsys):
        """Test invalid URL in interactive mode."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=True):
            with patch('ez_yt_dlp.input', side_effect=['v', 'not-a-url', 'v', 'https://example.com/v', '~/Videos', 'q']):
                rc = interactive_mode()
                captured = capsys.readouterr()
                assert "Invalid URL" in captured.out
