"""Tests for incident Markdown report exporter and clipboard integration."""

from unittest.mock import MagicMock, patch

from logshrink.config import Incident, ShrinkStats
from logshrink.exporter import Exporter


def test_markdown_report_generation_with_incidents():
    stats = ShrinkStats(total_lines=5000, suppressed_lines=4500, incident_count=1)
    incidents = [
        Incident(
            id=1,
            title="ConnectionRefusedError: port 5432",
            timestamp="19:00:00",
            level="ERROR",
            lines=[
                "Traceback (most recent call last):",
                "ConnectionRefusedError: port 5432",
            ],
            occurrences=4,
            first_seen="19:00:00",
            last_seen="19:05:00",
        )
    ]

    md = Exporter.generate_markdown(incidents, stats, source_name="api.log")

    assert "# 🚨 LogShrink Incident & Noise Reduction Report" in md
    assert "90.0%" in md
    assert "api.log" in md
    assert "| #1 | **ERROR** | 4x |" in md
    assert "ConnectionRefusedError" in md


def test_markdown_report_generation_clean_run():
    stats = ShrinkStats(total_lines=100, suppressed_lines=50, incident_count=0)
    md = Exporter.generate_markdown([], stats, source_name="clean.log")

    assert "Clean run! No errors or unhandled exceptions" in md


def test_save_markdown_file(tmp_path):
    dest = tmp_path / "reports" / "incident_report.md"
    stats = ShrinkStats(total_lines=10, suppressed_lines=5)

    success = Exporter.save_markdown([], stats, str(dest))
    assert success is True
    assert dest.exists()
    content = dest.read_text(encoding="utf-8")
    assert "LogShrink Incident & Noise Reduction Report" in content


def test_clipboard_copy_native_fallback():
    # Test that calling copy_to_clipboard doesn't crash even if clipboard tools aren't present
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        result = Exporter.copy_to_clipboard("Sample Incident Log")
        assert result is True


def test_append_markdown_file(tmp_path):
    dest = tmp_path / "summary.md"
    dest.write_text("# Initial Summary Header\n", encoding="utf-8")
    stats = ShrinkStats(total_lines=20, suppressed_lines=15)

    success = Exporter.append_markdown([], stats, str(dest), source_name="ci.log")
    assert success is True
    content = dest.read_text(encoding="utf-8")
    assert "# Initial Summary Header" in content
    assert "LogShrink Incident & Noise Reduction Report" in content
    assert "ci.log" in content
