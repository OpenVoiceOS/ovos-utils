import unittest
from unittest import mock
from unittest.mock import Mock


class TestDeviceInput(unittest.TestCase):
    # @mock.patch('distutils.spawn.find_executable')
    # def test_get_input_device_list(self, find_exec):
    #     from ovos_utils.device_input import InputDeviceHelper
    #     find_exec.return_value = False
    #     dev_input = InputDeviceHelper()
    #     dev_input.libinput_devices_list = ['libinput']
    #     dev_input.xinput_devices_list = ['xinput']
    #     self. assertEqual(dev_input.get_input_device_list(),
    #                       ['libinput', 'xinput'])

    @mock.patch('distutils.spawn.find_executable')
    def test_can_use_touch_mouse(self, find_exec):
        from ovos_utils.device_input import InputDeviceHelper
        find_exec.return_value = True
        dev_input = InputDeviceHelper()

        dev_input._build_linput_devices_list = Mock()
        dev_input._build_xinput_devices_list = Mock()

        dev_input.libinput_devices_list = [{'Device': 'Mock',
                                            'Capabilities': ['mouse']},
                                            {'Device': "Mock 1",
                                             'Capabilities': ['touch']}
                                            ]
        self.assertTrue(dev_input.can_use_touch_mouse())

        dev_input.libinput_devices_list.pop()
        self.assertTrue(dev_input.can_use_touch_mouse())
        dev_input.libinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_touch_mouse())
        dev_input.xinput_devices_list = [{'Device': 'xinput',
                                          'Capabilities': ['tablet']
                                          }]
        self.assertTrue(dev_input.can_use_touch_mouse())
        dev_input.xinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_touch_mouse())

    @mock.patch('distutils.spawn.find_executable')
    def test_can_use_keyboard(self, find_exec):
        from ovos_utils.device_input import InputDeviceHelper
        find_exec.return_value = True
        dev_input = InputDeviceHelper()

        dev_input._build_linput_devices_list = Mock()
        dev_input._build_xinput_devices_list = Mock()

        dev_input.libinput_devices_list = [{'Device': 'Mock',
                                            'Capabilities': ['keyboard']},
                                            {'Device': "Mock 1",
                                             'Capabilities': ['touch']}
                                            ]
        self.assertTrue(dev_input.can_use_keyboard())

        dev_input.libinput_devices_list.pop()
        self.assertTrue(dev_input.can_use_keyboard())
        dev_input.libinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_keyboard())
        dev_input.xinput_devices_list = [{'Device': 'xinput',
                                          'Capabilities': ['keyboard']
                                          }]
        self.assertTrue(dev_input.can_use_keyboard())
        dev_input.xinput_devices_list.pop()
        self.assertFalse(dev_input.can_use_keyboard())
