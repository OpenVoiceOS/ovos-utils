# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import os
import tempfile
import unittest
from unittest.mock import patch


class TestEnsureDirectoryExists(unittest.TestCase):
    def test_creates_directory(self):
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base:
            target = os.path.join(base, "new_dir")
            result = ensure_directory_exists(target)
            self.assertTrue(os.path.isdir(result))
            self.assertEqual(os.path.normpath(result), os.path.normpath(target))

    def test_existing_directory_ok(self):
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base:
            result = ensure_directory_exists(base)
            self.assertTrue(os.path.isdir(result))

    def test_with_domain(self):
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base:
            result = ensure_directory_exists(base, domain="test_domain")
            expected = os.path.join(base, "test_domain")
            self.assertTrue(os.path.isdir(result))
            self.assertEqual(os.path.normpath(result), os.path.normpath(expected))

    def test_expands_home(self):
        from ovos_utils.file_utils import ensure_directory_exists
        with patch("os.makedirs") as mock_makedirs, \
             patch("os.path.isdir", return_value=True):
            result = ensure_directory_exists("~/testdir")
            self.assertNotIn("~", result)

    def test_returns_string(self):
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base:
            result = ensure_directory_exists(base)
            self.assertIsInstance(result, str)


class TestToAlnum(unittest.TestCase):
    def test_alphanumeric_unchanged(self):
        from ovos_utils.file_utils import to_alnum
        self.assertEqual(to_alnum("hello123"), "hello123")

    def test_hyphens_replaced(self):
        from ovos_utils.file_utils import to_alnum
        result = to_alnum("my-skill-id")
        self.assertEqual(result, "my_skill_id")

    def test_dots_replaced(self):
        from ovos_utils.file_utils import to_alnum
        result = to_alnum("my.skill.id")
        self.assertEqual(result, "my_skill_id")

    def test_spaces_replaced(self):
        from ovos_utils.file_utils import to_alnum
        result = to_alnum("my skill id")
        self.assertEqual(result, "my_skill_id")

    def test_empty_string(self):
        from ovos_utils.file_utils import to_alnum
        self.assertEqual(to_alnum(""), "")

    def test_all_special_chars(self):
        from ovos_utils.file_utils import to_alnum
        result = to_alnum("!@#$%")
        self.assertEqual(result, "_____")

    def test_converts_to_str(self):
        from ovos_utils.file_utils import to_alnum
        result = to_alnum(12345)
        self.assertEqual(result, "12345")


class TestGetTempPath(unittest.TestCase):
    def test_no_args_returns_tmp(self):
        from ovos_utils.file_utils import get_temp_path
        result = get_temp_path()
        self.assertIsInstance(result, str)
        self.assertTrue(os.path.isdir(result))

    def test_single_arg(self):
        from ovos_utils.file_utils import get_temp_path
        result = get_temp_path("mydir")
        self.assertIsInstance(result, str)
        self.assertIn("mydir", result)

    def test_multiple_args(self):
        from ovos_utils.file_utils import get_temp_path
        result = get_temp_path("mydir", "subdir", "file.wav")
        self.assertIn("mydir", result)
        self.assertIn("subdir", result)
        self.assertIn("file.wav", result)

    def test_invalid_arg_raises_type_error(self):
        from ovos_utils.file_utils import get_temp_path
        with self.assertRaises(TypeError):
            get_temp_path(None)

    def test_result_is_under_tmpdir(self):
        from ovos_utils.file_utils import get_temp_path
        result = get_temp_path("testfolder")
        self.assertTrue(result.startswith(tempfile.gettempdir()))


class TestGetCacheDirectory(unittest.TestCase):
    def test_returns_string(self):
        from ovos_utils.file_utils import get_cache_directory
        result = get_cache_directory("test_cache")
        self.assertIsInstance(result, str)

    def test_directory_created(self):
        from ovos_utils.file_utils import get_cache_directory
        result = get_cache_directory("test_cache_unique_xyz")
        self.assertTrue(os.path.isdir(result))

    def test_subdirectory(self):
        from ovos_utils.file_utils import get_cache_directory
        result = get_cache_directory("test/sub/dir")
        self.assertTrue(os.path.isdir(result))

    def test_folder_name_in_path(self):
        from ovos_utils.file_utils import get_cache_directory
        result = get_cache_directory("mycache")
        self.assertIn("mycache", result)


class TestEnsureDirectoryRace(unittest.TestCase):
    def test_directory_created_by_another_process(self):
        from ovos_utils.file_utils import ensure_directory_exists
        real_makedirs = os.makedirs

        def lose_race(path, mode=0o777, exist_ok=False):
            os.mkdir(path)  # the other process wins between check and create
            return real_makedirs(path, mode, exist_ok=exist_ok)

        with tempfile.TemporaryDirectory() as base, \
                patch("os.makedirs", side_effect=lose_race), \
                patch("ovos_utils.file_utils.LOG") as log:
            target = os.path.join(base, "shared")
            result = ensure_directory_exists(target)
            self.assertEqual(result, target)
            self.assertTrue(os.path.isdir(target))
        log.warning.assert_not_called()


class TestEnsureDirectoryExisting(unittest.TestCase):
    def test_existing_directory_leaves_umask_alone(self):
        from ovos_utils.file_utils import ensure_directory_exists
        with tempfile.TemporaryDirectory() as base, \
                patch("os.umask") as umask:
            self.assertEqual(ensure_directory_exists(base), base)
        umask.assert_not_called()


if __name__ == "__main__":
    unittest.main()
