"""CLI entry point and command-line interface implementation for LogShrink."""

from __future__ import annotations

import argparse
import contextlib
import os
import signal
import sys

from logshrink import __version__
from logshrink.aggregator import LogAggregator
from logshrink.config import Preset, ShrinkConfig
from logshrink.exporter import Exporter
from logshrink.formatter import AnsiFormatter
from logshrink.normalizer import Normalizer
from logshrink.streamer import Streamer


def create_parser() -> argparse.ArgumentParser:
    """Builds the argument parser for LogShrink."""
    parser = argparse.ArgumentParser(
        prog="logshrink",
        description="A zero-config CLI that deduplicates repetitive polling noise and auto-highlights real errors in live terminal logs.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Log file(s) to read. If omitted or '-', reads continuously from standard input.",
    )

    parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Follow file append operations in real time (like `tail -f`).",
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        default=2,
        help="Minimum identical/pattern occurrences required to suppress repetitions (default: 2).",
    )

    parser.add_argument(
        "-w",
        "--window",
        type=float,
        default=5.0,
        help="Time window in seconds for collapsing recurring patterns (default: 5.0).",
    )

    parser.add_argument(
        "-p",
        "--preset",
        choices=["auto", "docker", "json", "web", "raw"],
        default="auto",
        help="Log format preset for parsing (default: auto).\n"
        "  auto   : Autodetect JSON, Docker, or standard logs\n"
        "  docker : Strip container names and timestamps\n"
        "  json   : Parse structured JSON logs\n"
        "  web    : Optimized for Nginx/Apache/Caddy/uvicorn\n"
        "  raw    : Strict line-by-line exact match",
    )

    parser.add_argument(
        "-e",
        "--errors-only",
        action="store_true",
        help="Only display errors, warnings, and stack traces. Filter out all normal logs.",
    )

    parser.add_argument(
        "--export",
        metavar="PATH",
        type=str,
        default=None,
        help="Export all detected error incidents to a formatted Markdown report file.",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Write/append formatted Markdown incident report to $GITHUB_STEP_SUMMARY (for GitHub Actions).",
    )

    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy captured error incidents to the system clipboard upon exit.",
    )

    parser.add_argument(
        "-i",
        "--ignore",
        action="append",
        metavar="REGEX",
        default=[],
        help="Regex pattern to discard completely. Can be specified multiple times.",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI syntax highlighting and colors.",
    )

    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="Do not display the reduction statistics card on exit.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )

    return parser


def main():
    """CLI entrypoint."""
    sys.exit(run())


def run(args: list[str] | None = None) -> int:
    """Executes the LogShrink pipeline."""
    # Ensure UTF-8 output where supported
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = create_parser()
    parsed_args = parser.parse_args(args)

    preset_map = {
        "auto": Preset.AUTO,
        "docker": Preset.DOCKER,
        "json": Preset.JSON,
        "web": Preset.WEB,
        "raw": Preset.RAW,
    }

    config = ShrinkConfig(
        threshold=parsed_args.threshold,
        window=parsed_args.window,
        preset=preset_map[parsed_args.preset],
        errors_only=parsed_args.errors_only,
        color=not parsed_args.no_color,
        export_path=parsed_args.export,
        copy_to_clipboard=parsed_args.copy,
        show_stats=not parsed_args.no_stats,
        follow=parsed_args.follow,
        ignore_patterns=parsed_args.ignore,
    )

    # Determine files or stdin
    files = parsed_args.files
    if not files or files == ["-"]:
        files = None

    # Pre-validate files exist before initializing pipeline
    if files:
        for f in files:
            if not os.path.exists(f):
                print(f"Error: File not found: {f}", file=sys.stderr)
                return 1

    formatter = AnsiFormatter(color_enabled=config.color)
    normalizer = Normalizer(preset=config.preset)
    aggregator = LogAggregator(
        config=config,
        normalizer=normalizer,
        formatter=formatter,
    )

    source_label = ", ".join(files) if files else "stdin"
    interrupted = False

    def handle_sigint(signum, frame):
        nonlocal interrupted
        interrupted = True
        sys.stderr.write("\n")

    with contextlib.suppress(ValueError, AttributeError):
        signal.signal(signal.SIGINT, handle_sigint)

    try:
        stream = Streamer.get_stream(files=files, follow=config.follow)
        for line in stream:
            if interrupted:
                break
            for out in aggregator.process_line(line):
                print(out, flush=True)

    except (KeyboardInterrupt, BrokenPipeError):
        pass
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
    finally:
        # Final flush
        for out in aggregator.finalize():
            print(out, flush=True)

        incidents = aggregator.detected_incidents

        # Markdown Export if requested
        if config.export_path:
            Exporter.save_markdown(
                incidents=incidents,
                stats=aggregator.stats,
                destination_path=config.export_path,
                source_name=source_label,
            )

        # Step Summary if requested (e.g. GitHub Actions step summary)
        if parsed_args.summary:
            summary_env = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_env:
                Exporter.append_markdown(
                    incidents=incidents,
                    stats=aggregator.stats,
                    destination_path=summary_env,
                    source_name=source_label,
                )
            else:
                Exporter.save_markdown(
                    incidents=incidents,
                    stats=aggregator.stats,
                    destination_path="logshrink-summary.md",
                    source_name=source_label,
                )

        # Output GitHub Actions step outputs if running in CI
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with contextlib.suppress(Exception):
                with open(github_output, "a", encoding="utf-8") as gf:
                    gf.write(f"incident-count={len(incidents)}\n")
                    gf.write(f"reduced-percentage={aggregator.stats.reduction_percentage:.1f}\n")
                    gf.write(f"suppressed-lines={aggregator.stats.suppressed_lines}\n")
                    gf.write(f"total-lines={aggregator.stats.total_lines}\n")

        # Clipboard Copy if requested
        if config.copy_to_clipboard:
            report_text = Exporter.generate_markdown(
                incidents=incidents,
                stats=aggregator.stats,
                source_name=source_label,
            )
            success = Exporter.copy_to_clipboard(report_text)
            if success:
                count_msg = f"{len(incidents)} incidents" if incidents else "clean run report"
                print(f"[LogShrink] Copied {count_msg} to clipboard.", file=sys.stderr)
            else:
                print("[LogShrink] Warning: Clipboard utility unavailable.", file=sys.stderr)

        # Print stats card
        if config.show_stats:
            summary = formatter.format_summary_stats(
                aggregator.stats,
                export_file=config.export_path or "",
            )
            print(summary, file=sys.stderr)

    return 0


if __name__ == "__main__":
    main()
