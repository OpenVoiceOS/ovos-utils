# Copyright 2024, OpenVoiceOS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for ovos_utils.log_parser module."""

import os
import tempfile
import unittest
import unittest.mock
from datetime import datetime


class TestLogLine(unittest.TestCase):
    """Tests for the LogLine dataclass."""

    def test_str_with_all_fields(self) -> None:
        """__str__ should format a full log line correctly."""
        from ovos_utils.log_parser import LogLine, TIME_FORMAT
        ts = datetime(2024, 1, 1, 12, 0, 0, 123456)
        ll = LogLine(timestamp=ts, source="skills", location="my_skill:handler:10",
                     level="INFO", message="Hello")
        s = str(ll)
        self.assertIn("skills", s)
        self.assertIn("INFO", s)
        self.assertIn("Hello", s)

    def test_str_without_source(self) -> None:
        """__str__ for a line with no source should return just the message."""
        from ovos_utils.log_parser import LogLine
        ll = LogLine(message="bare message")
        self.assertEqual(str(ll), "bare message")

    def test_format_timestamp_with_timestamp(self) -> None:
        """format_timestamp should return formatted string when timestamp is set."""
        from ovos_utils.log_parser import LogLine
        ts = datetime(2024, 6, 15, 9, 30, 0, 0)
        ll = LogLine(timestamp=ts)
        result = ll.format_timestamp()
        self.assertIn("2024-06-15", result)

    def test_format_timestamp_without_timestamp(self) -> None:
        """format_timestamp should return empty string when timestamp is None."""
        from ovos_utils.log_parser import LogLine
        ll = LogLine()
        self.assertEqual(ll.format_timestamp(), "")


class TestFrame(unittest.TestCase):
    """Tests for the Frame class."""

    def test_as_dict(self) -> None:
        """as_dict should return location, level, and message keys."""
        from ovos_utils.log_parser import Frame
        frame = Frame(
            filename="/usr/lib/python3.10/site-packages/my_package/module.py",
            lineno=42,
            name="my_function",
            line="    raise ValueError('oops')"
        )
        d = frame.as_dict()
        self.assertIn("location", d)
        self.assertIn("level", d)
        self.assertIn("message", d)
        self.assertEqual(d["level"], "TRACEBACK")

    def test_as_logline(self) -> None:
        """as_logline should return a LogLine instance."""
        from ovos_utils.log_parser import Frame, LogLine
        frame = Frame(
            filename="/usr/lib/python3.10/site-packages/my_pkg/mod.py",
            lineno=10,
            name="func",
            line="    x = 1"
        )
        ll = frame.as_logline()
        self.assertIsInstance(ll, LogLine)

    def test_format_location_site_packages(self) -> None:
        """format_location should extract package from site-packages path."""
        from ovos_utils.log_parser import Frame
        frame = Frame(
            filename="/home/user/.venv/lib/python3.10/site-packages/my_pkg/module.py",
            lineno=5,
            name="do_thing",
            line="    pass"
        )
        loc = frame.format_location()
        self.assertIn("my_pkg", loc)
        self.assertIn("module", loc)

    def test_format_location_bin_path(self) -> None:
        """format_location should handle /bin/ paths."""
        from ovos_utils.log_parser import Frame
        frame = Frame(
            filename="/usr/bin/my-script.py",
            lineno=1,
            name="main",
            line="    pass"
        )
        loc = frame.format_location()
        self.assertIn("my_script", loc)

    def test_str_representation(self) -> None:
        """__str__ should produce a traceback-style string."""
        from ovos_utils.log_parser import Frame
        frame = Frame(
            filename="/path/to/file.py",
            lineno=99,
            name="some_func",
            line="    raise Exception"
        )
        s = str(frame)
        self.assertIn("99", s)
        self.assertIn("some_func", s)


class TestTraceback(unittest.TestCase):
    """Tests for the Traceback class."""

    TRACEBACK_STR = (
        'Traceback (most recent call last):\n'
        '  File "/path/to/module.py", line 10, in handler\n'
        '    raise RuntimeError("bad")\n'
        'RuntimeError: bad\n'
    )

    def test_from_string(self) -> None:
        """from_string should parse frames and exception from a traceback string."""
        from ovos_utils.log_parser import Traceback
        tb = Traceback.from_string(self.TRACEBACK_STR)
        self.assertEqual(len(tb.frames), 1)
        self.assertIn("RuntimeError", tb.exception)

    def test_from_list(self) -> None:
        """from_list should work like from_string given a list of lines."""
        from ovos_utils.log_parser import Traceback
        lines = self.TRACEBACK_STR.splitlines(keepends=True)
        tb = Traceback.from_list(lines)
        self.assertGreater(len(tb.frames), 0)

    def test_to_loglines(self) -> None:
        """to_loglines should return a list of LogLine objects."""
        from ovos_utils.log_parser import Traceback, LogLine
        tb = Traceback.from_string(self.TRACEBACK_STR)
        ts = datetime(2024, 1, 1)
        tb.timestamp = ts
        log_lines = tb.to_loglines()
        self.assertIsInstance(log_lines, list)
        self.assertTrue(all(isinstance(ll, LogLine) for ll in log_lines))
        self.assertEqual(log_lines[0].level, "EXCEPTION")

    def test_exception_location(self) -> None:
        """exception_location should return location of last frame."""
        from ovos_utils.log_parser import Traceback
        tb = Traceback.from_string(self.TRACEBACK_STR)
        loc = tb.exception_location
        self.assertIsNotNone(loc)

    def test_str(self) -> None:
        """__str__ should produce a readable traceback string."""
        from ovos_utils.log_parser import Traceback
        tb = Traceback.from_string(self.TRACEBACK_STR)
        s = str(tb)
        self.assertIn("Traceback", s)
        self.assertIn("RuntimeError", s)

    def test_timestamp_property(self) -> None:
        """Traceback timestamp getter/setter should work correctly."""
        from ovos_utils.log_parser import Traceback
        tb = Traceback.from_string(self.TRACEBACK_STR)
        ts = datetime(2024, 3, 15, 10, 0)
        tb.timestamp = ts
        self.assertEqual(tb.timestamp, ts)


