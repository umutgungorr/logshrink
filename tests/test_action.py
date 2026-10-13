"""Tests for GitHub Action entrypoint and input parsing."""

from logshrink.action import main


def test_action_success_on_file(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2026-10-13 [INFO] GET /health 200\n"
        "2026-10-13 [INFO] GET /health 200\n"
        "2026-10-13 [ERROR] Database timeout\n",
        encoding="utf-8",
    )
    export_file = tmp_path / "action_export.md"
    summary_file = tmp_path / "action_summary.md"
    output_file = tmp_path / "action_output"

    monkeypatch.setenv("INPUT_LOG_FILE", str(log_file))
    monkeypatch.setenv("INPUT_SUMMARY", "true")
    monkeypatch.setenv("INPUT_EXPORT_FILE", str(export_file))
    monkeypatch.setenv("INPUT_OPTIONS", "--no-color")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    exit_code = main()
    assert exit_code == 0
    assert export_file.exists()
    assert summary_file.exists()
    assert output_file.exists()

    output_content = output_file.read_text(encoding="utf-8")
    assert "incident-count=1" in output_content


def test_action_missing_log_file(monkeypatch, capsys):
    monkeypatch.delenv("INPUT_LOG_FILE", raising=False)
    exit_code = main()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Missing required input 'log-file'." in captured.err


def test_action_nonexistent_log_file(monkeypatch, capsys):
    monkeypatch.setenv("INPUT_LOG_FILE", "definitely_non_existent_file.log")
    exit_code = main()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: File not found" in captured.err


def test_action_quoted_options_parsing(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2026-10-13 [INFO] ignore me please\n2026-10-13 [INFO] normal line\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("INPUT_LOG_FILE", str(log_file))
    monkeypatch.setenv("INPUT_OPTIONS", '--ignore "ignore me please" --no-color')

    exit_code = main()
    assert exit_code == 0


def test_action_fail_on_error(tmp_path, monkeypatch):
    log_file = tmp_path / "crash.log"
    log_file.write_text("2026-10-13 [ERROR] Fatal exception\n", encoding="utf-8")

    monkeypatch.setenv("INPUT_LOG_FILE", str(log_file))

    # Without fail-on-error -> returns 0
    monkeypatch.setenv("INPUT_FAIL_ON_ERROR", "false")
    assert main() == 0

    # With fail-on-error -> returns 1
    monkeypatch.setenv("INPUT_FAIL_ON_ERROR", "true")
    assert main() == 1
