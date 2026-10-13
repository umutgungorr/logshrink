"""Tests for log line normalization and signature fingerprinting."""

from logshrink.config import Preset
from logshrink.normalizer import Normalizer


def test_iso_timestamp_normalization():
    norm = Normalizer()
    line1 = "2026-10-13T19:00:01.123Z [INFO] Service healthy"
    line2 = "2026-10-13T19:00:02.456Z [INFO] Service healthy"

    sig1, sum1 = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "[INFO] Service healthy" in sig1
    assert "Service healthy" in sum1


def test_ip_address_and_port_normalization():
    norm = Normalizer()
    line1 = "Incoming request from 192.168.1.100:49210"
    line2 = "Incoming request from 10.0.0.5:58219"

    sig1, _ = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "<IP>:<PORT>" in sig1


def test_uuid_and_hash_normalization():
    norm = Normalizer()
    line1 = "Processing session 123e4567-e89b-12d3-a456-426614174000 hash a1b2c3d4e5f67890123456789abcdef0"
    line2 = "Processing session 987fcdeb-51a2-43d7-9876-ba9876543210 hash 0fedcba9876543210987654321fedcba"

    sig1, _ = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "<UUID>" in sig1
    assert "<HASH>" in sig1


def test_duration_and_size_normalization():
    norm = Normalizer()
    line1 = "Query took 12ms, returned 45KB"
    line2 = "Query took 180ms, returned 120KB"

    sig1, _ = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "<DUR>" in sig1
    assert "<SIZE>" in sig1


def test_empty_and_whitespace_lines():
    norm = Normalizer()
    sig, summary = norm.normalize("")
    assert sig == ""
    assert summary == ""

    sig, summary = norm.normalize("   \t  \n")
    assert sig == ""
    assert summary == ""


def test_docker_prefix_stripping():
    norm = Normalizer(preset=Preset.DOCKER)
    line1 = "api-gateway_1 | 2026-10-13T19:00:00Z GET /ready 200"
    line2 = "api-gateway_1 | 2026-10-13T19:00:05Z GET /ready 200"

    sig1, sum1 = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "GET /ready 200" in sum1


def test_web_access_log_normalization():
    norm = Normalizer(preset=Preset.WEB)
    line1 = '192.168.1.1 - - [13/Oct/2026:19:00:01 +0000] "GET /healthz HTTP/1.1" 200 12 "-" "curl/7.68.0"'
    line2 = '10.0.0.2 - - [13/Oct/2026:19:00:02 +0000] "GET /healthz HTTP/1.1" 200 12 "-" "kube-probe/1.28"'

    sig1, sum1 = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert sig1 == "WEB:GET /healthz 200"
    assert sum1 == "GET /healthz 200"


def test_json_log_normalization():
    norm = Normalizer(preset=Preset.JSON)
    line1 = '{"time":"2026-10-13T19:00:01Z","level":"info","msg":"heartbeat","latency":0.001}'
    line2 = '{"time":"2026-10-13T19:00:02Z","level":"info","msg":"heartbeat","latency":0.003}'

    sig1, sum1 = norm.normalize(line1)
    sig2, _ = norm.normalize(line2)

    assert sig1 == sig2
    assert "msg=heartbeat" in sig1
    assert "heartbeat" in sum1


def test_is_polling_noise():
    norm = Normalizer()
    assert norm.is_polling_noise("GET /healthz 200 OK") is True
    assert norm.is_polling_noise("GET /ready 200 OK") is True
    assert norm.is_polling_noise("Sending heartbeat to cluster coordinator") is True
    assert norm.is_polling_noise("kube-probe checking worker") is True
    assert norm.is_polling_noise("POST /api/v1/charge_credit_card 200") is False
    assert norm.is_polling_noise("User login failed") is False
