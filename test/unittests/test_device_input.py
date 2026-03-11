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

"""Unit tests for ovos_utils.device_input module."""

import sys
import types
import unittest
from unittest import mock
from unittest.mock import Mock, MagicMock, patch

# distutils was removed in Python 3.12+; provide a minimal stub
if "distutils" not in sys.modules:
    distutils_stub = types.ModuleType("distutils")
    spawn_stub = types.ModuleType("distutils.spawn")
    spawn_stub.find_executable = lambda x: None
    distutils_stub.spawn = spawn_stub
    sys.modules["distutils"] = distutils_stub
    sys.modules["distutils.spawn"] = spawn_stub


class TestInputDeviceHelper(unittest.TestCase):
    """Tests for InputDeviceHelper class."""

    @patch("distutils.spawn.find_executable", return_value=None)
    def test_init_no_executables(self, mock_find: MagicMock) -> None:
        """InputDeviceHelper should initialise with empty device lists."""
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        self.assertEqual(helper.libinput_devices_list, [])
        self.assertEqual(helper.xinput_devices_list, [])

    @patch("distutils.spawn.find_executable")
    @patch("subprocess.check_output")
    def test_build_libinput_devices_list(self, mock_output: MagicMock,
                                          mock_find: MagicMock) -> None:
        """_build_linput_devices_list should parse libinput output correctly."""
        mock_find.return_value = "/usr/bin/libinput"
        mock_output.return_value = (
            b"Device:     My Keyboard\n"
            b"Kernel:     /dev/input/event0\n"
            b"Group:      1\n"
            b"Capabilities: keyboard\n"
        )
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        helper._build_linput_devices_list()
        self.assertEqual(len(helper.libinput_devices_list), 1)
        dev = helper.libinput_devices_list[0]
        self.assertEqual(dev["Device"], "My Keyboard")
        self.assertIn("keyboard", dev["Capabilities"])

    @patch("distutils.spawn.find_executable")
    @patch("subprocess.check_output")
    def test_build_libinput_multiple_capabilities(self, mock_output: MagicMock,
                                                   mock_find: MagicMock) -> None:
        """_build_linput_devices_list should handle space-separated capabilities."""
        mock_find.return_value = "/usr/bin/libinput"
        mock_output.return_value = (
            b"Device:     Touchpad\n"
            b"Kernel:     /dev/input/event1\n"
            b"Group:      2\n"
            b"Capabilities: pointer gesture touch\n"
        )
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        helper._build_linput_devices_list()
        caps = helper.libinput_devices_list[0]["Capabilities"]
        self.assertIsInstance(caps, list)
        self.assertGreater(len(caps), 1)

    @patch("distutils.spawn.find_executable")
    @patch("subprocess.check_output", side_effect=Exception("libinput failed"))
    def test_get_libinput_devices_exception(self, mock_output: MagicMock,
                                              mock_find: MagicMock) -> None:
        """_get_libinput_devices_list should clear list and log on exception."""
        mock_find.side_effect = lambda x: "/usr/bin/libinput" if x == "libinput" else None
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        result = helper._get_libinput_devices_list()
        self.assertEqual(result, [])

    @patch("distutils.spawn.find_executable", return_value=None)
    def test_get_libinput_devices_no_executable(self, mock_find: MagicMock) -> None:
        """_get_libinput_devices_list should return empty list when libinput not found."""
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        result = helper._get_libinput_devices_list()
        self.assertEqual(result, [])

    @patch("distutils.spawn.find_executable")
    @patch("subprocess.check_output")
    def test_build_xinput_devices_list(self, mock_output: MagicMock,
                                        mock_find: MagicMock) -> None:
        """_build_xinput_devices_list should parse xinput output correctly."""
        mock_find.return_value = "/usr/bin/xinput"
        mock_output.return_value = (
            b"Virtual core pointer\n"
            b"\xe2\x86\xb3 SynPS/2 Synaptics TouchPad  id=12  [slave  pointer  (2)]\n"
            b"\xe2\x86\xb3 AT Translated Set 2 keyboard  id=13  [slave  keyboard (3)]\n"
        )
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        helper._build_xinput_devices_list()
        self.assertGreater(len(helper.xinput_devices_list), 0)

    @patch("distutils.spawn.find_executable")
    @patch("subprocess.check_output", side_effect=Exception("xinput failed"))
    def test_get_xinput_devices_exception(self, mock_output: MagicMock,
                                           mock_find: MagicMock) -> None:
        """_get_xinput_devices_list should clear list on exception."""
        mock_find.side_effect = lambda x: "/usr/bin/xinput" if x == "xinput" else None
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        result = helper._get_xinput_devices_list()
        self.assertEqual(result, [])

    @patch("ovos_utils.device_input.find_executable", return_value=None)
    def test_get_xinput_devices_no_executable(self, mock_find: MagicMock) -> None:
        """_get_xinput_devices_list should return empty list when xinput not found."""
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        result = helper._get_xinput_devices_list()
        self.assertEqual(result, [])

    @mock.patch("distutils.spawn.find_executable")
    def test_can_use_touch_mouse(self, find_exec: MagicMock) -> None:
        """can_use_touch_mouse should detect touch/mouse/tablet/pointer/gesture."""
        from ovos_utils.device_input import InputDeviceHelper
        find_exec.return_value = True
        dev_input = InputDeviceHelper()

        dev_input._build_linput_devices_list = Mock()
        dev_input._build_xinput_devices_list = Mock()

        dev_input.libinput_devices_list = [{"Device": "Mock",
                                             "Capabilities": ["mouse"]},
                                            {"Device": "Mock 1",
                                             "Capabilities": ["touch"]}
                                            ]
        self.assertTrue(dev_input.can_use_touch_mouse())

        dev_input.libinput_devices_list.pop()
        self.assertTrue(dev_input.can_use_touch_mouse())
        dev_input.libinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_touch_mouse())
        dev_input.xinput_devices_list = [{"Device": "xinput",
                                          "Capabilities": ["tablet"]
                                          }]
        self.assertTrue(dev_input.can_use_touch_mouse())
        dev_input.xinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_touch_mouse())

    @mock.patch("distutils.spawn.find_executable")
    def test_can_use_keyboard(self, find_exec: MagicMock) -> None:
        """can_use_keyboard should detect keyboard devices."""
        from ovos_utils.device_input import InputDeviceHelper
        find_exec.return_value = True
        dev_input = InputDeviceHelper()

        dev_input._build_linput_devices_list = Mock()
        dev_input._build_xinput_devices_list = Mock()

        dev_input.libinput_devices_list = [{"Device": "Mock",
                                             "Capabilities": ["keyboard"]},
                                            {"Device": "Mock 1",
                                             "Capabilities": ["touch"]}
                                            ]
        self.assertTrue(dev_input.can_use_keyboard())

        dev_input.libinput_devices_list.pop()
        self.assertTrue(dev_input.can_use_keyboard())
        dev_input.libinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_keyboard())
        dev_input.xinput_devices_list = [{"Device": "xinput",
                                          "Capabilities": ["keyboard"]
                                          }]
        self.assertTrue(dev_input.can_use_keyboard())
        dev_input.xinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_keyboard())

    @patch("distutils.spawn.find_executable", return_value=None)
    @patch("ovos_utils.device_input.is_gui_installed", return_value=True)
    def test_can_use_touch_mouse_no_executable_gui_installed(
            self, mock_gui: MagicMock, mock_find: MagicMock) -> None:
        """can_use_touch_mouse should return gui installed status when no executable."""
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        result = helper.can_use_touch_mouse()
        self.assertTrue(result)

    @patch("ovos_utils.device_input.find_executable", return_value=None)
    @patch("ovos_utils.device_input.is_gui_installed", return_value=False)
    def test_can_use_touch_mouse_no_executable_no_gui(
            self, mock_gui: MagicMock, mock_find: MagicMock) -> None:
        """can_use_touch_mouse should return False when no executable and no GUI."""
        from ovos_utils.device_input import InputDeviceHelper
        helper = InputDeviceHelper()
        result = helper.can_use_touch_mouse()
        self.assertFalse(result)

    @patch("distutils.spawn.find_executable")
    def test_get_input_device_list(self, mock_find: MagicMock) -> None:
        """get_input_device_list should combine libinput and xinput device lists."""
        from ovos_utils.device_input import InputDeviceHelper
        mock_find.return_value = True
        helper = InputDeviceHelper()
        helper._build_linput_devices_list = Mock()
        helper._build_xinput_devices_list = Mock()
        helper.libinput_devices_list = [{"Device": "A", "Capabilities": ["mouse"]}]
        helper.xinput_devices_list = [{"Device": "B", "Capabilities": ["keyboard"]}]
        result = helper.get_input_device_list()
        self.assertEqual(len(result), 2)


class TestModuleFunctions(unittest.TestCase):
    """Tests for module-level can_use_touch_mouse and can_use_keyboard."""

    @patch("ovos_utils.device_input.InputDeviceHelper")
    def test_module_can_use_touch_mouse(self, mock_helper_cls: MagicMock) -> None:
        """Module-level can_use_touch_mouse should delegate to InputDeviceHelper."""
        mock_helper_cls.return_value.can_use_touch_mouse.return_value = True
        from ovos_utils.device_input import can_use_touch_mouse
        result = can_use_touch_mouse()
        self.assertTrue(result)

    @patch("ovos_utils.device_input.InputDeviceHelper")
    def test_module_can_use_keyboard(self, mock_helper_cls: MagicMock) -> None:
        """Module-level can_use_keyboard should delegate to InputDeviceHelper."""
        mock_helper_cls.return_value.can_use_keyboard.return_value = False
        from ovos_utils.device_input import can_use_keyboard
        result = can_use_keyboard()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
