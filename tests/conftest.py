import sys
from pathlib import Path

import pytest

src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


@pytest.fixture
def sample_healthcheck_stream():
    """Generates a stream of noisy healthcheck lines with changing timestamps and durations."""
    return [
        "2026-10-13T19:00:00.100Z [INFO] Server started on port 8080",
        "2026-10-13T19:00:01.001Z [INFO] GET /healthz HTTP/1.1 200 (took 0.4ms)",
        "2026-10-13T19:00:02.002Z [INFO] GET /healthz HTTP/1.1 200 (took 0.6ms)",
        "2026-10-13T19:00:03.003Z [INFO] GET /healthz HTTP/1.1 200 (took 0.3ms)",
        "2026-10-13T19:00:04.004Z [INFO] GET /healthz HTTP/1.1 200 (took 0.5ms)",
        "2026-10-13T19:00:05.005Z [INFO] User 42 authenticated",
    ]


@pytest.fixture
def sample_python_traceback():
    """Returns a realistic Python exception traceback."""
    return [
        "2026-10-13 19:10:00 [ERROR] Unhandled exception processing request:",
        "Traceback (most recent call last):",
        '  File "/app/handlers.py", line 54, in handle_request',
        "    res = database.query(req.user_id)",
        '  File "/app/database.py", line 12, in query',
        "    raise ConnectionRefusedError('dial tcp 127.0.0.1:5432: connect refused')",
        "ConnectionRefusedError: dial tcp 127.0.0.1:5432: connect refused",
        "2026-10-13 19:10:01 [INFO] Worker recycled",
    ]


@pytest.fixture
def sample_go_panic():
    """Returns a realistic Go panic log."""
    return [
        "panic: runtime error: index out of range [3] with length 2",
        "",
        "goroutine 1 [running]:",
        "main.processItem(0xc0000a2000)",
        "\t/build/main.go:42 +0x3a",
        "main.main()",
        "\t/build/main.go:18 +0x85",
        "2026-10-13 19:15:00 server terminated",
    ]


@pytest.fixture
def sample_json_logs():
    """Returns structured JSON log entries."""
    return [
        '{"timestamp":"2026-10-13T19:20:00Z","level":"info","msg":"ping","latency_ms":1.2}',
        '{"timestamp":"2026-10-13T19:20:01Z","level":"info","msg":"ping","latency_ms":0.8}',
        '{"timestamp":"2026-10-13T19:20:02Z","level":"info","msg":"ping","latency_ms":1.5}',
        '{"timestamp":"2026-10-13T19:20:03Z","level":"error","msg":"connection lost","code":500}',
    ]
