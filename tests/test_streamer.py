"""Tests for streamer file reading and tail/follow modes."""

import pytest

from logshrink.streamer import Streamer


def test_stream_static_file(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

    lines = list(Streamer.stream_file(str(log_file)))
    assert lines == ["line 1\n", "line 2\n", "line 3\n"]


def test_stream_file_not_found():
    with pytest.raises(FileNotFoundError):
        list(Streamer.stream_file("non_existent_file.log"))


def test_follow_file_initial_and_appended(tmp_path):
    log_file = tmp_path / "follow.log"
    log_file.write_text("initial line\n", encoding="utf-8")

    # Read generator and simulate 1 follow step
    gen = Streamer.follow_file(str(log_file), poll_interval=0.01)
    line1 = next(gen)
    assert line1 == "initial line\n"

    # Append new line
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("appended line\n")

    line2 = next(gen)
    assert line2 == "appended line\n"

    # Close generator
    gen.close()
