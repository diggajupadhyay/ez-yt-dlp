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
    resolve_yt_dlp,
    prepare_output_dir,
    interactive_mode,
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

    def test_build_command_video_mode(self, tmp_path):
        """Test video mode command."""
        cmd = build_command("video", "https://example.com/v", str(tmp_path))
        assert "yt-dlp" in cmd
        assert "-f" in cmd
        assert "bestvideo+bestaudio" in cmd
        assert "--merge-output-format" in cmd
        assert "mp4" in cmd
        assert "--no-playlist" in cmd

    def test_build_command_audio_mode(self, tmp_path):
        """Test audio mode command."""
        cmd = build_command("audio", "https://example.com/v", str(tmp_path), audio_format="mp3")
        assert "--extract-audio" in cmd
        assert "--audio-format" in cmd
        assert "mp3" in cmd
        assert "--audio-quality" in cmd
        assert "0" in cmd

    def test_build_command_audio_format_m4a(self, tmp_path):
        """Test audio mode with m4a format."""
        cmd = build_command("audio", "https://example.com/v", str(tmp_path), audio_format="m4a")
        assert "--audio-format" in cmd
        idx = cmd.index("--audio-format")
        assert cmd[idx + 1] == "m4a"

    def test_build_command_playlist(self, tmp_path):
        """Test playlist option."""
        cmd = build_command("video", "https://example.com/v", str(tmp_path), playlist=True)
        assert "--yes-playlist" in cmd
        assert "--no-playlist" not in cmd

    def test_build_command_no_playlist(self, tmp_path):
        """Test no playlist option (default)."""
        cmd = build_command("video", "https://example.com/v", str(tmp_path), playlist=False)
        assert "--no-playlist" in cmd
        assert "--yes-playlist" not in cmd

    def test_build_command_extra_opts(self, tmp_path):
        """Test extra options."""
        cmd = build_command(
            "video", "https://example.com/v", str(tmp_path),
            extra_opts=["--rate-limit", "1M"],
        )
        assert "--rate-limit" in cmd
        assert "1M" in cmd

    def test_build_command_invalid_mode(self, tmp_path):
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="mode must be"):
            build_command("invalid", "https://example.com/v", str(tmp_path))

    def test_build_command_output_template(self, tmp_path):
        """Test custom output template."""
        cmd = build_command(
            "video", "https://example.com/v", str(tmp_path),
            output_template="%(title)s-%(id)s.%(ext)s",
        )
        assert "-o" in cmd
        idx = cmd.index("-o")
        assert "%(title)s-%(id)s.%(ext)s" in cmd[idx + 1]

    def test_prepare_output_dir_creates_directory(self, tmp_path):
        """Test that output directory preparation creates the directory."""
        new_dir = os.path.join(tmp_path, "new", "nested", "dir")
        assert not os.path.exists(new_dir)
        assert prepare_output_dir(new_dir) == new_dir
        assert os.path.exists(new_dir)

    def test_build_command_is_side_effect_free(self, tmp_path):
        """Test that command building does not create directories."""
        new_dir = tmp_path / "new"
        cmd = build_command("video", "https://example.com/v", str(new_dir))
        assert not new_dir.exists()
        assert cmd[-2] == str(new_dir / "%(title)s.%(ext)s")

    def test_build_command_uses_resolved_command(self, tmp_path):
        """Test that a resolved yt-dlp command is used."""
        resolved = ["/usr/bin/python", "-m", "yt_dlp"]
        cmd = build_command(
            "video",
            "https://example.com/v",
            str(tmp_path),
            yt_dlp_command=resolved,
        )
        assert cmd[:3] == resolved

    def test_build_command_expands_user_path(self, tmp_path):
        """Test that user paths are expanded."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            cmd = build_command(
                "video",
                "https://example.com/v",
                "~/Videos",
            )
        assert cmd[-2] == str(tmp_path / "Videos" / "%(title)s.%(ext)s")

    def test_prepare_output_dir_reports_directory_error(self, tmp_path):
        """Test that output directory errors are reported."""
        existing_file = tmp_path / "file"
        existing_file.write_text("not a directory")
        with pytest.raises(OSError, match="Unable to create output directory"):
            prepare_output_dir(str(existing_file / "nested"))


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

    def test_run_yt_dlp_dry_run_quotes_arguments(self, capsys):
        """Test dry-run output is safely quoted."""
        cmd = ["yt-dlp", "-o", "/tmp/a b", "https://example.com/v?x=1&y=2"]
        rc = run_yt_dlp(cmd, dry_run=True)
        captured = capsys.readouterr()
        assert rc == 0
        assert "'/tmp/a b'" in captured.out
        assert "'https://example.com/v?x=1&y=2'" in captured.out

    def test_run_yt_dlp_success(self):
        """Test successful execution returns 0."""
        cmd = ["yt-dlp", "--version"]
        with patch("ez_yt_dlp.subprocess.run") as mock_run:
            rc = run_yt_dlp(cmd)
        assert rc == 0
        mock_run.assert_called_once_with(cmd, check=True)

    def test_run_yt_dlp_failure(self, capsys):
        """Test failed execution returns non-zero."""
        cmd = ["yt-dlp", "--version"]
        with patch("ez_yt_dlp.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, cmd)
            rc = run_yt_dlp(cmd)
        assert rc != 0
        captured = capsys.readouterr()
        assert "Download failed" in captured.err or "Download failed" in captured.out

    def test_run_yt_dlp_not_found(self, capsys):
        """Test FileNotFoundError handling."""
        cmd = ["yt-dlp", "--version"]
        with patch("ez_yt_dlp.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError
            rc = run_yt_dlp(cmd)
        assert rc == 2
        captured = capsys.readouterr()
        assert "yt-dlp not found" in captured.out


class TestResolveYtDlp:
    """Tests for yt-dlp command resolution."""

    def test_resolve_yt_dlp_falls_back_to_path_executable(self):
        with patch("ez_yt_dlp.importlib.util.find_spec", return_value=None):
            with patch("ez_yt_dlp.shutil.which", return_value="/usr/bin/yt-dlp"):
                assert resolve_yt_dlp() == ["/usr/bin/yt-dlp"]

    def test_resolve_yt_dlp_uses_python_module(self):
        with patch("ez_yt_dlp.shutil.which", return_value=None):
            with patch("ez_yt_dlp.importlib.util.find_spec", return_value=object()):
                assert resolve_yt_dlp()[1:] == ["-m", "yt_dlp"]

    def test_resolve_yt_dlp_returns_none_when_missing(self):
        with patch("ez_yt_dlp.shutil.which", return_value=None):
            with patch("ez_yt_dlp.importlib.util.find_spec", return_value=None):
                assert resolve_yt_dlp() is None


class TestEnsureYtDlpInstalled:
    """Tests for yt-dlp installation check."""

    def test_ensure_yt_dlp_installed(self):
        """Test when yt-dlp is available."""
        with patch("ez_yt_dlp.resolve_yt_dlp", return_value=["yt-dlp"]):
            assert ensure_yt_dlp_installed(allow_install=False) is True

    def test_ensure_yt_dlp_not_installed_no_install(self):
        """Test when yt-dlp is missing and install is disabled."""
        with patch("ez_yt_dlp.resolve_yt_dlp", return_value=None):
            assert ensure_yt_dlp_installed(allow_install=False) is False

    def test_ensure_yt_dlp_install_success(self):
        """Test successful installation via pip."""
        with patch(
            "ez_yt_dlp.resolve_yt_dlp",
            side_effect=[None, ["/usr/bin/yt-dlp"]],
        ):
            with patch("ez_yt_dlp.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = ensure_yt_dlp_installed(allow_install=True)
        assert result is True

    def test_ensure_yt_dlp_install_failure(self, capsys):
        """Test failed installation via pip."""
        with patch("ez_yt_dlp.resolve_yt_dlp", return_value=None):
            with patch("ez_yt_dlp.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, ["pip"])
                result = ensure_yt_dlp_installed(allow_install=True)
        assert result is False
        captured = capsys.readouterr()
        assert "Failed to install" in captured.out

    def test_ensure_yt_dlp_install_oserror(self, capsys):
        """Test pip execution errors are handled."""
        with patch("ez_yt_dlp.resolve_yt_dlp", return_value=None):
            with patch("ez_yt_dlp.subprocess.run", side_effect=OSError):
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
            mock_interactive.assert_called_once_with(
                allow_install=True,
                dry_run=False,
            )

    def test_main_no_url_dry_run(self):
        """Test dry-run is passed to interactive mode."""
        with patch("ez_yt_dlp.interactive_mode", return_value=0) as mock_interactive:
            rc = main(["--dry-run"])
        assert rc == 0
        mock_interactive.assert_called_once_with(
            allow_install=True,
            dry_run=True,
        )

    def test_main_with_url_no_yt_dlp(self, capsys):
        """Test with URL but yt-dlp not installed."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=False):
            rc = main(["https://example.com/v"])
            assert rc == 2

    def test_main_dry_run(self, capsys, tmp_path):
        """Test dry-run mode."""
        output_dir = tmp_path / "dry-run"
        with patch("ez_yt_dlp.ensure_yt_dlp_installed") as mock_ensure:
            rc = main([
                "--dry-run",
                "--output", str(output_dir),
                "https://example.com/v",
            ])
        assert rc == 0
        captured = capsys.readouterr()
        assert "DRY-RUN:" in captured.out
        assert not output_dir.exists()
        mock_ensure.assert_not_called()

    def test_main_reports_output_directory_error(self, capsys, tmp_path):
        """Test output directory errors return a useful message."""
        existing_file = tmp_path / "file"
        existing_file.write_text("not a directory")
        with patch("ez_yt_dlp.ensure_yt_dlp_installed", return_value=True):
            rc = main([
                "--output", str(existing_file / "nested"),
                "https://example.com/v",
            ])
        assert rc == 1
        captured = capsys.readouterr()
        assert "Unable to create output directory" in captured.out

    def test_main_audio_mode(self, capsys, tmp_path):
        """Test audio mode."""
        output_dir = tmp_path / "audio"
        rc = main([
            "--audio",
            "--dry-run",
            "--output", str(output_dir),
            "https://example.com/v",
        ])
        assert rc == 0
        captured = capsys.readouterr()
        assert "--extract-audio" in captured.out

    def test_main_playlist_mode(self, capsys, tmp_path):
        """Test playlist mode."""
        output_dir = tmp_path / "playlist"
        rc = main([
            "--playlist",
            "--dry-run",
            "--output", str(output_dir),
            "https://example.com/v",
        ])
        assert rc == 0
        captured = capsys.readouterr()
        assert "--yes-playlist" in captured.out


