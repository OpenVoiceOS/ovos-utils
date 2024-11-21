from ovos_utils.fakebus import dig_for_message, FakeMessage, FakeBus
from ovos_utils.log import log_deprecation


log_deprecation("ovos_utils.messagebus has been deprecated since version 0.1.0!! "
                "please import from ovos_utils.fakebus or ovos_bus_client directly", "1.0.0")


class Message(FakeMessage):
  """just for compat, stuff in the wild importing from here even with deprecation warnings..."""
  
  
