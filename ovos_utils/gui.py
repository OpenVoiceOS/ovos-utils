import os
from os.path import join, isdir
from typing import List

from ovos_utils.log import LOG
from ovos_bus_client.util import wait_for_reply
from ovos_utils.system import is_installed, has_screen, is_process_running

_default_gui_apps = (
    "ovos-gui-app",
    "ovos-shell",
    "mycroft-gui-app",
    "mycroft-embedded-shell"
)


def can_display() -> bool:
    """
    Return true if a display is available
    """
    return bool(has_screen())


def is_gui_installed(applications: List[str] = _default_gui_apps) -> bool:
    """
    Return true if a GUI application is installed
    @param applications: list of applications to check for
    """
    return any((is_installed(app) for app in applications))


def is_gui_running(applications: List[str] = _default_gui_apps) -> bool:
    """
    Return true if a GUI application is running
    @param applications: list of applications to check for
    """
    deprecated = any((is_process_running(app) for app in applications
                      if app.startswith("mycroft-")))
    if deprecated:
        LOG.warning("you are running a deprecated mycroft-gui version, "
                    "please move to a OVOS maintained version")
        return True
    return deprecated or any((is_process_running(app) for app in applications))


def is_gui_connected(bus=None) -> bool:
    """
    Check if a GUI is connected to the MessageBus.
    sends "gui.status.request" and waits for "gui.status.request.response"
    @param bus: MessageBusClient to use for query
    @return: True if GUI is connected
    """
    response = wait_for_reply("gui.status.request",
                              "gui.status.request.response", bus=bus)
    if response:
        return response.data["connected"]
    return False


def can_use_local_gui() -> bool:
    """
    Returns True if a local GUI is installed and running (does not check if the
    GUI is connected to an accessible GUI service).
    """
    if can_display() and is_gui_installed() and is_gui_running():
        return True
    return False


def can_use_gui(bus=None,
                local: bool = False) -> bool:
    """
    Check if a GUI is available to connect to
    @param bus: MessageBusClient to use for query
    @param local: If True, only check for a GUI on the local host
    @return: True if a GUI is available
    """
    if local:
        return can_use_local_gui()
    return can_use_local_gui() or is_gui_connected(bus)


def get_ui_directories(root_dir: str) -> dict:
    """
    Get a dict of available UI directories by GUI framework.
    @param root_dir: base directory to inspect for available UI directories
    @return: Dict of framework name to UI resource directory
    """
    ui_directories = dict()
    if isdir(f"{root_dir}/ui"):
        LOG.debug("legacy UI directory found - Handling `ui` directory as `qt5`")
        ui_directories["qt5"] = f"{root_dir}/ui"
    elif isdir(f"{root_dir}/gui"):
        for framework in os.listdir(f"{root_dir}/gui"):
            if isdir(f"{root_dir}/gui/{framework}"):
                LOG.debug(f"Skill supports GUI framework: {framework} from folder: {root_dir}/gui/{framework}")
                ui_directories[framework] = f"{root_dir}/gui/{framework}"
    return ui_directories
