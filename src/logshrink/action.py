"""GitHub Actions composite action runner entrypoint for LogShrink.

Safely parses GitHub Action inputs from environment variables to prevent shell
injection and avoid Windows path backslash corruption in composite action steps.
"""

from __future__ import annotations

import os
import shlex
import sys

from logshrink.cli import run


def main() -> int:
    """Parses GitHub Action inputs from environment variables and invokes LogShrink."""
    log_file = os.environ.get("INPUT_LOG_FILE", "").strip()
    summary_raw = os.environ.get("INPUT_SUMMARY", "true").strip().lower()
    summary = summary_raw in ("true", "1", "yes", "on")
    export_file = os.environ.get("INPUT_EXPORT_FILE", "").strip()
    options_raw = os.environ.get("INPUT_OPTIONS", "").strip()
    fail_on_error_raw = os.environ.get("INPUT_FAIL_ON_ERROR", "false").strip().lower()
    fail_on_error = fail_on_error_raw in ("true", "1", "yes", "on")

    if not log_file:
        print("Error: Missing required input 'log-file'.", file=sys.stderr)
        return 1

    args: list[str] = []

    if summary:
        args.append("--summary")

    if export_file:
        args.extend(["--export", export_file])

    if fail_on_error:
        args.append("--fail-on-error")

    if options_raw:
        try:
            parsed_opts = shlex.split(options_raw, posix=(os.name != "nt"))
        except Exception:
            parsed_opts = options_raw.split()
        args.extend(parsed_opts)

    args.append(log_file)

    return run(args)


if __name__ == "__main__":
    sys.exit(main())
