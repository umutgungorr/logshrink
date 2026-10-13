"""Error, exception, and multi-line stack trace boundary detector."""

from __future__ import annotations

import datetime
import json
import re

from logshrink.config import Incident


class IncidentDetector:
    """Detects error boundaries, multi-line stack traces (Python, Java, Go,

    Node, Rust), and unhandled crashes.
    """

    # Error Level Markers
    RE_ERROR_LEVEL = re.compile(
        r"(?:\[|\b)(?:FATAL|CRITICAL|PANIC|SEVERE|EMERGENCY|ERROR)(?:\]|\b|:|\s*\|)|"
        r'level=["\']?(?:fatal|critical|panic|severe|emergency|error|err)["\']?|'
        r"\b(?:\[ERR\]|ERR:|\blvl=err\b|\blevel=err\b|\bERR\s*[-|])",
        re.IGNORECASE,
    )
    RE_STRICT_ERROR_TAG = re.compile(
        r"(?:\[|\b)(?:FATAL|CRITICAL|PANIC|SEVERE|EMERGENCY|ERROR)(?:\]|:|\s*\|)|"
        r'level=["\']?(?:fatal|critical|panic|severe|emergency|error)["\']?',
        re.IGNORECASE,
    )
    RE_WARN_LEVEL = re.compile(
        r"(?:\[|\b)(?:WARN|WARNING)(?:\]|\b|:|\s*\|)|"
        r'level=["\']?(?:warn|warning)["\']?|\blvl=warn\b',
        re.IGNORECASE,
    )
    RE_INFO_LEVEL = re.compile(
        r"(?:\[|\b)(?:INFO|DEBUG|TRACE|NOTICE)(?:\]|:|\s*\|)|"
        r'level=["\']?(?:info|debug|trace|notice)["\']?|\blvl=(?:info|debug|trace)\b',
        re.IGNORECASE,
    )
    RE_FALSE_ERROR = re.compile(
        r"\b(?:0\s+errors?|zero\s+errors?|no\s+errors?|without\s+(?:any\s+)?errors?|"
        r"without\s+err|err:\s*nil|err\s*==?\s*nil|error:\s*(?:nil|none|null)|"
        r"errors?:\s*0|error_code\s*=\s*0|error_handler|error_log)\b",
        re.IGNORECASE,
    )

    # Multi-line Trace Starters
    RE_PY_TRACE_START = re.compile(r"^Traceback \(most recent call last\):")
    RE_JAVA_TRACE_START = re.compile(
        r"^(?:[a-zA-Z0-9_$.]+(?:Exception|Error|Throwable):|Exception in thread )"
    )
    RE_GO_PANIC_START = re.compile(r"^panic:\s+.+")
    RE_RUST_PANIC_START = re.compile(r"^thread '.+' panicked at")
    RE_NODE_ERROR_START = re.compile(r"^(?:[A-Z][a-zA-Z0-9_$]*(?:Error|Exception)|Error):\s+.+")
    RE_HTTP_5XX = re.compile(
        r'HTTP/[0-9.]+"\s+5\d{2}\b|\bHTTP/[0-9.]+\s+5\d{2}\b|\bstatus[=:\s]5\d{2}\b|"\s+5\d{2}\s+\d+',
        re.IGNORECASE,
    )
    RE_HTTP_4XX = re.compile(
        r'HTTP/[0-9.]+"\s+4\d{2}\b|\bHTTP/[0-9.]+\s+4\d{2}\b|\bstatus[=:\s]4\d{2}\b|"\s+4\d{2}\s+\d+',
        re.IGNORECASE,
    )

    # Trace Frame Continuations
    RE_PY_FRAME = re.compile(r'^\s*File\s+"[^"]+",\s+line\s+\d+')
    RE_PY_EXC_LINE = re.compile(
        r"^(?:[a-zA-Z0-9_.]*(?:Error|Exception|Panic|Fault|Warning|Interrupt)|[A-Z][a-zA-Z0-9_$]*):\s*"
    )
    RE_JAVA_FRAME = re.compile(
        r"^\s+at\s+[a-zA-Z0-9_$.]+\(.*?\)|^\s+Caused by:|^(\s+\.\.\.\s+\d+\s+more)"
    )
    RE_GO_FRAME = re.compile(
        r"^(?:goroutine \d+|created by |[a-zA-Z0-9_./]+\.[a-zA-Z0-9_]+(?:\(.*\))?|^\s+/[^:]+:\d+|\t)"
    )
    RE_RUST_FRAME = re.compile(r"^\s*(?:stack backtrace:|\d+:\s+\S+)")
    RE_NODE_FRAME = re.compile(r"^\s+at\s+.+\(.*?\)|^\s+at\s+.+:\d+:\d+")
    RE_INDENTED = re.compile(r"^\s{2,}\S+")

    def __init__(self):
        self._current_incident: Incident | None = None
        self._incident_counter: int = 0
        self._seen_incidents: dict[str, Incident] = {}

    def is_error_line(self, line: str) -> bool:
        """Checks if a single line contains explicit error markers."""
        stripped = line.strip()
        if not stripped:
            return False

        # Trace starters are always error incidents
        if self.is_trace_starter(stripped):
            return True

        # Check structured JSON line
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                data = json.loads(stripped)
                if isinstance(data, dict):
                    lvl = str(
                        data.get("level")
                        or data.get("severity")
                        or data.get("log_level")
                        or data.get("lvl")
                        or ""
                    ).lower()
                    status = str(data.get("status") or data.get("status_code") or "")
                    if status.startswith("5") and len(status) == 3:
                        return True
                    if lvl in ("fatal", "critical", "panic", "severe", "emergency", "error", "err"):
                        return True
                    if lvl in ("info", "debug", "trace", "notice", "warn", "warning"):
                        return False
            except Exception:
                pass

        # Check HTTP 5xx codes (including Nginx/Apache access log formats)
        if self.RE_HTTP_5XX.search(line):
            return True

        # Check false-error phrases (e.g. "0 errors", "err: nil", "status=ok error=none")
        if self.RE_FALSE_ERROR.search(line) and not self.RE_STRICT_ERROR_TAG.search(line):
            return False

        # If line has explicit INFO/DEBUG/TRACE level tag, it is not an error line
        if self.RE_INFO_LEVEL.search(line):
            return False

        # General error markers
        return bool(self.RE_ERROR_LEVEL.search(line))

    def is_warning_line(self, line: str) -> bool:
        """Checks if a line contains warning markers."""
        if self.is_error_line(line):
            return False

        stripped = line.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                data = json.loads(stripped)
                if isinstance(data, dict):
                    lvl = str(
                        data.get("level")
                        or data.get("severity")
                        or data.get("log_level")
                        or data.get("lvl")
                        or ""
                    ).lower()
                    if lvl in ("warn", "warning"):
                        return True
                    status = str(data.get("status") or data.get("status_code") or "")
                    if status.startswith("4") and len(status) == 3:
                        return True
            except Exception:
                pass

        if self.RE_HTTP_4XX.search(line):
            return True

        return bool(self.RE_WARN_LEVEL.search(line))

    def is_trace_starter(self, line: str) -> bool:
        """Checks whether the line explicitly starts a stack trace or panic."""
        stripped = line.strip()
        if self.RE_PY_TRACE_START.search(stripped):
            return True
        if self.RE_GO_PANIC_START.search(stripped):
            return True
        if self.RE_RUST_PANIC_START.search(stripped):
            return True
        if self.RE_JAVA_TRACE_START.search(stripped):
            return True
        return bool(self.RE_NODE_ERROR_START.search(stripped))

    def is_trace_continuation(self, line: str) -> bool:
        """Checks whether the line is a continuation frame of an ongoing stack trace."""
        if not line.strip():
            return True
        # If active incident starts with an error line, a following Traceback line belongs to it
        if self._current_incident is not None and self.is_trace_starter(line):
            return True
        if self.RE_PY_FRAME.search(line):
            return True
        if self.RE_PY_EXC_LINE.search(line.strip()):
            return True
        if self.RE_JAVA_FRAME.search(line):
            return True
        if self.RE_GO_FRAME.search(line):
            return True
        if self.RE_RUST_FRAME.search(line):
            return True
        if self.RE_NODE_FRAME.search(line):
            return True
        # Indented line during active incident
        if self._current_incident is not None and self.RE_INDENTED.match(line):
            return True
        # Chained exceptions
        return bool("During handling of the above exception" in line or "Caused by:" in line)

    def process_line(self, line: str) -> tuple[Incident | None, bool]:
        """Processes a line through the incident state machine.

        Returns:
            (closed_incident, is_active_incident_line)
        """
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        # 1. If currently accumulating an incident
        if self._current_incident is not None:
            if self.is_trace_continuation(line):
                self._current_incident.lines.append(line)
                self._current_incident.last_seen = now_str
                return (None, True)
            else:
                # Active incident ends here. Close and emit.
                closed = self._finalize_current_incident()
                # Check if this new line is itself a new error/trace
                if self.is_trace_starter(line) or self.is_error_line(line):
                    self._start_incident(line, now_str)
                    return (closed, True)
                return (closed, False)

        # 2. Not in an incident: check if line starts an incident
        if self.is_trace_starter(line) or self.is_error_line(line):
            self._start_incident(line, now_str)
            return (None, True)

        return (None, False)

    def flush(self) -> Incident | None:
        """Flushes any currently open incident at stream completion."""
        return self._finalize_current_incident()

    def _start_incident(self, initial_line: str, timestamp: str) -> None:
        """Begins accumulating a new incident."""
        self._incident_counter += 1
        level = "ERROR"
        upper = initial_line.upper()
        if "CRITICAL" in upper or "FATAL" in upper or "PANIC" in upper:
            level = "CRITICAL"

        title = initial_line.strip()[:100]
        self._current_incident = Incident(
            id=self._incident_counter,
            title=title,
            timestamp=timestamp,
            level=level,
            lines=[initial_line],
            first_seen=timestamp,
            last_seen=timestamp,
            occurrences=1,
            fingerprint=self._compute_fingerprint(initial_line),
        )

    def _finalize_current_incident(self) -> Incident | None:
        """Closes the current incident and tracks deduplicated counts."""
        if self._current_incident is None:
            return None

        inc = self._current_incident
        self._current_incident = None

        # Strip trailing empty lines
        while inc.lines and not inc.lines[-1].strip():
            inc.lines.pop()
        if not inc.lines:
            return None

        # Re-evaluate fingerprint with full trace if available
        if len(inc.lines) > 1:
            # Use last meaningful line (e.g. exception type) + first line
            inc.fingerprint = self._compute_trace_fingerprint(inc.lines)

        fp = inc.fingerprint
        if fp in self._seen_incidents:
            existing = self._seen_incidents[fp]
            existing.occurrences += 1
            existing.last_seen = inc.last_seen
            return existing
        else:
            self._seen_incidents[fp] = inc
            return inc

    def _compute_fingerprint(self, initial_line: str) -> str:
        """Computes a normalized signature for a single error line."""
        cleaned = re.sub(r"\d+", "N", initial_line)
        cleaned = re.sub(r"0x[0-9a-fA-F]+", "PTR", cleaned)
        return cleaned.strip()

    def _compute_trace_fingerprint(self, lines: list[str]) -> str:
        """Computes normalized signature for a multi-line stack trace."""
        key_parts = []
        for trace_line in lines:
            s = trace_line.strip()
            if self.is_trace_starter(s) or self.RE_PY_EXC_LINE.match(s) or "Exception" in s:
                key_parts.append(re.sub(r"0x[0-9a-fA-F]+|\d+", "N", s))
        if not key_parts:
            key_parts = [re.sub(r"\d+", "N", lines[0].strip())]
        return " | ".join(key_parts[:3])

    @property
    def all_incidents(self) -> list[Incident]:
        """Returns all unique detected incidents."""
        return list(self._seen_incidents.values())
