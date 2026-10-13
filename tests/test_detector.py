"""Tests for error detection and multi-line stack trace boundaries."""

from logshrink.detector import IncidentDetector


def test_python_traceback_detection(sample_python_traceback):
    detector = IncidentDetector()
    incidents = []

    for line in sample_python_traceback:
        closed, _ = detector.process_line(line)
        if closed:
            incidents.append(closed)

    # Flush detector at end
    final = detector.flush()
    if final:
        incidents.append(final)

    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.level == "ERROR"
    assert "ConnectionRefusedError" in "".join(inc.lines)
    assert any("handlers.py" in line for line in inc.lines)


def test_go_panic_detection(sample_go_panic):
    detector = IncidentDetector()
    incidents = []

    for line in sample_go_panic:
        closed, _ = detector.process_line(line)
        if closed:
            incidents.append(closed)

    final = detector.flush()
    if final:
        incidents.append(final)

    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.level == "CRITICAL"
    assert "panic: runtime error" in inc.title
    assert any("main.go" in line for line in inc.lines)


def test_java_stack_trace_detection():
    java_log = [
        "2026-10-13 19:30:00 [INFO] Starting request handler",
        'Exception in thread "main" java.lang.NullPointerException: Cannot invoke method on null',
        "\tat com.example.service.UserService.getUser(UserService.java:84)",
        "\tat com.example.controller.UserController.handle(UserController.java:31)",
        "\t... 12 more",
        "2026-10-13 19:30:01 [INFO] Request completed",
    ]

    detector = IncidentDetector()
    incidents = []

    for line in java_log:
        closed, _ = detector.process_line(line)
        if closed:
            incidents.append(closed)

    final = detector.flush()
    if final:
        incidents.append(final)

    assert len(incidents) == 1
    inc = incidents[0]
    assert "NullPointerException" in inc.title
    assert len(inc.lines) == 4


def test_rust_panic_detection():
    rust_log = [
        "thread 'main' panicked at 'called `Option::unwrap()` on a `None` value', src/main.rs:14:9",
        "stack backtrace:",
        "   0: rust_begin_unwind",
        "   1: core::panicking::panic_fmt",
        "   2: myapp::main",
        "2026-10-13 19:35:00 [INFO] Container restarting...",
    ]

    detector = IncidentDetector()
    incidents = []

    for line in rust_log:
        closed, _ = detector.process_line(line)
        if closed:
            incidents.append(closed)

    final = detector.flush()
    if final:
        incidents.append(final)

    assert len(incidents) == 1
    inc = incidents[0]
    assert "Option::unwrap()" in inc.title


def test_single_line_error_levels():
    detector = IncidentDetector()
    assert detector.is_error_line("2026-10-13 [ERROR] Database write failed") is True
    assert detector.is_error_line("2026-10-13 [CRITICAL] Out of memory") is True
    assert detector.is_error_line("2026-10-13 [FATAL] Kernel segfault") is True
    assert detector.is_error_line('{"level":"error","msg":"connection timed out"}') is True
    assert detector.is_error_line("HTTP/1.1 500 Internal Server Error") is True
    assert detector.is_error_line("status=502 Bad Gateway") is True
    assert detector.is_error_line("2026-10-13 [INFO] Everything normal") is False


def test_warning_detection():
    detector = IncidentDetector()
    assert detector.is_warning_line("2026-10-13 [WARN] Disk space low (>85%)") is True
    assert detector.is_warning_line("2026-10-13 [WARNING] Deprecated API called") is True
    assert (
        detector.is_warning_line("2026-10-13 [ERROR] Disk full") is False
    )  # Is error, not warning


def test_incident_deduplication():
    detector = IncidentDetector()

    trace = [
        "Traceback (most recent call last):",
        '  File "/app/db.py", line 10, in connect',
        "TimeoutError: timeout",
    ]

    # Feed trace once
    for trace_line in trace:
        detector.process_line(trace_line)
    detector.process_line("2026-10-13 [INFO] Normal line 1")

    # Feed identical trace again
    for trace_line in trace:
        detector.process_line(trace_line)
    detector.process_line("2026-10-13 [INFO] Normal line 2")

    detector.flush()

    all_incs = detector.all_incidents
    assert len(all_incs) == 1
    assert all_incs[0].occurrences == 2
