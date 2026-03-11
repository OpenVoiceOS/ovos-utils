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

"""Unit tests for the deprecated ovos_utils.signal module."""

import os
import tempfile
import time
import types
import unittest
import warnings


class TestSignal(unittest.TestCase):
    """Tests for signal module functions (deprecated module)."""

    def _import_signal(self) -> types.ModuleType:
        """Import signal module suppressing the module-level DeprecationWarning."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import ovos_utils.signal as sig
        return sig

    def test_create_file(self) -> None:
        """create_file should create a file at the given path."""
        sig = self._import_signal()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "subdir", "testfile.txt")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                sig.create_file(filepath)
            self.assertTrue(os.path.isfile(filepath))

    def test_get_ipc_directory_with_config(self) -> None:
        """get_ipc_directory with explicit config should return a directory path."""
        sig = self._import_signal()
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"ipc_path": tmpdir}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                result = sig.get_ipc_directory(config=config)
            self.assertTrue(result.startswith(tmpdir))

    def test_get_ipc_directory_with_domain(self) -> None:
        """get_ipc_directory with domain should create a subdirectory."""
        sig = self._import_signal()
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"ipc_path": tmpdir}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                result = sig.get_ipc_directory(domain="test_domain", config=config)
            self.assertIn("test_domain", result)

    def test_get_ipc_directory_default_path(self) -> None:
        """get_ipc_directory with no ipc_path should use tmpdir/mycroft/ipc."""
        sig = self._import_signal()
        config = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = sig.get_ipc_directory(config=config)
        self.assertIn("mycroft", result)
        self.assertIn("ipc", result)

    def test_create_signal_returns_true_on_success(self) -> None:
        """create_signal should return True when signal file is created."""
        sig = self._import_signal()
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"ipc_path": tmpdir}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                result = sig.create_signal("test_signal", config=config)
            self.assertTrue(result)

    def test_check_for_signal_no_signal(self) -> None:
        """check_for_signal should return False when signal file does not exist."""
        sig = self._import_signal()
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"ipc_path": tmpdir}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                result = sig.check_for_signal("nonexistent_signal", config=config)
            self.assertFalse(result)

    def test_check_for_signal_single_use(self) -> None:
        """check_for_signal with sec_lifetime=0 should consume the signal file."""
        sig = self._import_signal()
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"ipc_path": tmpdir}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                sig.create_signal("single_use", config=config)
                result = sig.check_for_signal("single_use", sec_lifetime=0, config=config)
            self.assertTrue(result)
            # Signal should be consumed now
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                result2 = sig.check_for_signal("single_use", sec_lifetime=0, config=config)
            self.assertFalse(result2)

    def test_check_for_signal_permanent(self) -> None:
        """check_for_signal with sec_lifetime=-1 should never consume the signal."""
        sig = self._import_signal()
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"ipc_path": tmpdir}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                sig.create_signal("perm_signal", config=config)
                result1 = sig.check_for_signal("perm_signal", sec_lifetime=-1, config=config)
                result2 = sig.check_for_signal("perm_signal", sec_lifetime=-1, config=config)
            self.assertTrue(result1)
            self.assertTrue(result2)

    def test_module_raises_deprecation_warning(self) -> None:
        """Importing the signal module should raise a DeprecationWarning."""
        import sys
        # Remove cached module to force re-import
        sys.modules.pop("ovos_utils.signal", None)
        with self.assertWarns(DeprecationWarning):
            import ovos_utils.signal  # noqa: F401


if __name__ == "__main__":
    unittest.main()