class TestInteractiveMode:
    """Tests for interactive mode."""

    def test_interactive_mode_dry_run(self, tmp_path, capsys):
        """Test interactive dry-run avoids setup and directory creation."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            with patch("ez_yt_dlp.ensure_yt_dlp_installed") as mock_ensure:
                with patch(
                    "ez_yt_dlp.input",
                    side_effect=["v", "https://example.com/v", "~/Videos", "q"],
                ):
                    rc = interactive_mode(dry_run=True)
        assert rc == 0
        mock_ensure.assert_not_called()
        captured = capsys.readouterr()
        assert "DRY-RUN:" in captured.out
        assert "Dry-run complete. No files were downloaded." in captured.out
        assert not (tmp_path / "Videos").exists()

    def test_interactive_mode_no_yt_dlp(self, capsys):
        """Test interactive mode when yt-dlp is not installed."""
        with patch("ez_yt_dlp.ensure_yt_dlp_installed", return_value=False):
            with patch(
                "ez_yt_dlp.input",
                side_effect=["v", "https://example.com/v", "~/Videos"],
            ):
                rc = interactive_mode(allow_install=False)
        assert rc == 2

    def test_interactive_mode_quit(self, capsys):
        """Test quitting interactive mode."""
        with patch("ez_yt_dlp.ensure_yt_dlp_installed") as mock_ensure:
            with patch("ez_yt_dlp.input", side_effect=["q"]):
                rc = interactive_mode(allow_install=False)
        assert rc == 0
        mock_ensure.assert_not_called()
        captured = capsys.readouterr()
        assert "Quitting" in captured.out

    def test_interactive_mode_invalid_option(self, capsys):
        """Test invalid option in interactive mode."""
        with patch('ez_yt_dlp.ensure_yt_dlp_installed', return_value=True):
            with patch('ez_yt_dlp.input', side_effect=['x', 'q']):
                rc = interactive_mode()
                captured = capsys.readouterr()
                assert "Invalid option" in captured.out

    def test_interactive_mode_expands_output_path(self, tmp_path):
        """Test interactive output paths are expanded."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            with patch("ez_yt_dlp.ensure_yt_dlp_installed", return_value=True):
                with patch(
                    "ez_yt_dlp.input",
                    side_effect=["a", "https://example.com/v", "~/Music", "q"],
                ):
                    with patch("ez_yt_dlp.run_yt_dlp", return_value=0) as mock_run:
                        rc = interactive_mode()
        assert rc == 0
        cmd = mock_run.call_args.args[0]
        assert cmd[-2] == str(tmp_path / "Music" / "%(title)s.%(ext)s")

    def test_interactive_mode_invalid_url(self, capsys):
        """Test invalid URL in interactive mode."""
        with patch("ez_yt_dlp.ensure_yt_dlp_installed", return_value=True):
            with patch("ez_yt_dlp.input", side_effect=["v", "not-a-url", "q"]):
                rc = interactive_mode()
        assert rc == 0
        captured = capsys.readouterr()
        assert "Invalid URL" in captured.out
