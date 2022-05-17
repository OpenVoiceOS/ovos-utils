import subprocess
from distutils.spawn import find_executable


class InputDeviceHelper:
    def __init__(self) -> None:
        self.input_devices_list = []
        if not find_executable("libinput"):
            raise Exception("libinput executable not found")

    # ToDo: add support for discovring the input device based of a connected
    # monitors, currently linux only supports input listing directly from the
    # system

    def build_input_devices_list(self):
        # Always clear the list before building it
        self.input_devices_list.clear()

        input_device_names = []
        input_device_kernel_path = []
        input_device_group = []
        input_device_capabilities = []

        # Get the list of devices from libinput
        proc_output = subprocess.check_output(
            ['libinput', 'list-devices']).decode('utf-8')
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
            self.input_devices_list.append(
                {"Device": input_device_names[i],
                 "Kernel": input_device_kernel_path[i],
                 "Group": input_device_group[i],
                 "Capabilities": input_device_capabilities[i]
                 })

    def get_input_devices_list(self):
        self.build_input_devices_list()
        return self.input_devices_list

    def can_use_touch_mouse(self):
        # check if any of the devices support touch or mouse
        self.build_input_devices_list()
        for device in self.input_devices_list:
            if "touch" in device["Capabilities"] or "mouse" in device[
                    "Capabilities"] or "tablet" in device["Capabilities"] or "gesture" in device["Capabilities"]:
                return True

        return False

    def can_use_keyboard(self):
        self.build_input_devices_list()
        for device in self.input_devices_list:
            if "keyboard" in device["Capabilities"]:
                return True

        return False


def can_use_touch_mouse():
    return InputDeviceHelper().can_use_touch_mouse()


def can_use_keyboard():
    return InputDeviceHelper().can_use_keyboard()
