import subprocess
from distutils.spawn import find_executable

from ovos_utils.log import LOG


class InputDeviceHelper:
    def __init__(self) -> None:
        self.libinput_devices_list = []
        self.xinput_devices_list = []
        if not find_executable("libinput") and not find_executable("xinput"):
            raise Exception("xinput/libinput executable not found")

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
        self._build_linput_devices_list()
        return self.libinput_devices_list

    def _build_xinput_devices_list(self):
        # Always clear the list before building it
        self.xinput_devices_list.clear()

        # Get the list of devices from xinput
        proc_output = subprocess.check_output(['xinput', 'list']).decode('utf-8')
        for line in proc_output.splitlines():
            if "id=" not in line:
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
        self._build_xinput_devices_list()
        return self.xinput_devices_list

    def get_input_device_list(self):
        # check if any of the devices support touch or mouse
        if find_executable("libinput"):
            self._build_linput_devices_list()
        if find_executable("xinput"):
            self._build_xinput_devices_list()
        return self.libinput_devices_list + self.xinput_devices_list

    def can_use_touch_mouse(self):
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
    try:
        return InputDeviceHelper().can_use_touch_mouse()
    except:
        LOG.exception("could not check for input devices, is libinput-dev installed?")


def can_use_keyboard():
    return InputDeviceHelper().can_use_keyboard()
