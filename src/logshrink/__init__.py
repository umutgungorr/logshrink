"""LogShrink: A zero-config CLI that deduplicates repetitive polling noise
and auto-highlights real errors in live terminal logs.
"""

__version__ = "1.0.0"
__author__ = "Umut Güngör"
__license__ = "MIT"

from logshrink.aggregator import LogAggregator
from logshrink.config import LogLevel, Preset, ShrinkConfig
from logshrink.detector import Incident, IncidentDetector
from logshrink.formatter import AnsiFormatter
from logshrink.normalizer import Normalizer

__all__ = [
    "AnsiFormatter",
    "Incident",
    "IncidentDetector",
    "LogAggregator",
    "LogLevel",
    "Normalizer",
    "Preset",
    "ShrinkConfig",
    "__version__",
]
