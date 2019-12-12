from jarbas_utils.log import LOG

try:
    from mycroft_bus_client import MessageBusClient, Message
except ImportError:
    # TODO add to setup.py blocked until https://github.com/MycroftAI/mycroft-messagebus-client is on pip
    # TODO create websocket connection manually or just wait?
    MessageBusClient = None

    class Message(dict):
        @property
        def type(self):
            return self.get("type", "mycroft_message")

        @property
        def data(self):
            return self.get("data", {})

        @property
        def context(self):
            return self.get("context", {})


def get_mycroft_bus():
    if MessageBusClient is None:
        LOG.error("pip install git+https://github.com/MycroftAI/mycroft-messagebus-client")
        raise ImportError("mycroft-messagebus-client not found")
    client = MessageBusClient()
    client.run_in_thread()
    return client
