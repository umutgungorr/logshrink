"""Edge cases and stress tests for LogShrink."""

import io
from unittest.mock import patch

from logshrink.aggregator import LogAggregator
from logshrink.cli import run
from logshrink.config import Preset, ShrinkConfig
from logshrink.detector import IncidentDetector
from logshrink.formatter import AnsiFormatter
from logshrink.normalizer import Normalizer


def test_empty_stream():
    config = ShrinkConfig()
    agg = LogAggregator(config=config)
    output = list(agg.finalize())
    assert output == []
    assert agg.stats.total_lines == 0
    assert agg.stats.reduction_percentage == 0.0


def test_single_line_input():
    config = ShrinkConfig(threshold=2, color=False)
    agg = LogAggregator(config=config)

    output = list(agg.process_line("Single standalone line"))
    output.extend(agg.finalize())

    assert len(output) == 1
    assert output[0] == "Single standalone line"
    assert agg.stats.total_lines == 1
    assert agg.stats.suppressed_lines == 0


def test_massive_repetition_scaling():
    config = ShrinkConfig(threshold=2, color=False)
    agg = LogAggregator(config=config)

    output = []
    # 5,000 repetitive healthchecks
    for i in range(5000):
        line = f"2026-10-13T19:00:{i % 60:02d}.000Z [INFO] GET /live 200 OK (0.2ms)"
        output.extend(agg.process_line(line))

    output.extend(agg.finalize())

    badges = [badge for badge in output if "suppressed" in badge]
    assert len(badges) == 1
    assert "x5000 suppressed" in badges[0]
    assert agg.stats.total_lines == 5000
    assert agg.stats.suppressed_lines == 4999
    assert agg.stats.reduction_percentage > 99.9


def test_nodejs_async_stack_trace():
    node_log = [
        "2026-10-13 19:40:00 [ERROR] Uncaught exception:",
        "TypeError: Cannot read properties of undefined (reading 'map')",
        "    at async Object.renderList (/app/dist/index.js:84:22)",
        "    at async Server.<anonymous> (/app/dist/server.js:42:15)",
        "    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)",
        "2026-10-13 19:40:01 [INFO] Worker restart signal sent",
    ]

    detector = IncidentDetector()
    incidents = []
    for line in node_log:
        closed, _ = detector.process_line(line)
        if closed:
            incidents.append(closed)
    final = detector.flush()
    if final:
        incidents.append(final)

    assert len(incidents) == 1
    inc = incidents[0]
    assert "TypeError" in inc.title or "ERROR" in inc.level
    assert any("renderList" in frame for frame in inc.lines)


def test_http_gateway_errors_502_503_504():
    detector = IncidentDetector()
    assert detector.is_error_line("nginx: 10.0.0.1 - - HTTP/1.1 502 Bad Gateway") is True
    assert detector.is_error_line("upstream status=503 Service Unavailable") is True
    assert detector.is_error_line("cloud-edge: status=504 Gateway Timeout") is True


def test_malformed_json_fallback():
    norm = Normalizer(preset=Preset.JSON)
    # Starts and ends with brackets but is invalid JSON syntax
    broken_json = "{'key': invalid_value, broken}"
    sig, summary = norm.normalize(broken_json)
    assert sig != ""
    assert summary != ""


def test_nested_export_directory_creation(tmp_path):
    deep_path = tmp_path / "deep" / "nested" / "dir" / "report.md"
    log_file = tmp_path / "errors.log"
    log_file.write_text("2026-10-13 [ERROR] Fatal crash\n", encoding="utf-8")

    exit_code = run([str(log_file), "--export", str(deep_path), "--no-stats"])
    assert exit_code == 0
    assert deep_path.exists()
    assert "# 🚨 LogShrink" in deep_path.read_text(encoding="utf-8")


def test_cli_stdin_pipe(capsys):
    test_input = "2026-10-13 [INFO] GET /health 200\n2026-10-13 [INFO] GET /health 200\n"
    with patch("sys.stdin", io.StringIO(test_input)):
        exit_code = run(["-", "--no-color", "--no-stats"])
        assert exit_code == 0

    captured = capsys.readouterr()
    assert "[x2 suppressed]" in captured.out


