from ovos_utils.system import is_installed, has_screen


def can_display():
    return has_screen()


def is_gui_installed():
    return is_installed("mycroft-gui-app")


def is_gui_connected():
    # TODO bus api for https://github.com/MycroftAI/mycroft-core/pull/2682
    return False
