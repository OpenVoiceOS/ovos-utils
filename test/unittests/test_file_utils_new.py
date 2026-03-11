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

"""Additional unit tests for ovos_utils.file_utils module (coverage boost)."""

import collections
import os
import tempfile
import unittest
from unittest.mock import patch


class TestEnsureDirectoryExists(unittest.TestCase):
    """Tests for ensure_directory_exists."""

    def test_creates_new_directory(self) -> None:
        """ensure_directory_exists should create a directory if it doesn't exist."""
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base:
            new_dir = os.path.join(base, "new_subdir")
            result = ensure_directory_exists(new_dir)
            self.assertTrue(os.path.isdir(result))

    def test_with_domain(self) -> None:
        """ensure_directory_exists with domain should create base/domain path."""
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base:
            result = ensure_directory_exists(base, domain="mydomain")
            self.assertIn("mydomain", result)
            self.assertTrue(os.path.isdir(result))

    def test_existing_directory_returns_path(self) -> None:
        """ensure_directory_exists on an existing dir should return its path."""
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base:
            result = ensure_directory_exists(base)
            self.assertEqual(os.path.normpath(result), os.path.normpath(base))


class TestToAlnum(unittest.TestCase):
    """Tests for to_alnum."""

    def test_keeps_alphanumeric(self) -> None:
        """to_alnum should keep alphanumeric characters unchanged."""
        from ovos_utils.file_utils import to_alnum
        self.assertEqual(to_alnum("abc123"), "abc123")

    def test_replaces_special_chars(self) -> None:
        """to_alnum should replace non-alphanumeric chars with underscore."""
        from ovos_utils.file_utils import to_alnum
        result = to_alnum("my-skill.v1")
        self.assertNotIn("-", result)
        self.assertNotIn(".", result)
        self.assertIn("_", result)


class TestGetTempPath(unittest.TestCase):
    """Tests for get_temp_path."""

    def test_returns_string(self) -> None:
        """get_temp_path should return a string."""
        from ovos_utils.file_utils import get_temp_path
        self.assertIsInstance(get_temp_path("test"), str)

    def test_raises_type_error_on_bad_arg(self) -> None:
        """get_temp_path with non-string args should raise TypeError."""
        from ovos_utils.file_utils import get_temp_path
        with self.assertRaises(TypeError):
            get_temp_path(123)


class TestResolveOvosResourceFile(unittest.TestCase):
    """Tests for resolve_ovos_resource_file."""

    def test_returns_none_for_nonexistent(self) -> None:
        """Should return None when the resource doesn't exist anywhere."""
        from ovos_utils.file_utils import resolve_ovos_resource_file
        result = resolve_ovos_resource_file("definitely_not_a_real_resource.xyz")
        self.assertIsNone(result)

    def test_returns_path_for_fully_qualified_file(self) -> None:
        """Should return the path when given an existing absolute path."""
        from ovos_utils.file_utils import resolve_ovos_resource_file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name
        try:
            result = resolve_ovos_resource_file(fname)
            self.assertEqual(result, fname)
        finally:
            os.unlink(fname)

    def test_checks_extra_res_dirs(self) -> None:
        """Should find a resource in extra_res_dirs."""
        from ovos_utils.file_utils import resolve_ovos_resource_file
        with tempfile.TemporaryDirectory() as tmpdir:
            resource = "my_resource.txt"
            fpath = os.path.join(tmpdir, resource)
            with open(fpath, "w") as f:
                f.write("data")
            result = resolve_ovos_resource_file(resource, extra_res_dirs=[tmpdir])
        self.assertEqual(result, fpath)


class TestResolveResourceFile(unittest.TestCase):
    """Tests for resolve_resource_file."""

    def test_returns_none_when_not_found(self) -> None:
        """Should return None when resource is not found anywhere."""
        from ovos_utils.file_utils import resolve_resource_file
        with patch("ovos_utils.file_utils.log_deprecation"):
            result = resolve_resource_file(
                "this_resource_does_not_exist.xyz", config={}
            )
        self.assertIsNone(result)

    def test_returns_path_for_existing_file(self) -> None:
        """Should return the absolute path for an existing file."""
        from ovos_utils.file_utils import resolve_resource_file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name
        try:
            result = resolve_resource_file(fname, config={})
            self.assertEqual(result, fname)
        finally:
            os.unlink(fname)


