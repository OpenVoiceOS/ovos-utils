import unittest
from unittest.mock import patch

from ovos_utils.messagebus import FakeBus, Message


class TestEnclosureAPI(unittest.TestCase):
    from ovos_utils.enclosure.api import EnclosureAPI
    skill_id = "Enclosure Test"
    bus = FakeBus()
    api = EnclosureAPI(bus, skill_id)
    # TODO: Test api methods

    @patch('ovos_utils.enclosure.api.dig_for_message')
    def test_get_source_message(self, dig):
        # No message in stack
        dig.return_value = None
        msg = self.api._get_source_message()
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.context["destination"], ["enclosure"])
        self.assertEqual(msg.context["skill_id"], self.skill_id)

        # With message in stack
        test_message = Message("test", {"data": "something"},
                               {"source": [""], "destination": [""]})
        dig.return_value = test_message
        msg = self.api._get_source_message()
        self.assertEqual(msg, test_message)


class TestMark1(unittest.TestCase):
    # TODO Implement tests or move to separate PHAL plugin
    pass
