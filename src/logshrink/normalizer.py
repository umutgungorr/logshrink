"""Log line normalizer and fingerprinting engine for pattern clustering."""

from __future__ import annotations

import json
import re

from logshrink.config import Preset


class Normalizer:
    """Normalizes dynamic elements (timestamps, IPs, UUIDs, numbers, durations)

    from log lines to extract canonical pattern signatures and representative summaries.
    """

    # Timestamps
    RE_ISO_TIMESTAMP = re.compile(
        r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"
    )
    RE_HTTP_DATE = re.compile(r"\[\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4}\]")
    RE_SYSLOG_DATE = re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b"
    )
    RE_TIME_ONLY = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:\.\d{3,9})?\b")

    # Network & Identifiers
    RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    RE_IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}\b")
    RE_UUID = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    )
    RE_HEX_ADDR = re.compile(r"\b0x[0-9a-fA-F]+\b")
    RE_HEX_HASH = re.compile(r"\b[0-9a-fA-F]{16,64}\b")
    RE_PORT = re.compile(r":\d{4,5}\b")

    # Metrics & Durations
    RE_DURATION = re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:µs|us|ns|ms|s|sec|seconds|min|m|h)\b", re.IGNORECASE
    )
    RE_SIZE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:B|kB|KB|MB|GB|TB|bytes)\b", re.IGNORECASE)
    RE_NUMERIC_PARAM = re.compile(r"(?<=[=:])\s*\d+(?:\.\d+)?(?=[,;\s]|$)")
    RE_REQUEST_ID = re.compile(
        r"\b(?:req(?:uest)?[-_]?id|trace[-_]?id|span[-_]?id|tid|txid)[=:\s][A-Za-z0-9_-]+\b",
        re.IGNORECASE,
    )

    # Docker / Compose prefix
    RE_DOCKER_PREFIX = re.compile(
        r"^(?:\[[a-zA-Z0-9_\-\.]+\](?:\s*\|\s*|\s+)|[a-zA-Z0-9_\-\.]+\s*\|\s*|(?:\d{4}-\d{2}-\d{2}T[^\s]+\s+(?:stdout|stderr)\s+[FP]\s+))"
    )

    # Web log pattern (e.g. GET /path HTTP/1.1 200)
    RE_WEB_ACCESS = re.compile(r'"([A-Z]{3,7})\s+([^\s?]+)(?:\?[^\s"]*)?\s+HTTP/[0-9.]+"\s+(\d{3})')

    # Common Polling keywords
    RE_POLLING_SIGNS = re.compile(
        r"(?:/healthz?|/ready|/live|/ping|/metrics|heartbeat|keep-alive|SELECT 1|kube-probe)",
        re.IGNORECASE,
    )

    def __init__(self, preset: Preset = Preset.AUTO):
        self.preset = preset

    def normalize(self, line: str) -> tuple[str, str]:
        """Returns a tuple of (signature, summary).

        signature: Canonical string used for grouping lines into identical clusters.
        summary: Short human-readable title describing the message pattern.
        """
        line_clean = line.strip()
        if not line_clean:
            return ("", "")

        # 1. Preset specific preprocessing
        content = line_clean
        if self.preset in (Preset.AUTO, Preset.DOCKER):
            content = self.RE_DOCKER_PREFIX.sub("", content).strip()

        # Try JSON parsing if requested or auto or docker
        if (
            self.preset in (Preset.AUTO, Preset.JSON, Preset.DOCKER)
            and content.startswith("{")
            and content.endswith("}")
        ):
            json_sig, json_sum = self._normalize_json(content)
            if json_sig:
                return (json_sig, json_sum)

        # Try Web access log parsing
        web_match = self.RE_WEB_ACCESS.search(content)
        if web_match:
            method, path, status = web_match.groups()
            sig = f"WEB:{method} {path} {status}"
            summary = f"{method} {path} {status}"
            return (sig, summary)

        # 2. General regex maskings for standard text lines
        sig = content

        # Mask timestamps
        sig = self.RE_ISO_TIMESTAMP.sub("<TIME>", sig)
        sig = self.RE_HTTP_DATE.sub("<TIME>", sig)
        sig = self.RE_SYSLOG_DATE.sub("<TIME>", sig)
        sig = self.RE_TIME_ONLY.sub("<TIME>", sig)

        # Mask network/IDs
        sig = self.RE_REQUEST_ID.sub("<REQ_ID>", sig)
        sig = self.RE_UUID.sub("<UUID>", sig)
        sig = self.RE_HEX_ADDR.sub("<ADDR>", sig)
        sig = self.RE_HEX_HASH.sub("<HASH>", sig)
        sig = self.RE_IPV4.sub("<IP>", sig)
        sig = self.RE_IPV6.sub("<IP>", sig)
        sig = self.RE_PORT.sub(":<PORT>", sig)

        # Mask durations and sizes
        sig = self.RE_DURATION.sub("<DUR>", sig)
        sig = self.RE_SIZE.sub("<SIZE>", sig)
        sig = self.RE_NUMERIC_PARAM.sub("<NUM>", sig)

        # Collapse whitespace
        sig = " ".join(sig.split())

        # Build clean summary
        summary = self._extract_summary(content, sig)
        return (sig, summary)

    def is_polling_noise(self, line: str) -> bool:
        """Determines if a line looks like repetitive heartbeat or healthcheck polling."""
        return bool(self.RE_POLLING_SIGNS.search(line))

    def _normalize_json(self, content: str) -> tuple[str | None, str | None]:
        """Parses and extracts key invariants from JSON log messages."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return (None, None)

            # Docker JSON file driver handling (e.g. {"log": "GET /healthz 200\n", "stream": "stdout"})
            raw_log = data.get("log")
            if isinstance(raw_log, str) and raw_log.strip():
                inner_text = raw_log.strip()
                stream_type = str(data.get("stream") or "stdout")
                inner_sig, inner_sum = self.normalize(inner_text)
                if inner_sig:
                    return (f"DOCKER_JSON:{stream_type}:{inner_sig}", inner_sum)

            level = str(
                data.get("level")
                or data.get("severity")
                or data.get("log_level")
                or data.get("lvl")
                or ""
            ).lower()
            msg = str(
                data.get("msg")
                or data.get("message")
                or data.get("event")
                or data.get("action")
                or data.get("body")
                or data.get("text")
                or data.get("error")
                or data.get("err")
                or ""
            )
            path = str(data.get("path") or data.get("url") or data.get("uri") or "")
            status = str(data.get("status") or data.get("status_code") or "")

            components = []
            if level:
                components.append(f"lvl={level}")
            if msg:
                components.append(f"msg={msg}")
            if path:
                components.append(f"path={path}")
            if status:
                components.append(f"status={status}")

            if not components:
                first_val = ""
                for k, v in data.items():
                    if isinstance(v, str) and len(v) < 60:
                        first_val = f"{k}={v}"
                        break
                keys = ",".join(sorted(data.keys())[:5])
                components.append(f"keys=[{keys}]")
                if first_val:
                    components.append(first_val)

            sig = f"JSON:{';'.join(components)}"

            # Summary
            if path and status:
                summary = f"{msg or 'HTTP'} {path} {status}".strip()
            elif msg:
                summary = f"{level.upper() + ': ' if level else ''}{msg}"
            else:
                summary = sig

            return (sig, summary)
        except Exception:
            return (None, None)

    def _extract_summary(self, raw_line: str, signature: str) -> str:
        """Constructs a compact representation for display in suppressed badges."""
        s = signature
        for token in (
            "<TIME>",
            "<IP>",
            "<PORT>",
            "<ADDR>",
            "<HASH>",
            "<UUID>",
            "<DUR>",
            "<SIZE>",
            "<NUM>",
            "<REQ_ID>",
        ):
            s = s.replace(token, "")

        s = re.sub(r"\(\s*(?:took|in)?\s*\)", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\(\s*\)", "", s)
        s = re.sub(r"^[\s\|\:\-\]]+", "", s).strip()
        s = re.sub(r"\s+", " ", s).strip()
        if not s:
            s = raw_line[:40].strip()

        if len(s) > 60:
            return s[:57] + "..."
        return s
