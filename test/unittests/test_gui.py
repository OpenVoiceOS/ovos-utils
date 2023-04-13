import unittest
from mock import patch, call


class TestGui(unittest.TestCase):
    @patch("ovos_utils.gui.has_screen")
    def test_can_display(self, has_screen):
        from ovos_utils.gui import can_display
        has_screen.return_value = False
        self.assertFalse(can_display())
        has_screen.return_value = True
        self.assertTrue(can_display())
        has_screen.return_value = None
        self.assertFalse(can_display())

    @patch("ovos_utils.gui.is_installed")
    def test_is_gui_installed(self, is_installed):
        from ovos_utils.gui import is_gui_installed
        is_installed.return_value = False
        self.assertFalse(is_gui_installed())
        is_installed.assert_has_calls([call("mycroft-gui-app"),
                                       call("ovos-shell"),
                                       call("mycroft-embedded-shell"),
                                       call("plasmashell")])
        is_installed.return_value = True
        self.assertTrue(is_gui_installed())
        is_installed.assert_called_with("mycroft-gui-app")

        # Test passed applications
        self.assertTrue(is_gui_installed(["test"]))
        is_installed.assert_called_with("test")

    @patch("ovos_utils.gui.is_process_running")
    def test_is_gui_running(self, is_running):
        from ovos_utils.gui import is_gui_running
        is_running.return_value = False
        self.assertFalse(is_gui_running())
        is_running.assert_has_calls([call("mycroft-gui-app"),
                                     call("ovos-shell"),
                                     call("mycroft-embedded-shell"),
                                     call("plasmashell")])
        is_running.return_value = True
        self.assertTrue(is_gui_running())
        is_running.assert_called_with("mycroft-gui-app")

        # Test passed applications
        self.assertTrue(is_gui_running(["test"]))
        is_running.assert_called_with("test")

    def test_is_gui_connected(self):
        from ovos_utils.gui import is_gui_connected
        # TODO

    def test_can_use_local_gui(self):
        from ovos_utils.gui import can_use_local_gui
        # TODO

    def test_can_use_gui(self):
        from ovos_utils.gui import can_use_gui
        # TODO

    def test_extend_about_data(self):
        from ovos_utils.gui import extend_about_data
        # TODO

    def test_gui_widgets(self):
        from ovos_utils.gui import GUIWidgets
        # TODO

    def test_gui_tracker(self):
        from ovos_utils.gui import GUITracker
        # TODO

    def test_gui_dict(self):
        from ovos_utils.gui import _GUIDict
        # TODO

    def test_gui_interface(self):
        from ovos_utils.gui import GUIInterface
        # TODO
