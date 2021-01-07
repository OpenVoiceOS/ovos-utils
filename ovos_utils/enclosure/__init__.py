from ovos_utils.system import MycroftRootLocations
from ovos_utils.log import LOG
from enum import Enum
from os.path import exists, join


class MycroftEnclosures(str, Enum):
    PICROFT = "picroft"
    BIGSCREEN = "mycroft_mark_2"  # TODO handle bigscreen
    OVOS = "OpenVoiceOS"
    OLD_MARK1 = "mycroft_mark_1(old)"
    MARK1 = "mycroft_mark_1"
    MARK2 = "mycroft_mark_2"
    OTHER = "unknown"


def enclosure2rootdir(enclosure=None):
    enclosure = enclosure or detect_enclosure()
    if enclosure == MycroftEnclosures.OLD_MARK1:
        return MycroftRootLocations.OLD_MARK1
    elif enclosure == MycroftEnclosures.MARK1:
        return MycroftRootLocations.MARK1
    elif enclosure == MycroftEnclosures.MARK2:
        return MycroftRootLocations.MARK2
    elif enclosure == MycroftEnclosures.PICROFT:
        return MycroftRootLocations.PICROFT
    elif enclosure == MycroftEnclosures.OVOS:
        return MycroftRootLocations.OVOS
    elif enclosure == MycroftEnclosures.BIGSCREEN:
        return MycroftRootLocations.BIGSCREEN

    return None


def detect_enclosure():
    # TODO avoid circular import better
    # this is the only safe import to use from ovos_utils.configuration,
    # other methods are NOT, because they depend on this method directly,
    # ie, configuration objects use detect_enclosure
    from ovos_utils.configuration import MycroftSystemConfig

    # TODO very naive check, improve this
    # use db of reference fingerprints
    fingerprint = MycroftSystemConfig()\
        .get("enclosure", {}).get("platform", "unknown")
    if fingerprint == "OpenVoiceOS":
        return MycroftEnclosures.OVOS
    elif fingerprint == "mycroft_mark_1":
        if exists(MycroftRootLocations.OLD_MARK1):
            return MycroftEnclosures.OLD_MARK1
        return MycroftEnclosures.MARK1
    elif fingerprint == "mycroft_mark_2":
        # TODO bigscreen also reports this...
        return MycroftEnclosures.MARK2
    elif fingerprint == "picroft":
        return MycroftEnclosures.PICROFT

    return MycroftEnclosures.OTHER
