import subprocess
import evdev
from distutils.spawn import find_executable
from ovos_utils.gui import is_gui_installed
from ovos_utils.log import LOG


class EvdevHelper:
    def __init__(self):
        pass
    
    def _device_has_capability(self, device, capability):
        if capability in device.capabilities():
            return True
        return False

    def _device_supports_key(self, provided_keys, required_key):
        if required_key in provided_keys:
            return True
        return False

    def _check_if_device_is_type_mouse(self, device):
        if self._device_has_capability(device, evdev.ecodes.EV_REL):
            if self._device_has_capability(device, evdev.ecodes.REL_X):
                if self._device_has_capability(device, evdev.ecodes.REL_Y):
                    return True
        return False

    def _check_if_device_is_type_touchscreen(self, device):
        if self._device_has_capability(device, evdev.ecodes.EV_ABS):
            if self._device_has_capability(device, evdev.ecodes.ABS_X):
                if self._device_has_capability(device, evdev.ecodes.ABS_Y):
                    return True
        return False

    def _check_if_device_is_type_tablet(self, device):
        if self._device_has_capability(device, evdev.ecodes.EV_ABS):
            if self._device_has_capability(device, evdev.ecodes.ABS_X):
                if self._device_has_capability(device, evdev.ecodes.ABS_Y):
                    if self._device_has_capability(device, evdev.ecodes.ABS_PRESSURE):
                        return True
        return False

    def _check_if_device_is_type_gesture(self, device):
        if self._device_has_capability(device, evdev.ecodes.EV_ABS):
            if self._device_has_capability(device, evdev.ecodes.EV_KEY):
                if self._device_has_capability(device, evdev.ecodes.BTN_TOOL_FINGER):
                    return True
        return False

    def _check_if_device_is_type_keyboard(self, device):
        keys = [evdev.ecodes.KEY_F1, evdev.ecodes.KEY_F2,
                evdev.ecodes.KEY_F3, evdev.ecodes.KEY_F4,
                evdev.ecodes.KEY_F5, evdev.ecodes.KEY_F6,
                evdev.ecodes.KEY_F7, evdev.ecodes.KEY_F8,
                evdev.ecodes.KEY_F9, evdev.ecodes.KEY_F10,
                evdev.ecodes.KEY_F11, evdev.ecodes.KEY_F12,
                evdev.ecodes.KEY_LEFTCTRL, evdev.ecodes.KEY_LEFTSHIFT,
                evdev.ecodes.KEY_LEFTALT, evdev.ecodes.KEY_LEFTMETA,
                evdev.ecodes.KEY_RIGHTCTRL, evdev.ecodes.KEY_RIGHTSHIFT,
                evdev.ecodes.KEY_RIGHTALT, evdev.ecodes.KEY_RIGHTMETA,
                evdev.ecodes.KEY_ESC, evdev.ecodes.KEY_ENTER,
                evdev.ecodes.KEY_BACKSPACE, evdev.ecodes.KEY_TAB,
                evdev.ecodes.KEY_SPACE, evdev.ecodes.KEY_MENU]

        if self._device_has_capability(device, evdev.ecodes.EV_KEY):
            for key in keys:
                if self._device_supports_key(device.capabilities()[evdev.ecodes.EV_KEY], key):
                    return True
        
        return False

    def _build_device_capabilities(self, device):
        capabilities = []
        if self._check_if_device_is_type_mouse(device):
            capabilities.append("mouse")
        if self._check_if_device_is_type_keyboard(device):
            capabilities.append("keyboard")
        if self._check_if_device_is_type_touchscreen(device):
            capabilities.append("touch")
        if self._check_if_device_is_type_tablet(device):
            capabilities.append("tablet")
        if self._check_if_device_is_type_gesture(device):
            capabilities.append("gesture")
        return capabilities

    def _build_list_of_evdev_input_devices(self):
        input_devices = []
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            capabilities = self._build_device_capabilities(device)
            if capabilities:
                input_devices.append({
                    "Device": device.name,
                    "Capabilities": capabilities
                })
        return input_devices

    def supports_touch_or_pointer_input(self):
        devices = self._build_list_of_evdev_input_devices()
        for device in devices:
            if "touch" in device["Capabilities"] or "mouse" in device["Capabilities"]:
                return True
        return False


