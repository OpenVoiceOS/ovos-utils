import unittest

from ovos_utils.messagebus import FakeBus


class TestEnclosureAPI(unittest.TestCase):
    from ovos_utils.enclosure.api import EnclosureAPI
    bus = FakeBus()
    api = EnclosureAPI(bus)
    # TODO: Test api methods


class TestMark1(unittest.TestCase):
    # TODO Implement tests or move to separate PHAL plugin
    pass
