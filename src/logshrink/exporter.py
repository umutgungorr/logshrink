"""Incident report markdown exporter and system clipboard integration."""

from __future__ import annotations

import datetime
import os
import platform
import subprocess

from logshrink.config import Incident, ShrinkStats


class Exporter:
    """Exports detected incidents into Markdown reports and clipboard."""

    @staticmethod
    def generate_markdown(
        incidents: list[Incident],
        stats: ShrinkStats,
        source_name: str = "Stream",
    ) -> str:
        """Generates a GitHub-flavored Markdown report of all captured incidents."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pct = stats.reduction_percentage

        lines = [
            "# 🚨 LogShrink Incident & Noise Reduction Report",
            "",
            f"- **Generated At**: `{now}`",
            f"- **Source**: `{source_name}`",
            f"- **Total Lines Processed**: `{stats.total_lines:,}`",
            f"- **Noise Suppressed**: `{stats.suppressed_lines:,} ({pct:.1f}%)`",
            f"- **Unique Incidents Detected**: `{len(incidents)}`",
            "",
            "## 📊 Incident Overview",
            "",
            "| ID | Level | Occurrences | First Seen | Last Seen | Summary |",
            "|---|---|---|---|---|---|",
        ]

        if not incidents:
            lines.append("| - | - | 0 | - | - | *No error incidents detected* |")
        else:
            for inc in incidents:
                summary = inc.summary().replace("|", "\\|")
                lines.append(
                    f"| #{inc.id} | **{inc.level}** | {inc.occurrences}x | "
                    f"`{inc.first_seen}` | `{inc.last_seen}` | `{summary[:60]}` |"
                )

        lines.extend(["", "---", "", "## 🔍 Detailed Incident Logs", ""])

        if not incidents:
            lines.append("✅ Clean run! No errors or unhandled exceptions encountered.")
        else:
            for inc in incidents:
                lines.append(f"### Incident #{inc.id} — {inc.level} ({inc.occurrences}x)")
                lines.append(f"- **First Seen**: `{inc.first_seen}`")
                lines.append(f"- **Last Seen**: `{inc.last_seen}`")
                lines.append("")
                lines.append("```log")
                lines.extend(inc.lines)
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def save_markdown(
        incidents: list[Incident],
        stats: ShrinkStats,
        destination_path: str,
        source_name: str = "Stream",
    ) -> bool:
        """Saves generated Markdown report to a file path."""
        try:
            content = Exporter.generate_markdown(incidents, stats, source_name)
            dirname = os.path.dirname(destination_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(destination_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"LogShrink Warning: Failed to export report to '{destination_path}': {e}")
            return False

    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """Copies text to the system clipboard using native utilities or pyperclip."""
        # 1. Try pyperclip if available
        try:
            import pyperclip  # type: ignore

            pyperclip.copy(text)
            return True
        except ImportError:
            pass
        except Exception:
            pass

        # 2. Native OS clipboard command
        os_name = platform.system()
        try:
            if os_name == "Windows":
                # Use clip.exe
                p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
                p.communicate(input=text.encode("utf-16le"))
                return p.returncode == 0
            elif os_name == "Darwin":
                # macOS pbcopy
                p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                return p.returncode == 0
            else:
                # Linux wl-copy or xclip
                for cmd in [
                    ["wl-copy"],
                    ["xclip", "-selection", "clipboard"],
                    ["xsel", "--clipboard", "--input"],
                ]:
                    try:
                        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                        p.communicate(input=text.encode("utf-8"))
                        if p.returncode == 0:
                            return True
                    except FileNotFoundError:
                        continue
        except Exception:
            pass

        return False
