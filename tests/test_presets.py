"""Tests for zero-config presets (Docker, JSON, Web, Raw)."""

from logshrink.aggregator import LogAggregator
from logshrink.config import Preset, ShrinkConfig
from logshrink.normalizer import Normalizer


def test_preset_docker_container_name_removal():
    norm = Normalizer(preset=Preset.DOCKER)
    line1 = "[web-service-1] 2026-10-13 19:00:00 GET /ping 200"
    line2 = "[web-service-1] 2026-10-13 19:00:01 GET /ping 200"

    sig1, sum1 = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "GET /ping 200" in sum1


def test_preset_json_stream():
    config = ShrinkConfig(preset=Preset.JSON, threshold=2, color=False)
    agg = LogAggregator(config=config)

    lines = [
        '{"level":"info","msg":"heartbeat","t":100}',
        '{"level":"info","msg":"heartbeat","t":101}',
        '{"level":"info","msg":"heartbeat","t":102}',
        '{"level":"error","msg":"disk full","t":103}',
    ]

    output = []
    for line in lines:
        for out in agg.process_line(line):
            output.append(out)
    for out in agg.finalize():
        output.append(out)

    badges = [badge for badge in output if "suppressed" in badge]
    assert len(badges) == 1
    assert "x3 suppressed" in badges[0]
    assert agg.stats.incident_count == 1


def test_preset_web_access_logs():
    config = ShrinkConfig(preset=Preset.WEB, threshold=2, color=False)
    agg = LogAggregator(config=config)

    lines = [
        '10.0.0.1 - - [13/Oct/2026:19:00:01 +0000] "GET /metrics HTTP/1.1" 200 482 "-" "Prometheus/2.45"',
        '10.0.0.1 - - [13/Oct/2026:19:00:15 +0000] "GET /metrics HTTP/1.1" 200 482 "-" "Prometheus/2.45"',
        '10.0.0.1 - - [13/Oct/2026:19:00:30 +0000] "GET /metrics HTTP/1.1" 200 482 "-" "Prometheus/2.45"',
    ]

    output = []
    for line in lines:
        for out in agg.process_line(line):
            output.append(out)
    for out in agg.finalize():
        output.append(out)

    badges = [badge for badge in output if "suppressed" in badge]
    assert len(badges) == 1
    assert "GET /metrics 200" in badges[0]
