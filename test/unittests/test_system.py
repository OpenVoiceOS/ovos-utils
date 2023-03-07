import unittest


class TestSystem(unittest.TestCase):
    def test_is_running_from_module(self):
        from ovos_utils.system import is_running_from_module
        self.assertFalse(is_running_from_module("mycroft"))
        self.assertTrue(is_running_from_module("unittest"))

    def test_ntp_sync(self):
        # TODO
        pass

    def test_system_shutdown(self):
        # TODO
        pass

    def test_system_reboot(self):
        # TODO
        pass

    def test_ssh_enable(self):
        # TODO
        pass

    def test_ssh_disable(self):
        # TODO
        pass

    def test_restart_mycroft_service(self):
        # TODO
        pass

    def test_restart_service(self):
        # TODO
        pass

    def test_enable_service(self):
        # TODO
        pass

    def test_disable_service(self):
        # TODO
        pass

    def test_check_service_active(self):
        # TODO
        pass

    def test_set_root_path(self):
        from ovos_utils.system import set_root_path, _USER_DEFINED_ROOT
        set_root_path("test")
        self.assertEqual(_USER_DEFINED_ROOT, "test")
        set_root_path("mycroft")
        self.assertEqual(_USER_DEFINED_ROOT, "mycroft")
        set_root_path(None)
        self.assertIsNone(_USER_DEFINED_ROOT)

    def test_find_root_from_sys_path(self):
        # TODO
        pass

    def test_find_root_from_sitepackages(self):
        # TODO
        pass

    def test_search_mycroft_core_location(self):
        # TODO
        pass

    def test_get_desktop_environment(self):
        # TODO
        pass

    def test_is_process_running(self):
        # TODO
        pass

    def test_find_executable(self):
        # TODO
        pass

    def test_is_installed(self):
        # TODO
        pass

    def test_has_screen(self):
        # TODO
        pass

    def test_module_property(self):
        import sys
        from ovos_utils.system import module_property

        test_val = True

        @module_property
        def _mock_property():
            return test_val

        test_module = sys.modules[self.__module__]
        self.assertTrue(test_module.mock_property)

        test_val = False
        self.assertFalse(test_module.mock_property)
