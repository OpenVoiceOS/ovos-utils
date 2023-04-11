from ovos_utils.system import MycroftRootLocations
from ovos_utils.fingerprinting import detect_platform, MycroftPlatform
from enum import Enum
from os.path import exists
from typing import Optional
from ovos_utils.log import LOG


class MycroftEnclosures(str, Enum):
    # TODO: Deprecate in 0.1.0
    PICROFT = "picroft"
    BIGSCREEN = "kde"
    OVOS = "OpenVoiceOS"
    OLD_MARK1 = "mycroft_mark_1(old)"
    MARK1 = "mycroft_mark_1"
    MARK2 = "mycroft_mark_2"
    HOLMESV = "HolmesV"
    OLD_HOLMES = "mycroft-lib"
    GENERIC = "generic"
    OTHER = "unknown"


def enclosure2rootdir(enclosure: MycroftEnclosures = None) -> Optional[str]:
    """
    Find the default installed core location for a specific platform.
    @param enclosure: MycroftEnclosures object to get root path for
    @return: string default root path
    """
    # TODO: Deprecate in 0.1.0
    LOG.warning("This method is deprecated. Code should import from the current"
                "namespace; other system paths are irrelevant.")
    enclosure = enclosure or detect_enclosure()
    if enclosure == MycroftEnclosures.OLD_MARK1:
        return MycroftRootLocations.OLD_MARK1
    elif enclosure == MycroftEnclosures.MARK1:
        return MycroftRootLocations.MARK1
    elif enclosure == MycroftEnclosures.MARK2:
        return MycroftRootLocations.MARK2
    elif enclosure == MycroftEnclosures.PICROFT:
        return MycroftPlatform.PICROFT
    elif enclosure == MycroftEnclosures.OVOS:
        return MycroftPlatform.OVOS
    elif enclosure == MycroftEnclosures.BIGSCREEN:
        return MycroftPlatform.BIGSCREEN
    return None


def detect_enclosure() -> MycroftEnclosures:
    """
    Determine which enclosure is present on this file system.
    @return: MycroftEnclosures object detected
    """
    # TODO: Deprecate in 0.1.0
    LOG.warning("This method is deprecated. Platform-specific code should"
                "use ovos_utils.fingerprinting.detect_platform directly")
    platform = detect_platform()
    if platform == MycroftPlatform.MARK1:
        if exists(MycroftRootLocations.OLD_MARK1):
            return MycroftEnclosures.OLD_MARK1
        return MycroftEnclosures.MARK1
    elif platform == MycroftPlatform.MARK2:
        return MycroftEnclosures.MARK2
    elif platform == MycroftPlatform.PICROFT:
        return MycroftEnclosures.PICROFT
    elif platform == MycroftPlatform.OVOS:
        return MycroftEnclosures.OVOS
    elif platform == MycroftPlatform.BIGSCREEN:
        return MycroftEnclosures.BIGSCREEN
    elif platform == MycroftPlatform.HOLMESV:
        return MycroftEnclosures.HOLMESV
    elif platform == MycroftPlatform.OLD_HOLMES:
        return MycroftEnclosures.OLD_HOLMES

    return MycroftEnclosures.OTHER
