import unittest

from mock import mock, patch
from ovos_utils.messagebus import FakeBus


class TestIntent(unittest.TestCase):
    from ovos_utils.intents import Intent
    # TODO


class TestIntentBuilder(unittest.TestCase):
    from ovos_utils.intents import IntentBuilder
    # TODO


class TestAdaptIntent(unittest.TestCase):
    from ovos_utils.intents import AdaptIntent
    # TODO
    pass


class TestConverse(unittest.TestCase):
    from ovos_utils.intents.converse import ConverseTracker
    # TODO
    pass


class TestIntentServiceInterface(unittest.TestCase):
    def test_to_alnum(self):
        from ovos_utils.intents.intent_service_interface import to_alnum
        test_alnum = "test_skill123"
        self.assertEqual(test_alnum, to_alnum(test_alnum))
        test_dash = "test-skill123"
        self.assertEqual(test_alnum, to_alnum(test_dash))
        test_slash = "test/skill123"
        self.assertEqual(test_alnum, to_alnum(test_slash))

    def test_munge_regex(self):
        from ovos_utils.intents.intent_service_interface import munge_regex
        skill_id = "test_skill"
        non_regex = "just a string with no entity"
        with_regex = "a string with this (?P<entity>.*)"
        munged_regex = f"a string with this (?P<{skill_id}entity>.*)"

        self.assertEqual(non_regex, munge_regex(non_regex, skill_id))
        self.assertEqual(munged_regex, munge_regex(with_regex, skill_id))

    def test_munge_intent_parser(self):
        from ovos_utils.intents.intent_service_interface import \
            munge_intent_parser
        # TODO

    def test_intent_service_interface(self):
        from ovos_utils.intents.intent_service_interface import \
            IntentServiceInterface
        # TODO

    def test_intent_query_api(self):
        from ovos_utils.intents.intent_service_interface import IntentQueryApi
        # TODO

    def test_open_intent_envelope(self):
        pass
        # TODO: Deprecated?
