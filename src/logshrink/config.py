"""Configuration models, enums, and data containers for LogShrink."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field


class LogLevel(str, enum.Enum):
    """Normalized log severity levels."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARN = "WARN"
    WARNING = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    PANIC = "PANIC"

    @property
    def is_error(self) -> bool:
        return self in (
            LogLevel.ERROR,
            LogLevel.CRITICAL,
            LogLevel.FATAL,
            LogLevel.PANIC,
        )

    @property
    def is_warning(self) -> bool:
        return self in (LogLevel.WARN, LogLevel.WARNING)


class Preset(str, enum.Enum):
    """Presets for common log stream formats."""

    AUTO = "auto"
    DOCKER = "docker"
    JSON = "json"
    WEB = "web"
    RAW = "raw"


@dataclass
class ShrinkConfig:
    """Runtime configuration for LogShrink."""

    threshold: int = 2
    window: float = 5.0
    preset: Preset = Preset.AUTO
    errors_only: bool = False
    color: bool = True
    export_path: str | None = None
    copy_to_clipboard: bool = False
    show_stats: bool = True
    follow: bool = False
    ignore_patterns: list[str] = field(default_factory=list)
    suppress_polling: bool = True
    badge_format: str = ""

    def should_suppress_non_error(self) -> bool:
        return self.errors_only


@dataclass
class Incident:
    """Represents a detected error or multi-line exception/stack trace."""

    id: int
    title: str
    timestamp: str
    level: str
    lines: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    occurrences: int = 1
    fingerprint: str = ""

    def summary(self) -> str:
        first = self.lines[0].strip() if self.lines else self.title
        return f"{self.level}: {first[:80]}"


@dataclass
class ShrinkStats:
    """Statistics tracking for log deduplication."""

    total_lines: int = 0
    passed_lines: int = 0
    suppressed_lines: int = 0
    incident_count: int = 0
    incident_lines: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    @property
    def reduction_percentage(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return (self.suppressed_lines / self.total_lines) * 100.0

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time if self.end_time is not None else time.time()
        return max(0.001, end - self.start_time)

    @property
    def lines_per_second(self) -> float:
        return self.total_lines / self.elapsed_seconds
