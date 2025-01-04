from ovos_utils.fakebus import dig_for_message, Message, FakeMessage, FakeBus
from ovos_utils.log import log_deprecation


log_deprecation("ovos_utils.messagebus has been deprecated since version 0.1.0!! "
                "please import from ovos_utils.fakebus or ovos_bus_client directly", "1.0.0")

import warnings

warnings.warn(
    "ovos_utils.messagebus has been deprecated since version 0.1.0",
    DeprecationWarning,
    stacklevel=2,
)