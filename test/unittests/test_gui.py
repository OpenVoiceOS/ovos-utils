import unittest
from os.path import join, dirname
from threading import Event
from unittest.mock import patch, call

from ovos_bus_client.message import Message


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


class TestGuiInterface(unittest.TestCase):
    from ovos_utils.messagebus import FakeBus
    from ovos_utils.gui import GUIInterface
    bus = FakeBus()
    config = {"extension": "test"}
    ui_base_dir = join(dirname(__file__), "test_ui")
    ui_dirs = {'qt5': join(ui_base_dir, 'ui')}
    iface_name = "test_interface"
    interface = GUIInterface(iface_name, bus, None, config, ui_dirs)

    def test_00_gui_interface_init(self):
        self.assertEqual(self.interface.config, self.config)
        self.assertEqual(self.interface.bus, self.bus)
        self.assertIsNone(self.interface.remote_url)
        self.assertIsNone(self.interface.on_gui_changed_callback)
        self.assertEqual(self.interface.ui_directories, self.ui_dirs)
        self.assertEqual(self.interface.skill_id, self.iface_name)
        self.assertIsNone(self.interface.page)
        self.assertIsInstance(self.interface.connected, bool)

    def test_build_message_type(self):
        name = "test"
        self.assertEqual(self.interface.build_message_type(name),
                         f"{self.iface_name}.{name}")

        name = f"{self.iface_name}.{name}"
        self.assertEqual(self.interface.build_message_type(name), name)

    def test_setup_default_handlers(self):
        # TODO
        pass

    def test_upload_gui_pages(self):
        msg = None
        handled = Event()

        def on_pages(message):
            nonlocal msg
            msg = message
            handled.set()

        self.bus.once('gui.page.upload', on_pages)
        message = Message('test', {}, {'context': "Test"})
        self.interface.upload_gui_pages(message)
        self.assertTrue(handled.wait(10))

        self.assertEqual(msg.context['context'], message.context['context'])
        self.assertEqual(msg.msg_type, "gui.page.upload")
        self.assertEqual(msg.data['__from'], self.iface_name)
        self.assertEqual(msg.data['res_dir'], 'ui')

        pages = msg.data['pages']
        self.assertIsInstance(pages, dict)
        for key, val in pages.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, str)

        test_file_key = join(self.iface_name, "test.qml")
        self.assertEqual(pages.get(test_file_key), "Mock File Contents", pages)

        test_file_key = join(self.iface_name, "subdir", "test.qml")
        self.assertEqual(pages.get(test_file_key), "Nested Mock", pages)
        # TODO: Test other frameworks

    def test_register_handler(self):
        # TODO
        pass

    def test_set_on_gui_changed(self):
        # TODO
        pass

    def test_gui_set(self):
        # TODO
        pass

    def test_sync_data(self):
        # TODO
        pass

    def test_get(self):
        # TODO
        pass

    def test_clear(self):
        # TODO
        pass

    def test_send_event(self):
        # TODO
        pass

    def test_pages2uri(self):
        # TODO
        pass

    def test_show_page(self):
        # TODO
        pass

    def test_show_pages(self):
        # TODO
        pass

    def test_remove_page(self):
        # TODO
        pass

    def test_remove_pages(self):
        # TODO
        pass

    def test_show_notification(self):
        # TODO
        pass

    def test_show_controlled_notification(self):
        # TODO
        pass

    def test_remove_controlled_notification(self):
        # TODO
        pass

    def test_show_text(self):
        # TODO
        pass

    def test_show_image(self):
        # TODO
        pass

    def test_show_animated_image(self):
        # TODO
        pass

    def test_show_html(self):
        # TODO
        pass

    def test_show_url(self):
        # TODO
        pass

    def test_input_box(self):
        # TODO
        pass

    def test_release(self):
        # TODO
        pass

    def test_shutdown(self):
        # TODO
        pass