class InputDeviceHelper:
    def __init__(self) -> None:
        self.libinput_devices_list = []
        self.xinput_devices_list = []
        if not find_executable("libinput") and not find_executable("xinput"):
            LOG.warning("Could not find libinput, input device detection will be inaccurate")
        self.evdev_helper = EvdevHelper()      

    # ToDo: add support for discovring the input device based of a connected
    # monitors, currently linux only supports input listing directly from the
    # system
    def _build_linput_devices_list(self):
        # Always clear the list before building it
        self.libinput_devices_list.clear()

        input_device_names = []
        input_device_kernel_path = []
        input_device_group = []
        input_device_capabilities = []

        # Get the list of devices from libinput
        proc_output = subprocess.check_output(['libinput', 'list-devices']).decode('utf-8')
        for line in proc_output.splitlines():
            if line.startswith('Device'):
                unformated_device_name = line.split(':')[1]
                unformated_device_name = unformated_device_name.strip()
                input_device_names.append(unformated_device_name)

        for line in proc_output.splitlines():
            if line.startswith('Kernel'):
                unformated_device_kernel_path = line.split(':')[1]
                unformated_device_kernel_path = unformated_device_kernel_path.strip()
                input_device_kernel_path.append(unformated_device_kernel_path)

        for line in proc_output.splitlines():
            if line.startswith('Group'):
                unformated_device_group = line.split(':')[1]
                unformated_device_group = unformated_device_group.strip()
                input_device_group.append(unformated_device_group)

        for line in proc_output.splitlines():
            if line.startswith("Capabilities"):
                unformated_device_capabilities = line.split(':')[1]
                unformated_device_capabilities = unformated_device_capabilities.strip()
                # check if there is a comma in the string and if so, split it
                if ' ' in unformated_device_capabilities:
                    unformated_device_capabilities = unformated_device_capabilities.split(
                        ' ')
                else:
                    unformated_device_capabilities = [
                        unformated_device_capabilities]

                input_device_capabilities.append(
                    unformated_device_capabilities)

        for i in range(len(input_device_names)):
            self.libinput_devices_list.append(
                {"Device": input_device_names[i],
                 "Kernel": input_device_kernel_path[i],
                 "Group": input_device_group[i],
                 "Capabilities": input_device_capabilities[i]
                 })

    def _get_libinput_devices_list(self):
        if find_executable("libinput"):
            try:
                self._build_linput_devices_list()
            except:
                self.libinput_devices_list.clear()
                LOG.exception("Failed to query libinput for devices")
        return self.libinput_devices_list

    def _build_xinput_devices_list(self):
        # Always clear the list before building it
        self.xinput_devices_list.clear()

        # Get the list of devices from xinput
        proc_output = subprocess.check_output(['xinput', 'list']).decode('utf-8')
        for line in proc_output.splitlines():
            # skip virtual devices always present
            if "↳" not in line or "XTEST" in line:
                continue
            line = line.replace("↳", "").replace("⎡", "").replace("⎣", "").replace("⎜", "").strip()

            if "pointer" in line:
                dev = {"Device": line.split("id=")[0].strip(),
                       "Capabilities": ["mouse"]}
                self.xinput_devices_list.append(dev)
            if "keyboard" in line:
                dev = {"Device": line.split("id=")[0].strip(),
                       "Capabilities": ["keyboard"]}
                self.xinput_devices_list.append(dev)

    def _get_xinput_devices_list(self):
        if find_executable("xinput"):
            try:
                self._build_xinput_devices_list()
            except:
                self.xinput_devices_list.clear()
                LOG.exception("Failed to query xinput for devices")
        return self.xinput_devices_list

    def get_input_device_list(self):
        # check if any of the devices support touch or mouse
        self._get_libinput_devices_list()
        self._get_xinput_devices_list()
        return self.libinput_devices_list + self.xinput_devices_list

    def can_use_touch_mouse(self):
        # check evdev first as it is more reliable
        evdev_support_required_input = self.evdev_helper.supports_touch_or_pointer_input()
        if evdev_support_required_input:
            return True
        
        if not find_executable("libinput") and not find_executable("xinput"):
            # if gui installed assume we have a mouse
            # otherwise let's assume we are a server or something...
            return is_gui_installed()

        for device in self.get_input_device_list():
            if "touch" in device["Capabilities"] or \
                    "mouse" in device["Capabilities"] or \
                    "tablet" in device["Capabilities"] or \
                    "gesture" in device["Capabilities"]:
                return True

        return False

    def can_use_keyboard(self):
        for device in self.get_input_device_list():
            if "keyboard" in device["Capabilities"]:
                return True
        return False


def can_use_touch_mouse():
    return InputDeviceHelper().can_use_touch_mouse()


def can_use_keyboard():
    return InputDeviceHelper().can_use_keyboard()


if __name__ == "__main__":
    can_use_touch_mouse()
