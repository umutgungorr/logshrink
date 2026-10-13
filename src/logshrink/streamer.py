"""Stream readers for standard input, static files, and follow/tail modes."""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Generator


class Streamer:
    """Provides line generators from stdin, files, or follow/tail mode."""

    @staticmethod
    def stream_stdin() -> Generator[str, None, None]:
        """Reads lines continuously from sys.stdin."""
        try:
            yield from sys.stdin
        except (KeyboardInterrupt, BrokenPipeError):
            return

    @staticmethod
    def stream_file(filepath: str) -> Generator[str, None, None]:
        """Reads all lines from a static file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, encoding="utf-8", errors="replace") as f:
            yield from f

    @staticmethod
    def follow_file(filepath: str, poll_interval: float = 0.1) -> Generator[str, None, None]:
        """Follows additions to a file in real-time like `tail -f`.

        Handles file appending, rotation, and truncation gracefully.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, encoding="utf-8", errors="replace") as f:
            # First yield all existing lines
            for line in f:
                yield line

            # Keep following appended lines
            curr_pos = f.tell()
            curr_stat = os.fstat(f.fileno())

            try:
                while True:
                    line = f.readline()
                    if line:
                        if not line.endswith("\n"):
                            # Incomplete write: rewind and wait for remaining bytes
                            f.seek(curr_pos)
                            time.sleep(poll_interval)
                            continue
                        curr_pos = f.tell()
                        yield line
                    else:
                        time.sleep(poll_interval)
                        # Check truncation or rotation
                        try:
                            new_stat = os.stat(filepath)
                            if new_stat.st_size < curr_pos:
                                # File was truncated
                                f.seek(0)
                                curr_pos = 0
                                curr_stat = os.fstat(f.fileno())
                            elif (
                                hasattr(curr_stat, "st_ino") and new_stat.st_ino != curr_stat.st_ino
                            ):
                                # File was rotated
                                f.close()
                                f = open(filepath, encoding="utf-8", errors="replace")  # noqa: SIM115
                                curr_stat = os.fstat(f.fileno())
                                curr_pos = 0
                            else:
                                curr_pos = f.tell()
                        except FileNotFoundError:
                            pass
            except (KeyboardInterrupt, BrokenPipeError):
                return

    @classmethod
    def get_stream(
        cls,
        files: list[str] | None = None,
        follow: bool = False,
    ) -> Generator[str, None, None]:
        """Dispatches stream reader based on CLI flags."""
        if files:
            if follow and len(files) == 1:
                yield from cls.follow_file(files[0])
            else:
                for filepath in files:
                    yield from cls.stream_file(filepath)
        else:
            # Check if stdin has data or is piped
            yield from cls.stream_stdin()
