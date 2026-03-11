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

"""Unit tests for ovos_utils.gui module."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch


class TestCanDisplay(unittest.TestCase):
    """Tests for can_display."""

    @patch("ovos_utils.gui.has_screen", return_value=True)
    def test_returns_true_when_screen_present(self, _: MagicMock) -> None:
        """can_display should return True when has_screen() is True."""
        from ovos_utils.gui import can_display
        self.assertTrue(can_display())

    @patch("ovos_utils.gui.has_screen", return_value=False)
    def test_returns_false_when_no_screen(self, _: MagicMock) -> None:
        """can_display should return False when has_screen() is False."""
        from ovos_utils.gui import can_display
        self.assertFalse(can_display())


class TestIsGuiInstalled(unittest.TestCase):
    """Tests for is_gui_installed."""

    @patch("ovos_utils.gui.is_installed", return_value=True)
    def test_returns_true_when_app_installed(self, _: MagicMock) -> None:
        """is_gui_installed should return True when at least one GUI app is installed."""
        from ovos_utils.gui import is_gui_installed
        self.assertTrue(is_gui_installed())

    @patch("ovos_utils.gui.is_installed", return_value=False)
    def test_returns_false_when_no_app_installed(self, _: MagicMock) -> None:
        """is_gui_installed should return False when no GUI app is installed."""
        from ovos_utils.gui import is_gui_installed
        self.assertFalse(is_gui_installed())


class TestIsGuiRunning(unittest.TestCase):
    """Tests for is_gui_running."""

    @patch("ovos_utils.gui.is_process_running", return_value=True)
    def test_returns_true_when_running(self, _: MagicMock) -> None:
        """is_gui_running should return True when a GUI process is detected."""
        from ovos_utils.gui import is_gui_running
        self.assertTrue(is_gui_running())

    @patch("ovos_utils.gui.is_process_running", return_value=False)
    def test_returns_false_when_not_running(self, _: MagicMock) -> None:
        """is_gui_running should return False when no GUI process is running."""
        from ovos_utils.gui import is_gui_running
        self.assertFalse(is_gui_running())


class TestIsGuiConnected(unittest.TestCase):
    """Tests for is_gui_connected."""

    @patch("ovos_utils.gui.wait_for_reply")
    def test_returns_true_when_connected(self, mock_reply: MagicMock) -> None:
        """is_gui_connected should return True when response says connected."""
        mock_msg = MagicMock()
        mock_msg.data = {"connected": True}
        mock_reply.return_value = mock_msg
        from ovos_utils.gui import is_gui_connected
        result = is_gui_connected(bus=MagicMock())
        self.assertTrue(result)

    @patch("ovos_utils.gui.wait_for_reply")
    def test_returns_false_when_no_reply(self, mock_reply: MagicMock) -> None:
        """is_gui_connected should return False when no reply is received."""
        mock_reply.return_value = None
        from ovos_utils.gui import is_gui_connected
        result = is_gui_connected(bus=MagicMock())
        self.assertFalse(result)


class TestCanUseLocalGui(unittest.TestCase):
    """Tests for can_use_local_gui."""

    @patch("ovos_utils.gui.can_display", return_value=True)
    @patch("ovos_utils.gui.is_gui_installed", return_value=True)
    @patch("ovos_utils.gui.is_gui_running", return_value=True)
    def test_all_conditions_met(self, *_) -> None:
        """can_use_local_gui should return True when display, installed, and running."""
        from ovos_utils.gui import can_use_local_gui
        self.assertTrue(can_use_local_gui())

    @patch("ovos_utils.gui.can_display", return_value=False)
    @patch("ovos_utils.gui.is_gui_installed", return_value=True)
    @patch("ovos_utils.gui.is_gui_running", return_value=True)
    def test_no_display_returns_false(self, *_) -> None:
        """can_use_local_gui should return False when no display is available."""
        from ovos_utils.gui import can_use_local_gui
        self.assertFalse(can_use_local_gui())


class TestCanUseGui(unittest.TestCase):
    """Tests for can_use_gui."""

    @patch("ovos_utils.gui.can_use_local_gui", return_value=True)
    def test_local_flag_delegates_to_local(self, _: MagicMock) -> None:
        """can_use_gui with local=True should only check local GUI."""
        from ovos_utils.gui import can_use_gui
        result = can_use_gui(local=True)
        self.assertTrue(result)

    @patch("ovos_utils.gui.can_use_local_gui", return_value=False)
    @patch("ovos_utils.gui.is_gui_connected", return_value=True)
    def test_falls_back_to_connected(self, *_) -> None:
        """can_use_gui should return True when GUI is connected (even if not local)."""
        from ovos_utils.gui import can_use_gui
        result = can_use_gui(bus=MagicMock(), local=False)
        self.assertTrue(result)


class TestGetUiDirectories(unittest.TestCase):
    """Tests for get_ui_directories."""

    def test_legacy_ui_dir(self) -> None:
        """get_ui_directories should map qt5 for legacy 'ui' directory."""
        from ovos_utils.gui import get_ui_directories
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "ui"))
            result = get_ui_directories(root)
        self.assertIn("qt5", result)

    def test_modern_gui_dir(self) -> None:
        """get_ui_directories should discover framework subdirs under 'gui'."""
        from ovos_utils.gui import get_ui_directories
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "gui", "qt5"))
            os.makedirs(os.path.join(root, "gui", "kivy"))
            result = get_ui_directories(root)
        self.assertIn("qt5", result)
        self.assertIn("kivy", result)

    def test_no_ui_dirs(self) -> None:
        """get_ui_directories should return an empty dict when no UI directories exist."""
        from ovos_utils.gui import get_ui_directories
        with tempfile.TemporaryDirectory() as root:
            result = get_ui_directories(root)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
