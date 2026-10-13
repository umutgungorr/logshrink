"""Tests for ANSI terminal formatting, badges, and incident cards."""

from logshrink.config import Incident, ShrinkStats
from logshrink.formatter import AnsiFormatter


def test_badge_formatting_colored_and_plain():
    fmt_color = AnsiFormatter(color_enabled=True)
    fmt_plain = AnsiFormatter(color_enabled=False)

    badge_color = fmt_color.format_badge(
        count=480, summary="GET /healthz 200", last_seen="19:00:00"
    )
    badge_plain = fmt_plain.format_badge(
        count=480, summary="GET /healthz 200", last_seen="19:00:00"
    )

    assert "\033[" in badge_color
    assert "\033[" not in badge_plain
    assert "[x480 suppressed]" in badge_plain
    assert "GET /healthz 200" in badge_plain
    assert "last seen 19:00:00" in badge_plain


def test_incident_box_rendering():
    fmt = AnsiFormatter(color_enabled=False)
    incident = Incident(
        id=1,
        title="NullPointerException in UserService",
        timestamp="19:30:00",
        level="ERROR",
        lines=[
            "java.lang.NullPointerException",
            "\tat com.example.service.UserService.get(UserService.java:42)",
        ],
        occurrences=3,
    )

    rendered = fmt.format_incident(incident)
    assert "INCIDENT #1: ERROR (3x)" in rendered
    assert "NullPointerException" in rendered
    assert "UserService.java:42" in rendered
    assert "┌" in rendered
    assert "└" in rendered


def test_syntax_highlighting_of_traces():
    fmt = AnsiFormatter(color_enabled=True)
    line = '  File "/app/main.py", line 42, in process'
    highlighted = fmt._syntax_highlight_trace(line)

    # File path should be cyan and line number yellow
    assert "\033[1;36m/app/main.py\033[0m" in highlighted
    assert "\033[1;33m42\033[0m" in highlighted


def test_summary_stats_card():
    fmt = AnsiFormatter(color_enabled=False)
    stats = ShrinkStats(
        total_lines=1000,
        passed_lines=50,
        suppressed_lines=950,
        incident_count=2,
    )
    stats.end_time = stats.start_time + 1.0

    card = fmt.format_summary_stats(stats, export_file="report.md")
    assert "LogShrink Summary" in card
    assert "1,000" in card
    assert "95.0% noise reduced" in card
    assert "report.md" in card
