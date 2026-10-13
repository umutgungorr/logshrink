"""Log stream aggregator and pattern deduplication engine."""

from __future__ import annotations

import datetime
import re
from collections.abc import Generator

from logshrink.config import Incident, ShrinkConfig, ShrinkStats
from logshrink.detector import IncidentDetector
from logshrink.formatter import AnsiFormatter
from logshrink.normalizer import Normalizer


class LogCluster:
    """Tracks a cluster of repeated log lines sharing the same signature."""

    def __init__(self, signature: str, summary: str, initial_line: str):
        self.signature = signature
        self.summary = summary
        self.initial_line = initial_line
        self.count = 0  # Number of suppressed repeats after the first
        self.buffered_lines: list[str] = []
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.first_seen = now_str
        self.last_seen = now_str

    def add_repeat(self, line: str) -> None:
        self.count += 1
        self.buffered_lines.append(line)
        self.last_seen = datetime.datetime.now().strftime("%H:%M:%S")


class LogAggregator:
    """Processes log streams line by line, deduplicating repetitive messages

    into counter badges and isolating error incident blocks.
    """

    def __init__(
        self,
        config: ShrinkConfig,
        normalizer: Normalizer | None = None,
        detector: IncidentDetector | None = None,
        formatter: AnsiFormatter | None = None,
    ):
        self.config = config
        self.normalizer = normalizer or Normalizer(preset=config.preset)
        self.detector = detector or IncidentDetector()
        self.formatter = formatter or AnsiFormatter(color_enabled=config.color)
        self.stats = ShrinkStats()

        # Multi-cluster dictionary for interleaved pattern deduplication
        self._active_clusters: dict[str, LogCluster] = {}
        self._current_cluster: LogCluster | None = None
        self._compiled_ignores = [re.compile(p) for p in self.config.ignore_patterns]

    def process_line(self, raw_line: str) -> Generator[str, None, None]:
        """Processes a single incoming log line and yields output strings to display."""
        line = raw_line.rstrip("\r\n")
        self.stats.total_lines += 1

        # 1. Custom ignore patterns check
        for pattern in self._compiled_ignores:
            if pattern.search(line):
                self.stats.suppressed_lines += 1
                return

        # 2. Check detector state (multi-line traces and error markers)
        closed_incident, is_active_trace = self.detector.process_line(line)

        # If an earlier incident just closed, yield its formatted box
        if closed_incident is not None:
            self.stats.incident_count += 1
            self.stats.passed_lines += len(closed_incident.lines)
            self.stats.incident_lines += len(closed_incident.lines)
            yield from self._flush_all_clusters()
            yield self.formatter.format_incident(closed_incident)

        if is_active_trace:
            # We are inside or starting an incident:
            # First flush any pending suppressed normal log clusters
            yield from self._flush_all_clusters()
            return

        # 3. Not in an incident: check if errors-only filter is active
        if self.config.errors_only and not (
            self.detector.is_error_line(line) or self.detector.is_warning_line(line)
        ):
            self.stats.suppressed_lines += 1
            return

        # 4. Check for standalone warnings
        if self.detector.is_warning_line(line):
            yield from self._flush_all_clusters()
            self.stats.passed_lines += 1
            yield self.formatter.format_warning_line(line)
            return

        # 5. Normal log deduplication clustering
        sig, summary = self.normalizer.normalize(line)

        if not sig:
            # Empty line
            yield from self._flush_all_clusters()
            self.stats.passed_lines += 1
            yield ""
            return

        # Fast path: consecutive repetition of current active cluster
        if self._current_cluster is not None and self._current_cluster.signature == sig:
            self._current_cluster.add_repeat(line)
            self.stats.suppressed_lines += 1
            return

        # Multi-pattern check: signature matches an existing active cluster
        if sig in self._active_clusters:
            cluster = self._active_clusters[sig]
            cluster.add_repeat(line)
            self.stats.suppressed_lines += 1
            self._current_cluster = cluster
            return

        # Brand new pattern:
        # Flush previous burst if threshold reached
        if self._current_cluster is not None and self._current_cluster.count >= (
            self.config.threshold - 1
        ):
            yield from self._flush_cluster(self._current_cluster)

        # Cap active cluster pool to avoid memory leaks on unbounded distinct signatures
        if len(self._active_clusters) >= 200:
            oldest_sig = next(iter(self._active_clusters))
            yield from self._flush_cluster(self._active_clusters[oldest_sig])

        new_cluster = LogCluster(signature=sig, summary=summary, initial_line=line)
        self._active_clusters[sig] = new_cluster
        self._current_cluster = new_cluster
        self.stats.passed_lines += 1
        yield self.formatter.format_regular_line(line)

    def finalize(self) -> Generator[str, None, None]:
        """Flushes any remaining buffered cluster or open incident at EOF."""
        # Flush open incident
        final_incident = self.detector.flush()
        if final_incident is not None:
            self.stats.incident_count += 1
            self.stats.passed_lines += len(final_incident.lines)
            self.stats.incident_lines += len(final_incident.lines)
            yield from self._flush_all_clusters()
            yield self.formatter.format_incident(final_incident)
        else:
            yield from self._flush_all_clusters()

        import time

        self.stats.end_time = time.time()

    def _flush_cluster(self, cluster: LogCluster) -> Generator[str, None, None]:
        """Emits badge if repeats exceeded threshold, or unspools lines if below."""
        if cluster.signature in self._active_clusters:
            del self._active_clusters[cluster.signature]
        if self._current_cluster is cluster:
            self._current_cluster = None

        if cluster.count == 0:
            return

        # Check threshold
        if cluster.count >= (self.config.threshold - 1):
            badge = self.formatter.format_badge(
                count=cluster.count + 1,
                summary=cluster.summary,
                last_seen=cluster.last_seen,
                badge_format=self.config.badge_format,
            )
            yield badge
        else:
            # Below threshold: emit buffered lines
            for buffered_line in cluster.buffered_lines:
                self.stats.passed_lines += 1
                self.stats.suppressed_lines -= 1
                yield self.formatter.format_regular_line(buffered_line)

    def _flush_all_clusters(self) -> Generator[str, None, None]:
        """Flushes all currently active clusters."""
        clusters = list(self._active_clusters.values())
        for c in clusters:
            yield from self._flush_cluster(c)

    @property
    def detected_incidents(self) -> list[Incident]:
        """Returns all collected incidents."""
        return self.detector.all_incidents