class TestOVOSLogParser(unittest.TestCase):
    """Tests for OVOSLogParser class methods."""

    VALID_LOG_LINE = (
        "2024-01-15 09:30:00.123456 - skills - my_skill:handler:42 - INFO - Skill started\n"
    )

    def test_parse_valid_line(self) -> None:
        """parse should correctly parse a standard OVOS log line."""
        from ovos_utils.log_parser import OVOSLogParser, LogLine
        result = OVOSLogParser.parse(self.VALID_LOG_LINE)
        self.assertIsInstance(result, LogLine)
        self.assertEqual(result.source, "skills")
        self.assertEqual(result.level, "INFO")
        self.assertIn("Skill started", result.message)

    def test_parse_invalid_line(self) -> None:
        """parse should return a LogLine with just the message for non-matching lines."""
        from ovos_utils.log_parser import OVOSLogParser, LogLine
        result = OVOSLogParser.parse("random non-log line\n")
        self.assertIsInstance(result, LogLine)
        self.assertIn("random non-log line", result.message)

    def test_parse_invalid_line_with_last_timestamp(self) -> None:
        """parse should propagate last_timestamp to non-matching lines."""
        from ovos_utils.log_parser import OVOSLogParser
        ts = datetime(2024, 5, 5)
        result = OVOSLogParser.parse("some system message\n", last_timestamp=ts)
        self.assertEqual(result.timestamp, ts)

    def test_parse_file_valid(self) -> None:
        """parse_file should yield LogLine objects from a valid log file."""
        from ovos_utils.log_parser import OVOSLogParser, LogLine

        content = (
            "2024-01-15 09:30:00.123456 - skills - my_skill:h:1 - INFO - Starting\n"
            "2024-01-15 09:30:01.000000 - skills - my_skill:h:2 - DEBUG - Running\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(content)
            fname = f.name

        try:
            results = list(OVOSLogParser.parse_file(fname))
            self.assertGreater(len(results), 0)
            for item in results:
                self.assertIsInstance(item, LogLine)
        finally:
            os.unlink(fname)

    def test_parse_file_with_traceback(self) -> None:
        """parse_file should yield Traceback objects when tracebacks are present."""
        from ovos_utils.log_parser import OVOSLogParser, Traceback

        content = (
            "2024-01-15 09:30:00.123456 - skills - sk:h:1 - ERROR - Error occurred\n"
            "Traceback (most recent call last):\n"
            '  File "/path/to/file.py", line 5, in run\n'
            "    raise ValueError('oops')\n"
            "ValueError: oops\n"
            "\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(content)
            fname = f.name

        try:
            results = list(OVOSLogParser.parse_file(fname))
            tb_items = [r for r in results if isinstance(r, Traceback)]
            self.assertGreater(len(tb_items), 0)
        finally:
            os.unlink(fname)

    def test_parse_file_not_found(self) -> None:
        """parse_file should raise FileNotFoundError for missing files."""
        from ovos_utils.log_parser import OVOSLogParser
        with self.assertRaises(FileNotFoundError):
            list(OVOSLogParser.parse_file("/nonexistent/path/file.log"))

    def test_parse_file_skips_blank_lines(self) -> None:
        """parse_file should skip lines that are just newlines."""
        from ovos_utils.log_parser import OVOSLogParser, LogLine

        content = (
            "2024-01-15 09:30:00.123456 - skills - sk:h:1 - INFO - Line one\n"
            "\n"
            "2024-01-15 09:30:01.000000 - skills - sk:h:2 - INFO - Line two\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(content)
            fname = f.name

        try:
            results = list(OVOSLogParser.parse_file(fname))
            log_lines = [r for r in results if isinstance(r, LogLine)]
            self.assertEqual(len(log_lines), 2)
        finally:
            os.unlink(fname)


class TestParseTime(unittest.TestCase):
    """Tests for the parse_time helper."""

    def test_valid_time_string(self) -> None:
        """parse_time should return a datetime for a valid string."""
        from ovos_utils.log_parser import parse_time
        result = parse_time("2024-01-15 09:30:00")
        self.assertIsInstance(result, datetime)

    def test_invalid_time_string(self) -> None:
        """parse_time should return None for an invalid string."""
        from ovos_utils.log_parser import parse_time
        result = parse_time("not_a_date")
        self.assertIsNone(result)


class TestGetTimestampedFilename(unittest.TestCase):
    """Tests for get_timestamped_filename helper."""

    def test_returns_string(self) -> None:
        """get_timestamped_filename should return a string path."""
        from ovos_utils.log_parser import get_timestamped_filename
        result = get_timestamped_filename("test", "log")
        self.assertIsInstance(result, str)
        self.assertIn("test_", result)
        self.assertTrue(result.endswith(".log"))

    def test_custom_basedir(self) -> None:
        """get_timestamped_filename should honour a custom basedir."""
        from ovos_utils.log_parser import get_timestamped_filename
        result = get_timestamped_filename("myfile", "txt", basedir="/tmp")
        self.assertTrue(result.startswith("/tmp"))

    def test_tilde_expanded(self) -> None:
        """get_timestamped_filename should expand ~ to the home directory."""
        from ovos_utils.log_parser import get_timestamped_filename
        result = get_timestamped_filename("file", "log", basedir="~")
        self.assertNotIn("~", result)


class TestValidLog(unittest.TestCase):
    """Tests for valid_log helper."""

    def test_valid_log_true(self) -> None:
        """valid_log should return True when all requested logs are available."""
        from ovos_utils.log_parser import valid_log
        with unittest.mock.patch(
            "ovos_utils.log_parser.get_available_logs", return_value=["bus", "skills"]
        ):
            self.assertTrue(valid_log(["bus"], ["/tmp"]))

    def test_valid_log_false(self) -> None:
        """valid_log should return False when a requested log is not available."""
        from ovos_utils.log_parser import valid_log
        with unittest.mock.patch(
            "ovos_utils.log_parser.get_available_logs", return_value=["bus"]
        ):
            self.assertFalse(valid_log(["nonexistent"], ["/tmp"]))


class TestParseTimeframe(unittest.TestCase):
    """Tests for parse_timeframe utility."""

    def test_start_none_uses_last_load_time(self) -> None:
        """parse_timeframe with start=None should call get_last_load_time."""
        from ovos_utils.log_parser import parse_timeframe
        fixed_dt = datetime(2024, 1, 1)
        with unittest.mock.patch("ovos_utils.log_parser.get_last_load_time",
                                 return_value=fixed_dt):
            start, end = parse_timeframe(None, None)
        self.assertEqual(start, fixed_dt)
        self.assertIsNotNone(end)

    def test_explicit_start_and_end(self) -> None:
        """parse_timeframe with explicit strings should parse both."""
        from ovos_utils.log_parser import parse_timeframe
        start, end = parse_timeframe("2024-01-01 00:00:00", "2024-01-01 12:00:00")
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertLess(start, end)

    def test_end_none_uses_now(self) -> None:
        """parse_timeframe with end=None should use datetime.now()."""
        from ovos_utils.log_parser import parse_timeframe
        fixed_start = datetime(2024, 1, 1)
        with unittest.mock.patch("ovos_utils.log_parser.get_last_load_time",
                                 return_value=fixed_start):
            start, end = parse_timeframe(None, None)
        self.assertGreater(end, fixed_start)

    def test_invalid_start_returns_none(self) -> None:
        """parse_timeframe with invalid start string should return None for start."""
        from ovos_utils.log_parser import parse_timeframe
        start, end = parse_timeframe("not_a_date", "2024-01-01")
        self.assertIsNone(start)


class TestGetLastLoadTime(unittest.TestCase):
    """Tests for get_last_load_time utility."""

    def test_returns_epoch_when_no_directory(self) -> None:
        """get_last_load_time should return epoch datetime when no log directory found."""
        from ovos_utils.log_parser import get_last_load_time
        with unittest.mock.patch("ovos_utils.log_parser.get_log_path", return_value=None):
            result = get_last_load_time()
        self.assertEqual(result, datetime.fromtimestamp(0))

    def test_reads_log_for_last_load(self) -> None:
        """get_last_load_time should parse skills.log to find last load time."""
        import tempfile
        import os
        from ovos_utils.log_parser import get_last_load_time

        log_content = (
            "2024-03-01 10:00:00.000000 - skills - sk:h:1 - INFO - Loading message bus configs\n"
            "2024-03-01 10:01:00.000000 - skills - sk:h:2 - INFO - Skills loaded\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "skills.log")
            with open(log_path, "w") as f:
                f.write(log_content)
            with unittest.mock.patch("ovos_utils.log_parser.get_log_path",
                                     return_value=tmpdir):
                result = get_last_load_time()
        self.assertIsInstance(result, datetime)
        self.assertGreater(result, datetime.fromtimestamp(0))


if __name__ == "__main__":
    unittest.main()
