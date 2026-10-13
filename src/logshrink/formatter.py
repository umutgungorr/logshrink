"""ANSI syntax highlighting, terminal styling, and visual badge generator."""

from __future__ import annotations

import os
import re
import sys

from logshrink.config import Incident, ShrinkStats


class AnsiFormatter:
    """Formats terminal output with clean, high-contrast ANSI colors,

    supporting NO_COLOR standard and non-tty graceful degradation.
    """

    # ANSI Codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Foreground
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Bold Foreground
    B_RED = "\033[1;31m"
    B_GREEN = "\033[1;32m"
    B_YELLOW = "\033[1;33m"
    B_BLUE = "\033[1;34m"
    B_MAGENTA = "\033[1;35m"
    B_CYAN = "\033[1;36m"
    B_WHITE = "\033[1;37m"

    # Background
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_MAGENTA = "\033[45m"

    def __init__(self, color_enabled: bool = True):
        # Respect NO_COLOR env var (https://no-color.org/)
        no_color_env = os.environ.get("NO_COLOR", "").strip() != ""
        self.enabled = color_enabled and not no_color_env

        # Detect Unicode capability
        try:
            encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
            "┌─│└▲".encode(encoding)
            self.supports_unicode = True
        except Exception:
            self.supports_unicode = False

        self.box_tl = "┌" if self.supports_unicode else "+"
        self.box_h = "─" if self.supports_unicode else "-"
        self.box_v = "│" if self.supports_unicode else "|"
        self.box_bl = "└" if self.supports_unicode else "+"
        self.warn_sym = "▲" if self.supports_unicode else "*"

    def c(self, text: str, ansi_code: str) -> str:
        """Wraps text in ANSI escape code if color is enabled."""
        if not self.enabled:
            return text
        return f"{ansi_code}{text}{self.RESET}"

    def format_badge(
        self,
        count: int,
        summary: str,
        last_seen: str = "",
        badge_format: str | None = None,
    ) -> str:
        """Creates a counter badge for collapsed repetitive logs."""
        count_str = f"x{count}"
        if badge_format and "{count}" in badge_format:
            text = badge_format.format(
                count=count,
                summary=summary,
                last_seen=last_seen,
            )
            time_str = (
                f" (last seen {last_seen})"
                if (last_seen and "{last_seen}" not in badge_format)
                else ""
            )
            if self.enabled:
                return f"{self.CYAN}  [-] {self.B_CYAN}{text}{self.RESET}{self.GRAY}{time_str}{self.RESET}"
            return f"  [-] {text}{time_str}"

        if self.enabled:
            badge = f"{self.B_CYAN}[{count_str} suppressed]{self.RESET}"
            sum_str = f"{self.DIM}{summary}{self.RESET}"
            time_str = f" {self.GRAY}(last seen {last_seen}){self.RESET}" if last_seen else ""
            prefix = f"{self.CYAN}  [-] {self.RESET}"
            return f"{prefix}{badge} {sum_str}{time_str}"
        else:
            time_str = f" (last seen {last_seen})" if last_seen else ""
            return f"  [-] [{count_str} suppressed] {summary}{time_str}"

    def format_error_line(self, line: str) -> str:
        """Highlights a single error line."""
        if not self.enabled:
            return f"! {line}"
        return f"{self.B_RED}>>> {line}{self.RESET}"

    def format_warning_line(self, line: str) -> str:
        """Highlights a warning line in bold yellow."""
        if not self.enabled:
            return f"{self.warn_sym} {line}"
        return f"{self.B_YELLOW}{self.warn_sym} {line}{self.RESET}"

    def format_incident(self, incident: Incident) -> str:
        """Renders an incident box banner and syntax-highlighted stack trace."""
        lines_out: list[str] = []
        width = 72
        title = f" INCIDENT #{incident.id}: {incident.level} "
        if incident.occurrences > 1:
            title += f"({incident.occurrences}x) "

        banner_top = (
            (self.box_tl + (self.box_h * 2)) + title + (self.box_h * max(0, width - len(title) - 3))
        )
        banner_bot = self.box_bl + (self.box_h * (width - 1))

        if self.enabled:
            lines_out.append(f"{self.B_RED}{banner_top}{self.RESET}")
            for item_line in incident.lines:
                highlighted_line = self._syntax_highlight_trace(item_line)
                lines_out.append(f"{self.RED}{self.box_v}{self.RESET} {highlighted_line}")
            lines_out.append(f"{self.B_RED}{banner_bot}{self.RESET}")
        else:
            lines_out.append(banner_top)
            for item_line in incident.lines:
                lines_out.append(f"{self.box_v} {item_line}")
            lines_out.append(banner_bot)

        return "\n".join(lines_out)

    def _syntax_highlight_trace(self, line: str) -> str:
        """Applies syntax highlighting to trace paths, line numbers, and error types."""
        if not self.enabled:
            return line

        res = line
        # Highlight file paths and line numbers
        res = re.sub(
            r'File "([^"]+)", line (\d+)',
            rf'File "{self.B_CYAN}\1{self.RESET}", line {self.B_YELLOW}\2{self.RESET}',
            res,
        )
        # Highlight java at package.Class.method(Class.java:123)
        res = re.sub(
            r"(\([a-zA-Z0-9_]+\.java:)(\d+)(\))",
            rf"\1{self.B_YELLOW}\2{self.RESET}\3",
            res,
        )
        # Highlight Go /path/file.go:123
        res = re.sub(
            r"(/[^\s:]+\.go):(\d+)",
            rf"{self.B_CYAN}\1{self.RESET}:{self.B_YELLOW}\2{self.RESET}",
            res,
        )
        # Highlight Exception/Error keywords at start or end
        res = re.sub(
            r"\b([A-Za-z0-9_.]*(?:Error|Exception|Panic|Fault))(:|\b)",
            rf"{self.B_RED}\1{self.RESET}\2",
            res,
        )
        return res

    def format_regular_line(self, line: str) -> str:
        """Softly formats regular lines (e.g. dimming timestamp)."""
        if not self.enabled:
            return line

        # Softly dim leading timestamp if present
        m = re.match(r"^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s*(.*)", line)
        if m:
            ts, rest = m.groups()
            return f"{self.GRAY}{ts}{self.RESET} {rest}"
        return line

    def format_summary_stats(self, stats: ShrinkStats, export_file: str = "") -> str:
        """Builds the final terminal summary card."""
        pct = stats.reduction_percentage
        elapsed = stats.elapsed_seconds
        lines_per_sec = stats.lines_per_second

        sep = self.box_h * 58
        header = " LogShrink Summary "
        header_line = (self.box_h * 3) + header + (self.box_h * (58 - 3 - len(header)))

        pct_color = self.B_GREEN if pct > 50 else self.B_YELLOW

        lines = [
            f"{self.B_CYAN}{header_line}{self.RESET}" if self.enabled else header_line,
            f"  Total lines processed : {self.B_WHITE}{stats.total_lines:,}{self.RESET}"
            if self.enabled
            else f"  Total lines processed : {stats.total_lines:,}",
            f"  Lines passed through  : {stats.passed_lines:,}",
            f"  Lines suppressed      : {pct_color}{stats.suppressed_lines:,} ({pct:.1f}% noise reduced){self.RESET}"
            if self.enabled
            else f"  Lines suppressed      : {stats.suppressed_lines:,} ({pct:.1f}% noise reduced)",
            f"  Incidents captured    : {self.B_RED if stats.incident_count > 0 else self.GREEN}{stats.incident_count}{self.RESET}"
            if self.enabled
            else f"  Incidents captured    : {stats.incident_count}",
            f"  Processing time       : {elapsed:.2f}s ({lines_per_sec:,.0f} lines/sec)",
        ]

        if export_file:
            lines.append(
                f"  Incident report saved : {self.B_CYAN}{export_file}{self.RESET}"
                if self.enabled
                else f"  Incident report saved : {export_file}"
            )

        lines.append(f"{self.B_CYAN}{sep}{self.RESET}" if self.enabled else sep)
        return "\n".join(lines)
