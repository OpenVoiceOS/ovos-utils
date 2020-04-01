from os import getpid
from os.path import basename
import json

from jarbas_utils.log import LOG
from jarbas_utils import wait_for_exit_signal, create_daemon
from jarbas_utils.messagebus import get_websocket, get_mycroft_bus, Message


class DummyGUI:
    def __init__(self, host="0.0.0.0", port=8181):
        self.bus = get_mycroft_bus(host, port)
        self.loaded = []
        self.skill = None
        self.page = None
        self.vars = {}
        self.mycroft_ip = host
        self.gui_ws = None

    @property
    def gui_id(self):
        return "dummy_" + str(getpid())

    def connect(self):
        LOG.debug("Announcing GUI")
        self.bus.on('mycroft.gui.port', self._connect_to_gui)
        self.bus.emit(Message("mycroft.gui.connected",
                              {"gui_id": self.gui_id}))

    def _connect_to_gui(self, msg):
        # Attempt to connect to the port
        gui_id = msg.data.get("gui_id")
        if not gui_id == self.gui_id:
            # Not us, ignore!
            return

        # Create the websocket for GUI communications
        port = msg.data.get("port")
        if port:
            LOG.info("Connecting GUI on " + str(port))
            self.gui_ws = get_websocket(host=self.mycroft_ip,
                                        port=port, route="/gui",
                                        threaded=False)

            def on_open(*args, **kwargs):
                # DEBUG ME: not called
                LOG.debug("Gui connecting open")

            self.gui_ws.on("open", on_open)
            self.gui_ws.on("message", self.on_gui_message)
            print("DEBUG: gui exists", self.gui_ws)
            self.gui_ws.run_in_thread()
            print("DEBUG: should be running")

    def on_gui_message(self, payload):
        # DEBUG ME: not called
        print(payload)
        try:
            msg = json.loads(payload)
            LOG.debug("Msg: " + str(payload))
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
                self.skill = msg.get('data')[0]['skill_id']
                self.loaded.insert(0, [self.skill, []])
            elif msg_type == "mycroft.gui.list.insert":
                # Insert a page in an existing namespace
                self.page = msg['data'][0]['url']
                pos = msg.get('position')
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
                        self.page = n[1][pos]

            self.draw()
        except Exception as e:
            LOG.exception(e)
            LOG.error("Invalid JSON: " + str(payload))

    def draw(self):
        print("################################")
        if self.skill:
            print("Active Skill: {}".format(self.skill))
            print("Page: {}".format(basename(self.page)))
            print("vars: ")
            for v in self.vars[self.skill]:
                print("     {}: {}".format(v, self.vars[self.skill][v]))
        print("################################")


if __name__ == "__main__":
    gui = DummyGUI()
    gui.connect()
    wait_for_exit_signal()
