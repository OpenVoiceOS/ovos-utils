from os import walk
from typing import List, Union, Optional, Callable

import time
from collections import namedtuple
from enum import IntEnum
from os.path import join, splitext, isfile, isdir

from ovos_utils import resolve_ovos_resource_file, resolve_resource_file
from ovos_utils.log import LOG, log_deprecation
from ovos_utils.messagebus import wait_for_reply, get_mycroft_bus, Message
from ovos_utils.system import is_installed, has_screen, is_process_running

_default_gui_apps = (
    "mycroft-gui-app",
    "ovos-shell",
    "mycroft-embedded-shell",
    "plasmashell"
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
    return any((is_process_running(app) for app in applications))


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
    base_directory = root_dir
    if isdir(join(base_directory, "gui")):
        LOG.debug("Skill implements resources in `gui` directory")
        ui_directories["all"] = join(base_directory, "gui")
        return ui_directories
    LOG.info("Checking for legacy UI directories")
    if isdir(join(base_directory, "ui")):
        LOG.debug("Handling `ui` directory as `qt5`")
        ui_directories["qt5"] = join(base_directory, "ui")
    return ui_directories


def extend_about_data(about_data: Union[list, dict],
                      bus=None):
    """
    Add more information to the "About" section in the GUI.
    @param about_data: list of dict key, val information to add to the GUI
    @param bus: MessageBusClient object to emit update on
    """
    bus = bus or get_mycroft_bus()
    if isinstance(about_data, list):
        bus.emit(Message("smartspeaker.extension.extend.about",
                         {"display_list": about_data}))
    elif isinstance(about_data, dict):
        display_list = [about_data]
        bus.emit(Message("smartspeaker.extension.extend.about",
                         {"display_list": display_list}))
    else:
        LOG.error("about_data is not a list or dictionary")


class GUIWidgets:
    def __init__(self, bus=None):
        self.bus = bus or get_mycroft_bus()

    def show_widget(self, widget_type, widget_data):
        LOG.debug("Showing widget: " + widget_type)
        self.bus.emit(Message("ovos.widgets.display", {"type": widget_type, "data": widget_data}))

    def remove_widget(self, widget_type, widget_data):
        LOG.debug("Removing widget: " + widget_type)
        self.bus.emit(Message("ovos.widgets.remove", {"type": widget_type, "data": widget_data}))

    def update_widget(self, widget_type, widget_data):
        LOG.debug("Updating widget: " + widget_type)
        self.bus.emit(Message("ovos.widgets.update", {"type": widget_type, "data": widget_data}))


class GUIPlaybackStatus(IntEnum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    UNDEFINED = 3


class GUITracker:
    """ Replicates GUI API from mycroft-core,
    does not interact with GUI but exactly mimics status"""
    Namespace = namedtuple('Namespace', ['name', 'pages'])
    RESERVED_KEYS = ['__from', '__idle']
    IDLE_MESSAGE = "mycroft.mark2.collect_idle"  # TODO this will change

    def __init__(self, bus=None,
                 host='0.0.0.0', port=8181, route='/core', ssl=False):
        self.bus = bus or get_mycroft_bus(host, port, route, ssl)
        self._active_skill = None
        self._is_idle = False
        self.idle_ts = 0
        # This datastore holds the data associated with the GUI provider. Data
        # is stored in Namespaces, so you can have:
        # self.datastore["namespace"]["name"] = value
        # Typically the namespace is a meaningless identifier, but there is a
        # special "SYSTEM" namespace.
        self._datastore = {}

        # self.loaded is a list, each element consists of a namespace named
        # tuple.
        # The namespace namedtuple has the properties "name" and "pages"
        # The name contains the namespace name as a string and pages is a
        # mutable list of loaded pages.
        #
        # [Namespace name, [List of loaded qml pages]]
        # [
        # ["SKILL_NAME", ["page1.qml, "page2.qml", ... , "pageN.qml"]
        # [...]
        # ]
        self._loaded = []  # list of lists in order.

        # Listen for new GUI clients to announce themselves on the main bus
        self._active_namespaces = []

        # GUI handlers
        self.bus.on("gui.value.set", self._on_gui_set_value)
        self.bus.on("gui.page.show", self._on_gui_show_page)
        self.bus.on("gui.page.delete", self._on_gui_delete_page)
        self.bus.on("gui.clear.namespace", self._on_gui_delete_namespace)

        # Idle screen handlers TODO message cleanup...
        self._idle_screens = {}
        self.bus.on("mycroft.device.show.idle", self._on_show_idle)  # legacy
        self.bus.on(self.IDLE_MESSAGE, self._on_show_idle)
        self.bus.on("mycroft.mark2.register_idle", self._on_register_idle)

        self.bus.emit(Message("mycroft.mark2.collect_idle"))

    @staticmethod
    def is_gui_installed():
        return is_gui_installed()

    @staticmethod
    def is_gui_running():
        return is_gui_running()

    def is_gui_connected(self):
        return is_gui_connected(self.bus)

    @staticmethod
    def can_display():
        return can_display()

    def is_displaying(self):
        return self.active_skill is not None

    def is_idle(self):
        return self._is_idle

    @property
    def active_skill(self):
        return self._active_skill

    @property
    def gui_values(self):
        return self._datastore

    @property
    def idle_screens(self):
        return self._idle_screens

    @property
    def active_namespaces(self):
        return self._active_namespaces

    @property
    def gui_pages(self):
        return self._loaded

    # GUI event handlers
    # user can/should subclass this
    def on_idle(self, namespace):
        pass

    def on_active(self, namespace):
        pass

    def on_new_page(self, namespace, page, index):
        pass

    def on_delete_page(self, namespace, index):
        pass

    def on_gui_value(self, namespace, key, value):
        pass

    def on_new_namespace(self, namespace):
        pass

    def on_move_namespace(self, namespace, from_index, to_index):
        pass

    def on_remove_namespace(self, namespace, index):
        pass

    ######################################################################
    # GUI client API
    # TODO see how much of this can be removed
    @staticmethod
    def _get_page_data(message):
        """ Extract page related data from a message.

        Args:
            message: messagebus message object
        Returns:
            tuple (page, namespace, index)
        Raises:
            ValueError if value is missing.
        """
        data = message.data
        # Note:  'page' can be either a string or a list of strings
        if 'page' not in data:
            raise ValueError("Page missing in data")
        if 'index' in data:
            index = data['index']
        else:
            index = 0
        page = data.get("page", "")
        namespace = data.get("__from", "")
        return page, namespace, index

    def _set(self, namespace, name, value):
        """ Perform the send of the values to the connected GUIs. """
        if namespace not in self._datastore:
            self._datastore[namespace] = {}
        if self._datastore[namespace].get(name) != value:
            self._datastore[namespace][name] = value

    def __find_namespace(self, namespace):
        for i, skill in enumerate(self._loaded):
            if skill[0] == namespace:
                return i
        return None

    def __insert_pages(self, namespace: str, pages: List[str]):
        """ Insert pages into the namespace

        Args:
            namespace (str): Namespace to add to
            pages (list):    Pages (str) to insert
        """
        LOG.debug("Inserting new pages")
        # Insert the pages into local reprensentation as well.
        updated = self.Namespace(self._loaded[0].name,
                                 self._loaded[0].pages + pages)
        self._loaded[0] = updated

    def __remove_page(self, namespace, pos):
        """ Delete page.

        Args:
            namespace (str): Namespace to remove from
            pos (int):      Page position to remove
        """
        LOG.debug("Deleting {} from {}".format(pos, namespace))
        self.on_delete_page(namespace, pos)
        # Remove the page from the local reprensentation as well.
        self._loaded[0].pages.pop(pos)

    def __insert_new_namespace(self, namespace: str, pages: List[str]):
        """ Insert new namespace and pages.

        This first sends a message adding a new namespace at the
        highest priority (position 0 in the namespace stack)

        Args:
            namespace (str):  The skill namespace to create
            pages (str):      Pages to insert (name matches QML)
        """
        LOG.debug("Inserting new namespace")
        self.on_new_namespace(namespace)
        # Make sure the local copy is updated
        self._loaded.insert(0, self.Namespace(namespace, pages))
        if time.time() - self.idle_ts > 1:
            # we cant know if this page is idle or not, but when it is we
            # received a idle event within the same second
            self._is_idle = False
            self.on_active(namespace)
        else:
            self.on_idle(namespace)

    def __move_namespace(self, from_pos, to_pos):
        """ Move an existing namespace to a new position in the stack.

        Args:
            from_pos (int): Position in the stack to move from
            to_pos (int): Position to move to
        """
        LOG.debug("Activating existing namespace")
        # Move the local representation of the skill from current
        # position to position 0.
        namespace = self._loaded[from_pos].name
        self.on_move_namespace(namespace, from_pos, to_pos)
        self._loaded.insert(to_pos, self._loaded.pop(from_pos))

    def _show(self, namespace, page, index):
        """ Show a page and load it as needed.

        Args:
            page (str or list): page(s) to show
            namespace (str):  skill namespace
            index (int): ??? TODO: Unused in code ???

        TODO: - Update sync to match.
              - Separate into multiple functions/methods
        """

        LOG.debug("GUIConnection activating: " + namespace)
        self._active_skill = namespace
        pages = page if isinstance(page, list) else [page]

        # find namespace among loaded namespaces
        try:
            index = self.__find_namespace(namespace)
            if index is None:
                # This namespace doesn't exist, insert them first so they're
                # shown.
                self.__insert_new_namespace(namespace, pages)
                return
            else:  # Namespace exists
                if index > 0:
                    # Namespace is inactive, activate it by moving it to
                    # position 0
                    self.__move_namespace(index, 0)

                # Find if any new pages needs to be inserted
                new_pages = [p for p in pages if
                             p not in self._loaded[0].pages]
                if new_pages:
                    self.__insert_pages(namespace, new_pages)
        except Exception as e:
            LOG.exception(repr(e))

    ######################################################################
    # Internal GUI events
    def _on_gui_set_value(self, message):
        data = message.data
        namespace = data.get("__from", "")

        # Pass these values on to the GUI renderers
        for key in data:
            if key not in self.RESERVED_KEYS:
                try:
                    self._set(namespace, key, data[key])
                    self.on_gui_value(namespace, key, data[key])
                except Exception as e:
                    LOG.exception(repr(e))

    def _on_gui_delete_page(self, message):
        """ Bus handler for removing pages. """
        page, namespace, _ = self._get_page_data(message)
        try:
            self._remove_pages(namespace, page)
        except Exception as e:
            LOG.exception(repr(e))

    def _on_gui_delete_namespace(self, message):
        """ Bus handler for removing namespace. """
        try:
            namespace = message.data['__from']
            self._remove_namespace(namespace)
        except Exception as e:
            LOG.exception(repr(e))

    def _on_gui_show_page(self, message):
        try:
            page, namespace, index = self._get_page_data(message)
            # Pass the request to the GUI(s) to pull up a page template
            self._show(namespace, page, index)
            self.on_new_page(namespace, page, index)
        except Exception as e:
            LOG.exception(repr(e))

    def _remove_namespace(self, namespace):
        """ Remove namespace.

        Args:
            namespace (str): namespace to remove
        """
        index = self.__find_namespace(namespace)
        if index is None:
            return
        else:
            LOG.debug("Removing namespace {} at {}".format(namespace, index))
            self.on_remove_namespace(namespace, index)
            # Remove namespace from loaded namespaces
            self._loaded.pop(index)

    def _remove_pages(self, namespace, pages):
        """ Remove the listed pages from the provided namespace.

        Args:
            namespace (str):    The namespace to modify
            pages (list):       List of page names (str) to delete
        """
        try:
            index = self.__find_namespace(namespace)
            if index is None:
                return
            else:
                # Remove any pages that doesn't exist in the namespace
                pages = [p for p in pages if p in self._loaded[index].pages]
                # Make sure to remove pages from the back
                indexes = [self._loaded[index].pages.index(p) for p in pages]
                indexes = sorted(indexes)
                indexes.reverse()
                for page_index in indexes:
                    self.__remove_page(namespace, page_index)
        except Exception as e:
            LOG.exception(repr(e))

    def _on_register_idle(self, message):
        """Handler for catching incoming idle screens."""
        if "name" in message.data and "id" in message.data:
            screen = message.data["name"]
            if screen not in self._idle_screens:
                self.bus.on("{}.idle".format(message.data["id"]),
                            self._on_show_idle)
            self._idle_screens[screen] = message.data["id"]
            LOG.info("Registered {}".format(message.data["name"]))
        else:
            LOG.error("Malformed idle screen registration received")

    def _on_show_idle(self, message):
        self.idle_ts = time.time()
        self._is_idle = True


class _GUIDict(dict):
    """
    This is a helper dictionary subclass. It ensures that values changed
    in it are propagated to the GUI service in real time.
    """

    def __init__(self, gui, **kwargs):
        self.gui = gui
        super().__init__(**kwargs)

    def __setitem__(self, key, value):
        super(_GUIDict, self).__setitem__(key, value)
        self.gui._sync_data()


class GUIInterface:
    """
    Interface to the Graphical User Interface, allows interaction with
    the mycroft-gui from anywhere

    Values set in this class are synced to the GUI, accessible within QML
    via the built-in sessionData mechanism.  For example, in Python you can
    write in a skill:
        self.gui['temp'] = 33
        self.gui.show_page('Weather.qml')
    Then in the Weather.qml you'd access the temp via code such as:
        text: sessionData.time
    """

    def __init__(self, skill_id: str, bus=None,
                 remote_server: str = None, config: dict = None,
                 ui_directories: dict = None):
        """
        Create an interface to the GUI module. Values set here are exposed to
        the GUI client as sessionData
        @param skill_id: ID of this interface
        @param bus: MessagebusClient object to connect to
        @param remote_server: Optional URL of a remote GUI server
        @param config: dict gui Configuration
        @param ui_directories: dict framework to directory containing resources
            `all` key should reference a `gui` directory containing all
            specific resource subdirectories
        """
        if not config:
            log_deprecation(f"Expected a dict config and got None.", "0.1.0")
            try:
                from ovos_config.config import read_mycroft_config
                config = read_mycroft_config().get("gui", {})
            except ImportError:
                LOG.warning("Config not provided and ovos_config not available")
                config = dict()
        self.config = config
        if remote_server:
            self.config["remote-server"] = remote_server
        self._bus = bus
        self.__session_data = {}  # synced to GUI for use by this skill's pages
        self._pages = []
        self.current_page_idx = -1
        self._skill_id = skill_id
        self.on_gui_changed_callback = None
        self._events = []
        self.ui_directories = ui_directories or dict()
        if bus:
            self.set_bus(bus)

    @property
    def remote_url(self) -> Optional[str]:
        """Returns configuration value for url of remote-server."""
        return self.config.get('remote-server')

    @remote_url.setter
    def remote_url(self, val: str):
        self.config["remote-server"] = val

    def set_bus(self, bus=None):
        self._bus = bus or get_mycroft_bus()
        self.setup_default_handlers()

    @property
    def bus(self):
        """
        Return the attached MessageBusClient
        """
        return self._bus

    @bus.setter
    def bus(self, val):
        self.set_bus(val)

    @property
    def skill_id(self) -> str:
        """
        Return the ID of the module implementing this interface
        """
        return self._skill_id

    @skill_id.setter
    def skill_id(self, val: str):
        self._skill_id = val

    @property
    def page(self) -> Optional[str]:
        """
        Return the active GUI page name to show
        """
        return self._pages[self.current_page_idx] if len(self._pages) else None

    @property
    def connected(self) -> bool:
        """
        Returns True if at least 1 remote gui is connected or if gui is
        installed and running locally, else False
        """
        if not self.bus:
            return False
        return can_use_gui(self.bus)

    @property
    def pages(self) -> List[str]:
        """
        Get a list of the active page ID's managed by this interface 
        """
        return self._pages

    def build_message_type(self, event: str) -> str:
        """
        Ensure the specified event prepends this interface's `skill_id`
        """
        if not event.startswith(f'{self.skill_id}.'):
            event = f'{self.skill_id}.' + event
        return event

    # events
    def setup_default_handlers(self):
        """
        Sets the handlers for the default messages.
        """
        msg_type = self.build_message_type('set')
        self.bus.on(msg_type, self.gui_set)
        self._events.append((msg_type, self.gui_set))
        self.bus.on("gui.request_page_upload", self.upload_gui_pages)
        if self.ui_directories:
            LOG.debug("Volunteering gui page upload")
            self.bus.emit(Message("gui.volunteer_page_upload",
                                  {'skill_id': self.skill_id},
                                  {'source': self.skill_id, "destination": ["gui"]}))

    def upload_gui_pages(self, message: Message):
        """
        Emit a response Message with all known GUI files managed by
        this interface for the requested infrastructure
        @param message: `gui.request_page_upload` Message requesting pages
        """
        if not self.ui_directories:
            LOG.debug("No UI resources to upload")
            return

        requested_skill = message.data.get("skill_id") or self._skill_id
        if requested_skill != self._skill_id:
            # GUI requesting a specific skill to upload other than this one
            return

        request_res_type = message.data.get("framework") or "all" if "all" in \
            self.ui_directories else "qt5"
        # Note that ui_directory "all" is a special case that will upload all
        # gui files, including all framework subdirectories
        if request_res_type not in self.ui_directories:
            LOG.warning(f"Requested UI files not available: {request_res_type}")
            return
        LOG.debug(f"Requested upload resources for: {request_res_type}")
        pages = dict()
        # `pages` keys are unique identifiers in the scope of this interface;
        # if ui_directory is "all", then pages are prefixed with `<framework>/`
        res_dir = self.ui_directories[request_res_type]
        for path, _, files in walk(res_dir):
            for file in files:
                try:
                    full_path: str = join(path, file)
                    page_name = full_path.replace(f"{res_dir}/", "", 1)
                    with open(full_path, 'rb') as f:
                        file_bytes = f.read()
                    pages[page_name] = file_bytes.hex()
                except Exception as e:
                    LOG.exception(f"{file} not uploaded: {e}")
        # Note that `pages` in this context include file extensions
        self.bus.emit(message.forward("gui.page.upload",
                                      {"__from": self.skill_id,
                                       "framework": request_res_type,
                                       "pages": pages}))

    def register_handler(self, event: str, handler: Callable):
        """
        Register a handler for GUI events.

        will be prepended with self.skill_id.XXX if missing in event

        When using the triggerEvent method from Qt
        triggerEvent("event", {"data": "cool"})

        Args:
            event (str):    event to catch
            handler:        function to handle the event
        """
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        event = self.build_message_type(event)
        self._events.append((event, handler))
        self.bus.on(event, handler)

    def set_on_gui_changed(self, callback: Callable):
        """
        Registers a callback function to run when a value is
        changed from the GUI.

        Arguments:
            callback:   Function to call when a value is changed
        """
        self.on_gui_changed_callback = callback

    # internals
    def gui_set(self, message: Message):
        """
        Handler catching variable changes from the GUI.

        Arguments:
            message: Messagebus message
        """
        for key in message.data:
            self[key] = message.data[key]
        if self.on_gui_changed_callback:
            self.on_gui_changed_callback()

    def _sync_data(self):
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        data = self.__session_data.copy()
        data.update({'__from': self.skill_id})
        self.bus.emit(Message("gui.value.set", data))

    def __setitem__(self, key, value):
        """Implements set part of dict-like behaviour with named keys."""

        # cast to helper dict subclass that syncs data
        if isinstance(value, dict) and not isinstance(value, _GUIDict):
            value = _GUIDict(self, **value)

        self.__session_data[key] = value

        # emit notification (but not needed if page has not been shown yet)
        if self.page:
            self._sync_data()

    def __getitem__(self, key):
        """Implements get part of dict-like behaviour with named keys."""
        return self.__session_data[key]

    def get(self, *args, **kwargs):
        """Implements the get method for accessing dict keys."""
        return self.__session_data.get(*args, **kwargs)

    def __contains__(self, key):
        """
        Implements the "in" operation.
        """
        return self.__session_data.__contains__(key)

    def clear(self):
        """
        Reset the value dictionary, and remove namespace from GUI.

        This method does not close the GUI for a Skill. For this purpose see
        the `release` method.
        """
        self.__session_data = {}
        self._pages = []
        self.current_page_idx = -1
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        self.bus.emit(Message("gui.clear.namespace",
                              {"__from": self.skill_id}))

    def send_event(self, event_name: str,
                   params: Union[dict, list, str, int, float, bool] = None):
        """
        Trigger a gui event.

        Arguments:
            event_name (str): name of event to be triggered
            params: json serializable object containing any parameters that
                    should be sent along with the request.
        """
        params = params or {}
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        self.bus.emit(Message("gui.event.send",
                              {"__from": self.skill_id,
                               "event_name": event_name,
                               "params": params}))

    def _pages2uri(self, page_names: List[str]) -> List[str]:
        """
        Get a list of resolved URIs from a list of string page names.
        @param page_names: List of GUI resource names (file basenames) to locate
        @return: List of resolved paths to the requested pages
        """
        # TODO: This method resolves absolute file paths. These will no longer
        #       be used with the implementation of `ovos-gui`
        page_urls = []
        extra_dirs = list(self.ui_directories.values()) or list()
        for name in page_names:
            # Prefer plugin-specific resources first, then fallback to core
            page = resolve_ovos_resource_file(name, extra_dirs) or \
                   resolve_ovos_resource_file(join('ui', name), extra_dirs) or \
                   resolve_resource_file(name, self.config) or \
                   resolve_resource_file(join('ui', name), self.config)

            if page:
                if self.remote_url:
                    page_urls.append(self.remote_url + "/" + page)
                elif page.startswith("file://"):
                    page_urls.append(page)
                else:
                    page_urls.append("file://" + page)
            else:
                LOG.error(f"Unable to find page: {name}")
        LOG.debug(f"Resolved pages: {page_urls}")
        return page_urls

    @staticmethod
    def _normalize_page_name(page_name: str) -> str:
        """
        Normalize a requested GUI resource
        @param page_name: string name of a GUI resource
        @return: normalized string name (`.qml` removed for other GUI support)
        """
        if isfile(page_name):
            log_deprecation("GUI resources should specify a resource name and "
                            "not a file path.", "0.1.0")
            return page_name
        file, ext = splitext(page_name)
        if ext == ".qml":
            log_deprecation("GUI resources should exclude gui-specific file "
                            f"extensions. This call should probably pass "
                            f"`{file}`, instead of `{page_name}`", "0.1.0")
            return file

        return page_name

    # base gui interactions
    def show_page(self, name: str, override_idle: Union[bool, int] = None,
                  override_animations: bool = False):
        """
        Request to show a page in the GUI.
        @param name: page resource requested
        @param override_idle: number of seconds to override display for;
            if True, override display indefinitely
        @param override_animations: if True, disables all GUI animations
        """
        self.show_pages([name], 0, override_idle, override_animations)

    def show_pages(self, page_names: List[str], index: int = 0,
                   override_idle: Union[bool, int] = None,
                   override_animations: bool = False):
        """
        Request to show a list of pages in the GUI.
        @param page_names: list of page resources requested
        @param index: position to insert pages at (default 0)
        @param override_idle: number of seconds to override display for;
            if True, override display indefinitely
        @param override_animations: if True, disables all GUI animations
        """
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        if isinstance(page_names, str):
            page_names = [page_names]
        if not isinstance(page_names, list):
            raise ValueError('page_names must be a list')

        if index > len(page_names):
            LOG.error('Default index is larger than page list length')
            index = len(page_names) - 1

        # TODO: deprecate sending page_urls after ovos_gui implementation
        page_urls = self._pages2uri(page_names)
        page_names = [self._normalize_page_name(n) for n in page_names]

        self._pages = page_names
        self.current_page_idx = index

        # First sync any data...
        data = self.__session_data.copy()
        data.update({'__from': self.skill_id})
        LOG.debug(f"Updating gui data: {data}")
        self.bus.emit(Message("gui.value.set", data))

        # finally tell gui what to show
        self.bus.emit(Message("gui.page.show",
                              {"page": page_urls,
                               "page_names": page_names,
                               "ui_directories": self.ui_directories,
                               "index": index,
                               "__from": self.skill_id,
                               "__idle": override_idle,
                               "__animations": override_animations}))

    def remove_page(self, page: str):
        """
        Remove a single page from the GUI.
        @param page: Name of page to remove
        """
        self.remove_pages([page])

    def remove_pages(self, page_names: List[str]):
        """
        Request to remove a list of pages from the GUI.
        @param page_names: list of page resources requested
        """
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        if isinstance(page_names, str):
            page_names = [page_names]
        if not isinstance(page_names, list):
            raise ValueError('page_names must be a list')
        # TODO: deprecate sending page_urls after ovos_gui implementation
        page_urls = self._pages2uri(page_names)
        page_names = [self._normalize_page_name(n) for n in page_names]
        self.bus.emit(Message("gui.page.delete",
                              {"page": page_urls,
                               "page_names": page_names,
                               "__from": self.skill_id}))

    # Utils / Templates

    # backport - PR https://github.com/MycroftAI/mycroft-core/pull/2862
    def show_notification(self, content: str, duration: int = 10,
                          action: str = None, noticetype: str = "transient",
                          style: str = "info",
                          callback_data: Optional[dict] = None):
        """Display a Notification on homepage in the GUI.
        Arguments:
            content (str): Main text content of a notification, Limited
            to two visual lines.
            duration (int): seconds to display notification for
            action (str): Callback to any event registered by the skill
            to perform a certain action when notification is clicked.
            noticetype (str):
                transient: 'Default' displays a notification with a timeout.
                sticky: displays a notification that sticks to the screen.
            style (str):
                info: 'Default' displays a notification with information styling
                warning: displays a notification with warning styling
                success: displays a notification with success styling
                error: displays a notification with error styling
            callback_data (dict): data dictionary available to use with action
        """
        # TODO: Define enums for style and noticetype
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        # GUI does not accept NONE type, send an empty dict
        # Sending NONE will corrupt entries in the model
        callback_data = callback_data or dict()
        self.bus.emit(Message("ovos.notification.api.set",
                              data={
                                  "duration": duration,
                                  "sender": self.skill_id,
                                  "text": content,
                                  "action": action,
                                  "type": noticetype,
                                  "style": style,
                                  "callback_data": callback_data
                              }))

    def show_controlled_notification(self, content: str, style: str = "info"):
        """
        Display a controlled Notification in the GUI.
        Arguments:
            content (str): Main text content of a notification, Limited
            to two visual lines.
            style (str):
                info: 'Default' displays a notification with information styling
                warning: displays a notification with warning styling
                success: displays a notification with success styling
                error: displays a notification with error styling
        """
        # TODO: Define enum for style
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        self.bus.emit(Message("ovos.notification.api.set.controlled",
                              data={
                                  "sender": self.skill_id,
                                  "text": content,
                                  "style": style
                              }))

    def remove_controlled_notification(self):
        """
        Remove a controlled Notification in the GUI.
        """
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        self.bus.emit(Message("ovos.notification.api.remove.controlled"))

    def show_text(self, text: str, title: Optional[str] = None,
                  override_idle: Union[int, bool] = None,
                  override_animations: bool = False):
        """
        Display a GUI page for viewing simple text.

        Arguments:
            text (str): Main text content.  It will auto-paginate
            title (str): A title to display above the text content.
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
            override_animations (boolean):
                True: Disables showing all platform skill animations.
                False: 'Default' always show animations.
        """
        self["text"] = text
        self["title"] = title
        self.show_page("SYSTEM_TextFrame.qml", override_idle,
                       override_animations)

    def show_image(self, url: str, caption: Optional[str] = None,
                   title: Optional[str] = None,
                   fill: str = None, background_color: str = None,
                   override_idle: Union[int, bool] = None,
                   override_animations: bool = False):
        """
        Display a GUI page for viewing an image.

        Arguments:
            url (str): Pointer to the image
            caption (str): A caption to show under the image
            title (str): A title to display above the image content
            fill (str): Fill type supports 'PreserveAspectFit',
            'PreserveAspectCrop', 'Stretch'
            background_color (str): A background color for
            the page in hex i.e. #000000
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
            override_animations (boolean):
                True: Disables showing all platform skill animations.
                False: 'Default' always show animations.
        """
        self["image"] = url
        self["title"] = title
        self["caption"] = caption
        self["fill"] = fill
        self["background_color"] = background_color
        self.show_page("SYSTEM_ImageFrame.qml", override_idle,
                       override_animations)

    def show_animated_image(self, url: str, caption: Optional[str] = None,
                            title: Optional[str] = None,
                            fill: str = None, background_color: str = None,
                            override_idle: Union[int, bool] = None,
                            override_animations: bool = False):
        """
        Display a GUI page for viewing an image.

        Args:
            url (str): Pointer to the .gif image
            caption (str): A caption to show under the image
            title (str): A title to display above the image content
            fill (str): Fill type supports 'PreserveAspectFit',
            'PreserveAspectCrop', 'Stretch'
            background_color (str): A background color for
            the page in hex i.e. #000000
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
            override_animations (boolean):
                True: Disables showing all platform skill animations.
                False: 'Default' always show animations.
        """
        self["image"] = url
        self["title"] = title
        self["caption"] = caption
        self["fill"] = fill
        self["background_color"] = background_color
        self.show_page("SYSTEM_AnimatedImageFrame.qml", override_idle,
                       override_animations)

    def show_html(self, html: str, resource_url: Optional[str] = None,
                  override_idle: Union[int, bool] = None,
                  override_animations: bool = False):
        """
        Display an HTML page in the GUI.

        Args:
            html (str): HTML text to display
            resource_url (str): Pointer to HTML resources
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
            override_animations (boolean):
                True: Disables showing all platform skill animations.
                False: 'Default' always show animations.
        """
        self["html"] = html
        self["resourceLocation"] = resource_url
        self.show_page("SYSTEM_HtmlFrame.qml", override_idle,
                       override_animations)

    def show_url(self, url: str, override_idle: Union[int, bool] = None,
                 override_animations: bool = False):
        """
        Display an HTML page in the GUI.

        Args:
            url (str): URL to render
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
            override_animations (boolean):
                True: Disables showing all platform skill animations.
                False: 'Default' always show animations.
        """
        self["url"] = url
        self.show_page("SYSTEM_UrlFrame.qml", override_idle,
                       override_animations)

    def show_input_box(self, title: Optional[str] = None,
                       placeholder: Optional[str] = None,
                       confirm_text: Optional[str] = None,
                       exit_text: Optional[str] = None,
                       override_idle: Union[int, bool] = None,
                       override_animations: bool = False):
        """
        Display a fullscreen UI for a user to enter text and confirm or cancel
        @param title: title of input UI should describe what the input is
        @param placeholder: default text hint to show in an empty entry box
        @param confirm_text: text to display on the submit/confirm button
        @param exit_text: text to display on the cancel/exit button
        @param override_idle: if True, takes over the resting page indefinitely
            else Delays resting page for the specified number of seconds.
        @param override_animations: disable showing all platform animations
        """
        self["title"] = title
        self["placeholder"] = placeholder
        self["skill_id_handler"] = self.skill_id
        if not confirm_text:
            self["confirm_text"] = "Confirm"
        else:
            self["confirm_text"] = confirm_text

        if not exit_text:
            self["exit_text"] = "Exit"
        else:
            self["exit_text"] = exit_text

        self.show_page("SYSTEM_InputBox.qml", override_idle,
                       override_animations)

    def remove_input_box(self):
        """
        Remove an input box shown by `show_input_box`
        """
        LOG.info(f"GUI pages length {len(self._pages)}")
        if len(self._pages) > 1:
            self.remove_page("SYSTEM_InputBox.qml")
        else:
            self.release()

    def release(self):
        """
        Signal that this skill is no longer using the GUI,
        allow different platforms to properly handle this event.
        Also calls self.clear() to reset the state variables
        Platforms can close the window or go back to previous page
        """
        if not self.bus:
            raise RuntimeError("bus not set, did you call self.bind() ?")
        self.clear()
        self.bus.emit(Message("mycroft.gui.screen.close",
                              {"skill_id": self.skill_id}))

    def shutdown(self):
        """
        Shutdown gui interface.

        Clear pages loaded through this interface and remove the bus events
        """
        if self.bus:
            self.release()
            for event, handler in self._events:
                self.bus.remove(event, handler)
