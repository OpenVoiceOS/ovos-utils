from ovos_utils.enclosure.api import EnclosureAPI
from ovos_utils.log import LOG

LOG.warning("ovos_utils.enclosure.mark1 moved to https://github.com/OpenVoiceOS/ovos-mark1-utils ;"
            " this module will be removed in version 0.1.0")


class Mark1EnclosureAPI(EnclosureAPI):
    """ Mark1 enclosure, messagebus API"""
