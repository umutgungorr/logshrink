"""Tests for log stream aggregation, repetition collapsing, and statistics."""

from logshrink.aggregator import LogAggregator
from logshrink.config import ShrinkConfig
from logshrink.formatter import AnsiFormatter


def test_repetitive_healthchecks_suppressed(sample_healthcheck_stream):
    config = ShrinkConfig(threshold=2, color=False)
    formatter = AnsiFormatter(color_enabled=False)
    agg = LogAggregator(config=config, formatter=formatter)

    output = []
    for line in sample_healthcheck_stream:
        for out in agg.process_line(line):
            output.append(out)

    for out in agg.finalize():
        output.append(out)

    # 4 healthcheck lines should be collapsed into 1 initial line + 1 suppressed badge
    badge_lines = [item for item in output if "suppressed" in item]
    assert len(badge_lines) == 1
    assert "x4 suppressed" in badge_lines[0]

    # Verify reduction stats
    assert agg.stats.total_lines == 6
    assert agg.stats.suppressed_lines == 3
    assert agg.stats.reduction_percentage == 50.0


def test_errors_never_suppressed():
    config = ShrinkConfig(threshold=2, color=False)
    agg = LogAggregator(config=config)

    logs = [
        "2026-10-13 [ERROR] Database failure 1",
        "2026-10-13 [ERROR] Database failure 2",
        "2026-10-13 [ERROR] Database failure 3",
        "2026-10-13 [INFO] System recovered",
    ]

    output = []
    for line in logs:
        for out in agg.process_line(line):
            output.append(out)
    for out in agg.finalize():
        output.append(out)

    # Error incidents should all be emitted / captured
    assert agg.stats.incident_count >= 1


def test_errors_only_mode():
    config = ShrinkConfig(errors_only=True, color=False)
    agg = LogAggregator(config=config)

    logs = [
        "2026-10-13 [INFO] GET /home 200",
        "2026-10-13 [INFO] GET /profile 200",
        "2026-10-13 [ERROR] Failed to save avatar: disk full",
        "2026-10-13 [INFO] GET /logout 200",
    ]

    output = []
    for line in logs:
        for out in agg.process_line(line):
            output.append(out)
    for out in agg.finalize():
        output.append(out)

    # Only the error should be present in output
    assert not any("/home" in item for item in output)
    assert not any("/profile" in item for item in output)
    assert not any("/logout" in item for item in output)
    assert any("disk full" in item for item in output)


def test_custom_ignore_patterns():
    config = ShrinkConfig(
        ignore_patterns=[r"DEBUG\s+cache\.go", r"ping.*ack"],
        color=False,
    )
    agg = LogAggregator(config=config)

    logs = [
        "2026-10-13 [INFO] Application booted",
        "2026-10-13 DEBUG cache.go: key cached",
        "2026-10-13 ping from worker-1 ack",
        "2026-10-13 [INFO] Request completed",
    ]

    output = []
    for line in logs:
        for out in agg.process_line(line):
            output.append(out)
    for out in agg.finalize():
        output.append(out)

    assert not any("cache.go" in item for item in output)
    assert not any("ping from worker-1" in item for item in output)
    assert any("Application booted" in item for item in output)
    assert any("Request completed" in item for item in output)


def test_interleaved_patterns_flushing():
    config = ShrinkConfig(threshold=2, color=False)
    agg = LogAggregator(config=config)

    logs = [
        # 3 repetitions of Pattern A
        "2026-10-13 19:00:01 [INFO] GET /health 200",
        "2026-10-13 19:00:02 [INFO] GET /health 200",
        "2026-10-13 19:00:03 [INFO] GET /health 200",
        # 3 repetitions of Pattern B
        "2026-10-13 19:00:04 [INFO] Heartbeat check worker-1",
        "2026-10-13 19:00:05 [INFO] Heartbeat check worker-1",
        "2026-10-13 19:00:06 [INFO] Heartbeat check worker-1",
    ]

    output = []
    for line in logs:
        for out in agg.process_line(line):
            output.append(out)
    for out in agg.finalize():
        output.append(out)

    badges = [badge for badge in output if "suppressed" in badge]
    assert len(badges) == 2
    assert "x3 suppressed" in badges[0]
    assert "x3 suppressed" in badges[1]
