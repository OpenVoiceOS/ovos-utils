# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import os
import unittest
from pathlib import Path
from unittest.mock import patch


class TestXDGUtils(unittest.TestCase):
    def test_xdg_cache_home_default(self):
        from ovos_utils.xdg_utils import xdg_cache_home
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_CACHE_HOME", None)
            result = xdg_cache_home()
        self.assertIsInstance(result, Path)
        self.assertTrue(result.is_absolute())

    def test_xdg_cache_home_from_env(self):
        from ovos_utils.xdg_utils import xdg_cache_home
        with patch.dict(os.environ, {"XDG_CACHE_HOME": "/tmp/test_cache"}):
            result = xdg_cache_home()
        self.assertEqual(result, Path("/tmp/test_cache"))

    def test_xdg_cache_home_relative_ignored(self):
        from ovos_utils.xdg_utils import xdg_cache_home
        with patch.dict(os.environ, {"XDG_CACHE_HOME": "relative/path"}):
            result = xdg_cache_home()
        # Relative path should be ignored, return default
        self.assertNotEqual(result, Path("relative/path"))
        self.assertTrue(result.is_absolute())

    def test_xdg_config_home_default(self):
        from ovos_utils.xdg_utils import xdg_config_home
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_CONFIG_HOME", None)
            result = xdg_config_home()
        self.assertIsInstance(result, Path)
        self.assertTrue(result.is_absolute())

    def test_xdg_config_home_from_env(self):
        from ovos_utils.xdg_utils import xdg_config_home
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test_config"}):
            result = xdg_config_home()
        self.assertEqual(result, Path("/tmp/test_config"))

    def test_xdg_data_home_default(self):
        from ovos_utils.xdg_utils import xdg_data_home
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_DATA_HOME", None)
            result = xdg_data_home()
        self.assertIsInstance(result, Path)
        self.assertTrue(result.is_absolute())

    def test_xdg_data_home_from_env(self):
        from ovos_utils.xdg_utils import xdg_data_home
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/test_data"}):
            result = xdg_data_home()
        self.assertEqual(result, Path("/tmp/test_data"))

    def test_xdg_data_dirs_default(self):
        from ovos_utils.xdg_utils import xdg_data_dirs
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_DATA_DIRS", None)
            result = xdg_data_dirs()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        for p in result:
            self.assertIsInstance(p, Path)

    def test_xdg_data_dirs_from_env(self):
        from ovos_utils.xdg_utils import xdg_data_dirs
        with patch.dict(os.environ, {"XDG_DATA_DIRS": "/tmp/data1:/tmp/data2"}):
            result = xdg_data_dirs()
        self.assertEqual(result, [Path("/tmp/data1"), Path("/tmp/data2")])

    def test_xdg_data_dirs_relative_ignored(self):
        from ovos_utils.xdg_utils import xdg_data_dirs
        with patch.dict(os.environ, {"XDG_DATA_DIRS": "/tmp/abs:relative/path"}):
            result = xdg_data_dirs()
        # Only absolute paths should be returned
        self.assertEqual(result, [Path("/tmp/abs")])

    def test_xdg_config_dirs_default(self):
        from ovos_utils.xdg_utils import xdg_config_dirs
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_CONFIG_DIRS", None)
            result = xdg_config_dirs()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_xdg_config_dirs_from_env(self):
        from ovos_utils.xdg_utils import xdg_config_dirs
        with patch.dict(os.environ, {"XDG_CONFIG_DIRS": "/tmp/cfg1:/tmp/cfg2"}):
            result = xdg_config_dirs()
        self.assertEqual(result, [Path("/tmp/cfg1"), Path("/tmp/cfg2")])

    def test_xdg_runtime_dir_default(self):
        from ovos_utils.xdg_utils import xdg_runtime_dir
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_RUNTIME_DIR", None)
            result = xdg_runtime_dir()
        self.assertIsNone(result)

    def test_xdg_runtime_dir_from_env(self):
        from ovos_utils.xdg_utils import xdg_runtime_dir
        with patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/tmp/runtime"}):
            result = xdg_runtime_dir()
        self.assertEqual(result, Path("/tmp/runtime"))

    def test_xdg_runtime_dir_relative_ignored(self):
        from ovos_utils.xdg_utils import xdg_runtime_dir
        with patch.dict(os.environ, {"XDG_RUNTIME_DIR": "relative/path"}):
            result = xdg_runtime_dir()
        self.assertIsNone(result)

    def test_xdg_state_home_default(self):
        from ovos_utils.xdg_utils import xdg_state_home
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_STATE_HOME", None)
            result = xdg_state_home()
        self.assertIsInstance(result, Path)
        self.assertTrue(result.is_absolute())

    def test_xdg_state_home_from_env(self):
        from ovos_utils.xdg_utils import xdg_state_home
        with patch.dict(os.environ, {"XDG_STATE_HOME": "/tmp/state"}):
            result = xdg_state_home()
        self.assertEqual(result, Path("/tmp/state"))

    def test_xdg_empty_env_uses_default(self):
        from ovos_utils.xdg_utils import xdg_cache_home
        with patch.dict(os.environ, {"XDG_CACHE_HOME": ""}):
            result = xdg_cache_home()
        # Empty string should use default
        self.assertTrue(result.is_absolute())
        self.assertNotEqual(str(result), "")


if __name__ == "__main__":
    unittest.main()
