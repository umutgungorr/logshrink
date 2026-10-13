"""Tests for CLI arguments, options, and full execution."""

import pytest

from logshrink.cli import create_parser, run


def test_cli_parser_defaults():
    parser = create_parser()
    args = parser.parse_args([])

    assert args.files == []
    assert args.follow is False
    assert args.threshold == 2
    assert args.preset == "auto"
    assert args.errors_only is False
    assert args.no_color is False
    assert args.no_stats is False


def test_cli_parser_custom_args():
    parser = create_parser()
    args = parser.parse_args(
        [
            "app.log",
            "-f",
            "-t",
            "5",
            "-p",
            "json",
            "-e",
            "--export",
            "incidents.md",
            "--copy",
            "--no-color",
            "--no-stats",
            "-i",
            "filter1",
            "-i",
            "filter2",
        ]
    )

    assert args.files == ["app.log"]
    assert args.follow is True
    assert args.threshold == 5
    assert args.preset == "json"
    assert args.errors_only is True
    assert args.export == "incidents.md"
    assert args.copy is True
    assert args.no_color is True
    assert args.no_stats is True
    assert args.ignore == ["filter1", "filter2"]


def test_cli_execution_on_file(tmp_path, capsys):
    log_file = tmp_path / "server.log"
    log_file.write_text(
        "2026-10-13 [INFO] GET /health 200\n"
        "2026-10-13 [INFO] GET /health 200\n"
        "2026-10-13 [INFO] GET /health 200\n"
        "2026-10-13 [ERROR] Out of memory crash\n",
        encoding="utf-8",
    )

    exit_code = run([str(log_file), "--no-color"])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "[x3 suppressed]" in captured.out
    assert "INCIDENT" in captured.out
    assert "LogShrink Summary" in captured.err


def test_cli_file_not_found(capsys):
    exit_code = run(["non_existent_file_path.log"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_version_flag():
    parser = create_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["-v"])
    assert exc_info.value.code == 0


def test_cli_summary_flag(tmp_path, monkeypatch):
    summary_file = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    log_file = tmp_path / "test.log"
    log_file.write_text("2026-10-13 [INFO] Health check\n", encoding="utf-8")

    exit_code = run([str(log_file), "--summary"])
    assert exit_code == 0
    assert summary_file.exists()
    content = summary_file.read_text(encoding="utf-8")
    assert "LogShrink Incident & Noise Reduction Report" in content


def test_cli_github_output_env(tmp_path, monkeypatch):
    output_file = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    log_file = tmp_path / "test.log"
    log_file.write_text(
        "2026-10-13 [INFO] ping\n2026-10-13 [INFO] ping\n2026-10-13 [ERROR] failure\n",
        encoding="utf-8",
    )

    exit_code = run([str(log_file)])
    assert exit_code == 0
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "incident-count=" in content
    assert "reduced-percentage=" in content
    assert "suppressed-lines=" in content
    assert "total-lines=3" in content


def test_cli_fail_on_error(tmp_path):
    log_clean = tmp_path / "clean.log"
    log_clean.write_text("2026-10-13 [INFO] all good\n", encoding="utf-8")

    log_err = tmp_path / "error.log"
    log_err.write_text("2026-10-13 [ERROR] disaster\n", encoding="utf-8")

    # Clean log should return 0 with or without --fail-on-error
    assert run([str(log_clean), "--fail-on-error"]) == 0

    # Error log returns 0 without --fail-on-error
    assert run([str(log_err)]) == 0

    # Error log returns 1 with --fail-on-error
    assert run([str(log_err), "--fail-on-error"]) == 1
