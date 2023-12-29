import unittest
from os.path import join, dirname, isfile
from threading import Event
from unittest.mock import patch, call, Mock

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

    def test_get_ui_directories(self):
        from ovos_utils.gui import get_ui_directories
        test_dir = join(dirname(__file__), "test_ui")

        # gui dir (best practice)
        dirs = get_ui_directories(test_dir)
        self.assertEqual(dirs, {"all": join(test_dir, "gui")})

        # ui and uid dirs (legacy)
        dirs = get_ui_directories(join(test_dir, "legacy"))
        self.assertEqual(dirs, {"qt5": join(test_dir, "legacy", "ui")})


class TestGuiInterface(unittest.TestCase):
    from ovos_utils.fakebus import FakeBus
    from ovos_bus_client.apis.gui import GUIInterface
    bus = FakeBus()
    config = {"extension": "test"}
    ui_base_dir = join(dirname(__file__), "test_ui")
    ui_dirs = {'qt5': join(ui_base_dir, 'ui')}
    iface_name = "test_interface"

    volunteered_upload = Mock()
    bus.on('gui.volunteer_page_upload', volunteered_upload)

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
        self.volunteered_upload.assert_called_once()
        upload_message = self.volunteered_upload.call_args[0][0]
        self.assertEqual(upload_message.data["skill_id"], self.iface_name)

        # Test GUI init with no ui directories
        self.GUIInterface("no_ui_dirs_gui", self.bus, None, self.config)
        self.volunteered_upload.assert_called_once_with(upload_message)

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
        msg = Message("")
        handled = Event()

        def on_pages(message):
            nonlocal msg
            msg = message
            handled.set()

        self.bus.on('gui.page.upload', on_pages)

        # Upload default/legacy behavior (qt5 `ui` dir)
        message = Message('test', {}, {'context': "Test"})
        self.interface.upload_gui_pages(message)
        self.assertTrue(handled.wait(2))

        self.assertEqual(msg.context['context'], message.context['context'])
        self.assertEqual(msg.msg_type, "gui.page.upload")
        self.assertEqual(msg.data['__from'], self.iface_name)

        pages = msg.data['pages']
        self.assertIsInstance(pages, dict)
        for key, val in pages.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, str)

        test_file_key = "test.qml"
        self.assertEqual(bytes.fromhex(pages.get(test_file_key)),
                         b"Mock File Contents", pages)

        test_file_key = join("subdir", "test.qml")
        self.assertEqual(bytes.fromhex(pages.get(test_file_key)),
                         b"Nested Mock", pages)

        # Upload all resources
        handled.clear()
        self.interface.ui_directories['all'] = join(dirname(__file__),
                                                    'test_ui', 'gui')
        message = Message('test', {"framework": "all"}, {'context': "All"})
        self.interface.upload_gui_pages(message)
        self.assertTrue(handled.wait(2))

        self.assertEqual(msg.context['context'], message.context['context'])
        self.assertEqual(msg.msg_type, "gui.page.upload")
        self.assertEqual(msg.data['__from'], self.iface_name)

        pages = msg.data['pages']
        self.assertIsInstance(pages, dict)
        for key, val in pages.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, str)

        self.assertEqual(bytes.fromhex(pages.get("qt5/test.qml")),
                         b"qt5", pages)
        self.assertEqual(bytes.fromhex(pages.get("qt6/test.qml")),
                         b"qt6", pages)

        # Upload requested other skill
        handled.clear()
        message = Message('test', {"framework": "all",
                                   "skill_id": "other_skill"})
        self.interface.upload_gui_pages(message)
        self.assertFalse(handled.wait(2))

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

    @patch('ovos_bus_client.apis.gui.resolve_resource_file')
    @patch('ovos_bus_client.apis.gui.resolve_ovos_resource_file')
    def test_pages2uri(self, ovos_res, res):
        def _resolve(name, config):
            self.assertEqual(config, self.interface.config)
            if name.startswith("ui/core"):
                return f"res/{name}"

        def _ovos_resolve(name, extra_dirs):
            self.assertEqual(extra_dirs,
                             list(self.interface.ui_directories.values()))
            if name.startswith("ui/ovos"):
                return f"ovos/{name}"

        # Mock actual resource resolution methods
        ovos_res.side_effect = _ovos_resolve
        res.side_effect = _resolve

        # remote_url is None
        # OVOS Res
        self.assertEqual(self.interface._pages2uri(["ui/ovos/test"]),
                         ["file://ovos/ui/ovos/test"])
        ovos_res.assert_called_once()
        self.assertEqual(self.interface._pages2uri(["ovos/test"]),
                         ["file://ovos/ui/ovos/test"])
        res.assert_not_called()
        # Core Res
        self.assertEqual(self.interface._pages2uri(["ui/core/test"]),
                         ["file://res/ui/core/test"])
        res.assert_called_once()
        self.assertEqual(self.interface._pages2uri(["core/test"]),
                         ["file://res/ui/core/test"])

    def test_normalize_page_name(self):
        legacy_name = "test.qml"
        name_with_path = "subdir/test"
        name_with_dot = "subdir/test.file"
        self.assertEqual(self.interface._normalize_page_name(legacy_name),
                         "test")
        self.assertEqual(self.interface._normalize_page_name(name_with_path),
                         "subdir/test")
        self.assertEqual(self.interface._normalize_page_name(name_with_dot),
                         "subdir/test.file")

    def test_show_page(self):
        real_show_pages = self.interface.show_pages
        self.interface.show_pages = Mock()

        # Default args
        self.interface.show_page("test")
        self.interface.show_pages.assert_called_once_with(["test"], 0,
                                                          None, False)

        self.interface.show_page("test2", True, True)
        self.interface.show_pages.assert_called_with(["test2"], 0,
                                                     True, True)

        self.interface.show_page("test3", 30, True)
        self.interface.show_pages.assert_called_with(["test3"], 0,
                                                     30, True)
        self.interface.show_pages = real_show_pages

    def test_show_pages(self):
        msg: Message = Message("")
        handled = Event()

        def _gui_value_set(message):
            self.assertEqual(message.data['__from'], self.interface.skill_id)

        def _gui_page_show(message):
            nonlocal msg
            msg = message
            handled.set()

        self.bus.on('gui.value.set', _gui_value_set)
        self.bus.on('gui.page.show', _gui_page_show)

        # Test resource absolute paths
        file_base_dir = join(dirname(__file__), "test_ui", "ui")
        files = [join(file_base_dir, "test.qml"),
                 join(file_base_dir, "subdir", "test.qml")]
        self.interface.show_pages(files)
        self.assertTrue(handled.wait(2))
        self.assertEqual(msg.msg_type, "gui.page.show")
        for page in msg.data['page']:
            self.assertTrue(page.startswith("file://"))
            path = page.replace("file://", "")
            self.assertTrue(isfile(path), page)
        self.assertEqual(len(msg.data['page']), len(msg.data['page_names']))
        self.assertIsInstance(msg.data["index"], int)
        self.assertEqual(msg.data['__from'], self.interface.skill_id)
        self.assertIsNone(msg.data["__idle"])
        self.assertIsInstance(msg.data["__animations"], bool)
        self.assertEqual(msg.data["ui_directories"],
                         self.interface.ui_directories)

        # Test resources resolved locally
        handled.clear()
        files = ["file.qml", "subdir/file.qml"]
        index = 1
        override_idle = 30
        override_animations = True
        self.interface.show_pages(files, index, override_idle,
                                  override_animations)
        self.assertTrue(handled.wait(2))
        self.assertEqual(msg.msg_type, "gui.page.show")
        for page in msg.data['page']:
            self.assertTrue(page.startswith("file://"))
            path = page.replace("file://", "")
            self.assertTrue(isfile(path), page)
        self.assertEqual(msg.data["page_names"], ["file", "subdir/file"])
        self.assertEqual(msg.data["index"], index)
        self.assertEqual(msg.data["__from"], self.interface.skill_id)
        self.assertEqual(msg.data["__idle"], override_idle)
        self.assertEqual(msg.data["__animations"], override_animations)
        self.assertEqual(msg.data["ui_directories"],
                         self.interface.ui_directories)

        # Test resources not resolved locally
        handled.clear()
        files = ["file.qml", "other.page"]
        index = 1
        override_idle = 30
        override_animations = True
        self.interface.show_pages(files, index, override_idle,
                                  override_animations)
        self.assertTrue(handled.wait(2))
        self.assertEqual(msg.msg_type, "gui.page.show")
        self.assertEqual(msg.data["page"], list())
        self.assertEqual(msg.data["page_names"], ["file", "other.page"])
        self.assertEqual(msg.data["index"], index)
        self.assertEqual(msg.data["__from"], self.interface.skill_id)
        self.assertEqual(msg.data["__idle"], override_idle)
        self.assertEqual(msg.data["__animations"], override_animations)
        self.assertEqual(msg.data["ui_directories"],
                         self.interface.ui_directories)

    def test_remove_page(self):
        real_remove_pages = self.interface.remove_pages
        self.interface.remove_pages = Mock()
        self.interface.remove_page("test_page")
        self.interface.remove_pages.assert_called_once_with(["test_page"])
        self.interface.remove_pages = real_remove_pages

    def test_remove_pages(self):
        msg = Message("")
        handled = Event()

        def _gui_page_delete(message):
            nonlocal msg
            msg = message
            handled.set()

        self.bus.on("gui.page.delete", _gui_page_delete)

        # Test resolved page
        pages = ["test.qml"]
        self.interface.remove_pages(pages)
        self.assertTrue(handled.wait(2))
        self.assertEqual(msg.msg_type, "gui.page.delete")
        self.assertEqual(len(msg.data['page']), len(pages))
        for page in msg.data['page']:
            self.assertTrue(page.startswith("file://"))
            path = page.replace("file://", "")
            self.assertTrue(isfile(path), page)
        self.assertEqual(msg.data['page_names'], ["test"])
        self.assertEqual(msg.data['__from'], self.interface.skill_id)

        # Test unresolved pages
        handled.clear()
        pages = ['file.qml', 'dir/other.file']
        self.interface.remove_pages(pages)
        self.assertTrue(handled.wait(2))
        self.assertEqual(msg.msg_type, "gui.page.delete")
        self.assertEqual(msg.data['page'], [])
        self.assertEqual(msg.data['page_names'], ["file", "dir/other.file"])
        self.assertEqual(msg.data['__from'], self.interface.skill_id)

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