def test_no_color_environment_variable(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    fmt = AnsiFormatter(color_enabled=True)
    badge = fmt.format_badge(10, "GET /health 200")
    assert "\033[" not in badge


def test_interleaved_alternating_streams():
    """Verify that multiple alternating patterns (A, B, A, B, A, B) are both suppressed."""
    config = ShrinkConfig(threshold=2, color=False)
    agg = LogAggregator(config=config)

    lines = [
        "2026-10-13 12:00:00 [INFO] GET /healthz 200",
        "2026-10-13 12:00:01 [INFO] GET /metrics 200",
        "2026-10-13 12:00:02 [INFO] GET /healthz 200",
        "2026-10-13 12:00:03 [INFO] GET /metrics 200",
        "2026-10-13 12:00:04 [INFO] GET /healthz 200",
        "2026-10-13 12:00:05 [INFO] GET /metrics 200",
    ]

    output = []
    for line in lines:
        output.extend(agg.process_line(line))
    output.extend(agg.finalize())

    badges = [badge for badge in output if "suppressed" in badge]
    assert len(badges) == 2
    assert any("healthz" in b for b in badges)
    assert any("metrics" in b for b in badges)
    assert agg.stats.total_lines == 6
    assert agg.stats.suppressed_lines == 4
    assert agg.stats.passed_lines == 2


def test_false_positive_error_phrases_suppressed():
    """Verify that lines with 'err: nil', '0 errors', 'error_handler', etc. are not marked as errors."""
    detector = IncidentDetector()

    assert detector.is_error_line("2026-10-13 [INFO] Completed with 0 errors") is False
    assert (
        detector.is_error_line("2026-10-13 [INFO] Registered error_handler for route /api") is False
    )
    assert detector.is_error_line("2026-10-13 [INFO] Database query returned err: nil") is False
    assert detector.is_error_line("2026-10-13 [INFO] Status: ok, error: none") is False
    assert detector.is_error_line("2026-10-13 [INFO] Operation finished without err") is False
    assert detector.is_error_line('{"level":"info","msg":"error_handler initialized"}') is False


def test_web_access_5xx_detected_as_error_and_not_suppressed():
    """Verify that standard Nginx/Apache 5xx access logs are detected as errors."""
    detector = IncidentDetector()
    access_500 = '127.0.0.1 - - [13/Oct/2026:12:00:00 +0000] "GET /api HTTP/1.1" 500 123'
    access_502 = '127.0.0.1 - - [13/Oct/2026:12:00:00 +0000] "POST /api HTTP/1.1" 502 45'
    access_404 = '127.0.0.1 - - [13/Oct/2026:12:00:00 +0000] "GET /api HTTP/1.1" 404 12'

    assert detector.is_error_line(access_500) is True
    assert detector.is_error_line(access_502) is True
    assert detector.is_error_line(access_404) is False
    assert detector.is_warning_line(access_404) is True

    # In errors-only mode, 500 must NOT be suppressed
    config = ShrinkConfig(preset=Preset.WEB, errors_only=True, color=False)
    agg = LogAggregator(config=config)
    output = list(agg.process_line(access_500))
    output.extend(agg.finalize())
    assert agg.stats.suppressed_lines == 0
    assert agg.stats.incident_count == 1


def test_docker_json_log_driver_parsing():
    """Verify that Docker container JSON file logs unpack inner log payloads."""
    norm = Normalizer(preset=Preset.DOCKER)
    line1 = '{"log":"2026-10-13 [INFO] GET /healthz 200\\n","stream":"stdout"}'
    line2 = '{"log":"2026-10-13 [INFO] GET /healthz 200\\n","stream":"stdout"}'

    sig1, sum1 = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "DOCKER_JSON" in sig1
    assert "healthz" in sum1


def test_summary_tokens_stripped():
    """Verify that duration and number tokens do not leak into badge summaries."""
    norm = Normalizer()
    line = "2026-10-13 12:00:00 [INFO] GET /healthz 200 OK (took 0.4ms) batch 42"
    _sig, summary = norm.normalize(line)

    assert "<DUR>" not in summary
    assert "<NUM>" not in summary
    assert "<TIME>" not in summary


def test_exact_stats_reconciliation():
    """Verify that passed_lines + suppressed_lines == total_lines exactly."""
    config = ShrinkConfig(threshold=2, color=False)
    agg = LogAggregator(config=config)

    logs = [
        "2026-10-13 [INFO] Server booted",
        "2026-10-13 [INFO] GET /health 200",
        "2026-10-13 [INFO] GET /health 200",
        "2026-10-13 [INFO] GET /health 200",
        "2026-10-13 [ERROR] Database lost",
        "Traceback (most recent call last):",
        '  File "db.py", line 12, in query',
        "OperationalError: lost",
        "2026-10-13 [INFO] Reconnected",
    ]

    output = []
    for line in logs:
        output.extend(agg.process_line(line))
    output.extend(agg.finalize())

    assert agg.stats.total_lines == 9
    assert agg.stats.suppressed_lines == 2
    assert agg.stats.passed_lines == 7
    assert agg.stats.passed_lines + agg.stats.suppressed_lines == agg.stats.total_lines
    assert agg.stats.incident_count == 1


def test_custom_badge_format():
    """Verify that custom badge_format templates are properly rendered."""
    fmt = AnsiFormatter(color_enabled=False)
    badge = fmt.format_badge(
        count=15,
        summary="GET /health",
        last_seen="12:00:00",
        badge_format="[COLLAPSED x{count}: {summary}]",
    )
    assert "[COLLAPSED x15: GET /health]" in badge


def test_cli_window_flag_parsed():
    """Verify that --window / -w argument is correctly parsed by CLI parser."""
    from logshrink.cli import create_parser

    parser = create_parser()
    args = parser.parse_args(["-w", "10.5"])
    assert args.window == 10.5


def test_follow_file_incomplete_line_handling(tmp_path):
    """Verify follow_file does not yield incomplete half-lines before newline is written."""
    from logshrink.streamer import Streamer

    log_file = tmp_path / "partial.log"
    log_file.write_text("initial\n", encoding="utf-8")

    gen = Streamer.follow_file(str(log_file), poll_interval=0.01)
    assert next(gen) == "initial\n"

    # Write partial line without newline
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("half_")

    # Complete line with newline
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("complete\n")

    assert next(gen) == "half_complete\n"
    gen.close()


def test_clipboard_copy_on_clean_run(capsys):
    """Verify that --copy handles 0 incidents cleanly without failing."""
    with patch("logshrink.exporter.Exporter.copy_to_clipboard", return_value=True):
        test_input = "2026-10-13 [INFO] Server started\n"
        with patch("sys.stdin", io.StringIO(test_input)):
            exit_code = run(["-", "--copy", "--no-color", "--no-stats"])
            assert exit_code == 0

        captured = capsys.readouterr()
        assert "clean run report" in captured.err