class TestReadVocabFile(unittest.TestCase):
    """Tests for read_vocab_file."""

    def test_reads_plain_lines(self) -> None:
        """read_vocab_file should return lists of alternatives for each line."""
        from ovos_utils.file_utils import read_vocab_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("hello\n")
            f.write("hi\n")
            fname = f.name
        try:
            result = read_vocab_file(fname)
            self.assertEqual(len(result), 2)
        finally:
            os.unlink(fname)

    def test_skips_comments_and_blanks(self) -> None:
        """read_vocab_file should skip comment lines and blank lines."""
        from ovos_utils.file_utils import read_vocab_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("# comment\n")
            f.write("\n")
            f.write("hello\n")
            fname = f.name
        try:
            result = read_vocab_file(fname)
            self.assertEqual(len(result), 1)
        finally:
            os.unlink(fname)


class TestReadValueFile(unittest.TestCase):
    """Tests for read_value_file."""

    def test_reads_csv_pairs(self) -> None:
        """read_value_file should return an OrderedDict with key-value pairs."""
        from ovos_utils.file_utils import read_value_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("key1,value1\n")
            f.write("key2,value2\n")
            fname = f.name
        try:
            result = read_value_file(fname, ",")
            self.assertIsInstance(result, collections.OrderedDict)
            self.assertEqual(result["key1"], "value1")
            self.assertEqual(result["key2"], "value2")
        finally:
            os.unlink(fname)

    def test_skips_comments(self) -> None:
        """read_value_file should skip rows starting with #."""
        from ovos_utils.file_utils import read_value_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("# comment\n")
            f.write("key,value\n")
            fname = f.name
        try:
            result = read_value_file(fname, ",")
            self.assertNotIn("# comment", result)
            self.assertIn("key", result)
        finally:
            os.unlink(fname)

    def test_skips_wrong_column_count(self) -> None:
        """read_value_file should skip rows not having exactly 2 columns."""
        from ovos_utils.file_utils import read_value_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("only_one_column\n")
            f.write("too,many,columns,here\n")
            f.write("good,row\n")
            fname = f.name
        try:
            result = read_value_file(fname, ",")
            self.assertEqual(len(result), 1)
            self.assertIn("good", result)
        finally:
            os.unlink(fname)

    def test_returns_empty_when_filename_is_none(self) -> None:
        """read_value_file with None filename should return an empty OrderedDict."""
        from ovos_utils.file_utils import read_value_file
        result = read_value_file(None, ",")
        self.assertEqual(len(result), 0)


class TestReadTranslatedFile(unittest.TestCase):
    """Tests for read_translated_file."""

    def test_basic_substitution(self) -> None:
        """read_translated_file should substitute template variables."""
        from ovos_utils.file_utils import read_translated_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name}}!\n")
            fname = f.name
        try:
            result = read_translated_file(fname, {"name": "World"})
            self.assertIsInstance(result, list)
            self.assertIn("Hello World!", result)
        finally:
            os.unlink(fname)

    def test_returns_none_when_filename_is_none(self) -> None:
        """read_translated_file with None filename should return None."""
        from ovos_utils.file_utils import read_translated_file
        result = read_translated_file(None, {})
        self.assertIsNone(result)


class TestLoadVocabulary(unittest.TestCase):
    """Tests for load_vocabulary."""

    def test_loads_voc_files(self) -> None:
        """load_vocabulary should load all .voc files in a directory."""
        from ovos_utils.file_utils import load_vocabulary
        with tempfile.TemporaryDirectory() as tmpdir:
            voc_path = os.path.join(tmpdir, "greet.voc")
            with open(voc_path, "w") as f:
                f.write("hello\n")
                f.write("hi\n")
            result = load_vocabulary(tmpdir, "my_skill")
            self.assertTrue(any("greet" in k for k in result))

    def test_empty_directory_returns_empty_dict(self) -> None:
        """load_vocabulary in an empty directory should return {}."""
        from ovos_utils.file_utils import load_vocabulary
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_vocabulary(tmpdir, "skill_id")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
