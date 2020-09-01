from os import getpid
from os.path import basename
import json
from time import sleep
from pprint import pformat
import curses
import logging
logging.getLogger("mycroft_bus_client.client.client").setLevel("ERROR")

try:
    from jarbas_utils.messagebus import get_mycroft_bus, MessageBusClient,\
        Message
except ImportError:
    print("Run pip install jarbas_utils")
    raise


def get_websocket(host, port, route='/', ssl=False, threaded=False):
    """
    Returns a connection to a websocket
    """
    client = MessageBusClient(host, port, route, ssl)
    if threaded:
        client.run_in_thread()
    return client


class CursesGUI:
    def __init__(self, host="0.0.0.0", port=8181, name=None, debug=0,
                 refresh_rate=0.5):
        self.loaded = []
        self.skill = None
        self.page = None
        self.vars = {}
        self.mycroft_ip = host
        self.gui_ws = None
        self.name = name or self.__class__.__name__.lower()
        self.debug = debug
        self.connected = False
        self.buffer = []
        self._debug_msg = []
        self._init_curses()
        self.refresh_rate = refresh_rate
        self.bus = get_mycroft_bus(host, port)

    def _init_curses(self):
        # init curses
        self.window = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.window.keypad(1)
        curses.curs_set(0)

    def run(self):

        self.window.clrtobot()
        self.window.refresh()
        # process GUI input
        if not self.connected:
            self.connect()
        while True:
            sleep(self.refresh_rate)
            self.draw()

    @property
    def gui_id(self):
        return self.name + "_" + str(getpid())

    def connect(self):
        self._log_debug("Announcing GUI")
        self.bus.on('mycroft.gui.port', self._connect_to_gui)
        self.bus.emit(Message("mycroft.gui.connected",
                              {"gui_id": self.gui_id}))
        self.connected = True

    def _log_debug(self, log_msg):
        if self.debug > 0:
            self._debug_msg += ["[DEBUG] " + log_msg]
            if len(self._debug_msg) > self.debug:
                self._debug_msg = self._debug_msg[-self.debug:]

    def _connect_to_gui(self, msg):
        # Attempt to connect to the port
        gui_id = msg.data.get("gui_id")
        if not gui_id == self.gui_id:
            # Not us, ignore!
            return

        # Create the websocket for GUI communications
        port = msg.data.get("port")
        if port:
            self._log_debug("Connecting GUI on " + str(port))
            self.gui_ws = get_websocket(host=self.mycroft_ip,
                                        port=port, route="/gui")
            self.gui_ws.on("open", self.on_open)
            self.gui_ws.on("message", self.on_gui_message)
            self.gui_ws.run_in_thread()

    def on_open(self, message):
        self._log_debug("Gui connection open")

    def on_gui_message(self, payload):
        try:
            msg = json.loads(payload)
            self._log_debug("Msg: " + str(payload))
            msg_type = msg.get("type")
            if msg_type == "mycroft.session.set":
                self.skill = msg.get("namespace")
                data = msg.get("data")
                if self.skill not in self.vars:
                    self.vars[self.skill] = {}
                for d in data:
                    self.vars[self.skill][d] = data[d]
            elif msg_type == "mycroft.session.list.insert":
                # Insert new namespace
                self.skill = msg['data'][0]['skill_id']
                self.loaded.insert(0, [self.skill, []])
            elif msg_type == "mycroft.gui.list.insert":
                # Insert a page in an existing namespace
                self.page = msg['data'][0]['url']
                pos = msg.get('position')
                # TODO sometimes throws IndexError: list index out of range
                # not invalid json, seems like either pos is out of range or
                # "mycroft.session.list.insert" message was missed
                # NOTE: only happened once with wiki skill, cant replicate
                self.loaded[0][1].insert(pos, self.page)
                self.skill = self.loaded[0][0]
            elif msg_type == "mycroft.session.list.move":
                # Move the namespace at "pos" to the top of the stack
                pos = msg.get('from')
                self.loaded.insert(0, self.loaded.pop(pos))
            elif msg_type == "mycroft.events.triggered":
                # Switch selected page of namespace
                self.skill = msg['namespace']
                pos = msg['data']['number']
                for n in self.loaded:
                    if n[0] == self.skill:
                        # TODO sometimes pos throws
                        #  IndexError: list index out of range
                        # ocasionally happens with weather skill
                        # LOGS:
                        #   05:38:29.363 - __main__:on_gui_message:56 - DEBUG - Msg: {"type": "mycroft.events.triggered", "namespace": "mycroft-weather.mycroftai", "event_name": "page_gained_focus", "data": {"number": 1}}
                        #   05:38:29.364 - __main__:on_gui_message:90 - ERROR - list index out of range
                        self.page = n[1][pos]

            self._draw_buffer()
        except Exception as e:
            self._log_debug("Invalid JSON: " + str(payload))

    def _draw_buffer(self):
        self.buffer = []
        if self.skill:
            self.buffer.append("Active Skill:" + self.skill)

            if self.page:
                self.buffer.append("Page:" + basename(self.page))
            else:
                self.buffer.append("Page: None")

            if self.skill in self.vars:
                for v in dict(self.vars[self.skill]):
                    if self.vars[self.skill][v]:
                        self.buffer.append("{}:".format(v))
                        pretty = pformat(self.vars[self.skill][v])
                        for l in pretty.split("\n"):
                            self.buffer.append("    " + l)

    def draw(self):
        try:
            debug = "\n".join(self._debug_msg) + "\n" + 80 * "#"
            message = "\n".join(self.buffer)
            if self.debug > 0:
                message = debug + "\n" + message
            self.window.addstr(0, 0, message)
        except:
            pass
        self.window.clrtobot()
        self.window.refresh()


if __name__ == "__main__":
    gui = CursesGUI(debug=0)
    gui.run()
