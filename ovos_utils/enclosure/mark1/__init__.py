from ovos_utils.enclosure.api import EnclosureAPI
from ovos_utils.log import log_deprecation

log_deprecation("ovos_utils.enclosure.mark1 moved to https://github.com/OpenVoiceOS/ovos-mark1-utils", "0.1.0")


class Mark1EnclosureAPI(EnclosureAPI):
    """ Mark1 enclosure, messagebus API"""
