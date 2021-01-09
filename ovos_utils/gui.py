from ovos_utils.system import is_installed, has_screen
from ovos_utils.messagebus import wait_for_reply, get_mycroft_bus, Message
from ovos_utils.log import LOG
from collections import namedtuple
import time


def can_display():
    return has_screen()


def is_gui_installed():
    return is_installed("mycroft-gui-app")


def is_gui_connected(bus=None):
    # bus api for https://github.com/MycroftAI/mycroft-core/pull/2682
    # send "gui.status.request"
    # receive "gui.status.request.response"
    response = wait_for_reply("gui.status.request",
                              "gui.status.request.response", bus=bus)
    if response:
        return response.data["connected"]
    return False


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

    def __insert_pages(self, namespace, pages):
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

    def __insert_new_namespace(self, namespace, pages):
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
                new_pages = [p for p in pages if p not in self._loaded[0].pages]
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


if __name__ == "__main__":
    from ovos_utils import wait_for_exit_signal
    LOG.set_level("DEBUG")
    g = GUITracker()
    wait_for_exit_signal()