import unittest

from mock import patch
from ovos_utils.messagebus import FakeBus


class TestEnclosureAPI(unittest.TestCase):
    from ovos_utils.enclosure.api import EnclosureAPI
    bus = FakeBus()
    api = EnclosureAPI(bus)
    # TODO: Test api methods


class TestMark1(unittest.TestCase):
    # TODO should this be removed from ovos-utils?
    pass
