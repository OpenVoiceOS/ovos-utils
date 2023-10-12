import unittest
from threading import Event
from time import sleep
from unittest.mock import Mock

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


class TestIntentServiceInterfaceFunctions(unittest.TestCase):
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

    def test_intent_query_api(self):
        from ovos_utils.intents.intent_service_interface import IntentQueryApi
        # TODO

    def test_open_intent_envelope(self):
        pass
        # TODO: Deprecated?


class TestIntentServiceInterface(unittest.TestCase):
    from ovos_utils.intents.intent_service_interface import \
        IntentServiceInterface
    bus = FakeBus()
    intent_interface = IntentServiceInterface(bus)
    test_id = "test_interface.test"

    def test_00_init(self):
        self.assertEqual(self.intent_interface.bus, self.bus)
        self.intent_interface._bus = None
        self.assertIsNone(self.intent_interface._bus)
        self.assertIsInstance(self.intent_interface.skill_id, str)
        self.assertEqual(self.intent_interface.registered_intents, list())
        self.assertEqual(self.intent_interface.detached_intents, list())
        self.assertEqual(self.intent_interface.intent_names, list())

        with self.assertRaises(RuntimeError):
            _ = self.intent_interface.bus
        self.intent_interface.set_bus(self.bus)
        self.assertEqual(self.intent_interface.bus, self.bus)

        self.intent_interface.set_id(self.test_id)
        self.assertEqual(self.intent_interface.skill_id, self.test_id)

    def test_register_adapt_keyword(self):
        event = Event()

        register_vocab = Mock(side_effect=lambda x: event.set())

        self.bus.on("register_vocab", register_vocab)

        # Test without aliases
        event.clear()
        self.intent_interface.register_adapt_keyword('test_intent',
                                                     'test', lang='en-us')
        self.assertTrue(event.wait(2))
        register_vocab.assert_called_once()
        message = register_vocab.call_args[0][0]
        self.assertEqual(message.msg_type, "register_vocab")
        self.assertEqual(message.context,
                         {"skill_id": self.intent_interface.skill_id,
                          "session": message.context["session"]})
        data = message.data
        self.assertEqual(data['entity_value'], 'test')
        self.assertEqual(data['entity_type'], 'test_intent')
        self.assertEqual(data['lang'], 'en-us')

        # Test with aliases
        register_vocab.reset_mock()
        event.clear()
        self.intent_interface.register_adapt_keyword('test_intent', 'test',
                                                     ['test2', 'test3'],
                                                     'en-us')
        self.assertTrue(event.wait(2))
        while len(register_vocab.call_args_list) < 3:
            # TODO: Better method to wait for all of the expected calls
            sleep(0.2)
        self.assertEqual(register_vocab.call_count, 3)
        first_msg = register_vocab.call_args_list[0][0][0]
        second_msg = register_vocab.call_args_list[1][0][0]
        third_msg = register_vocab.call_args_list[2][0][0]
        self.assertEqual(first_msg.serialize(), message.serialize())
        self.assertEqual(second_msg.context, message.context)
        self.assertEqual(second_msg.data['entity_value'], 'test2')
        self.assertEqual(second_msg.data['entity_type'], 'test_intent')
        self.assertEqual(second_msg.data['lang'], 'en-us')
        self.assertEqual(third_msg.context, message.context)
        self.assertEqual(third_msg.data['entity_value'], 'test3')
        self.assertEqual(third_msg.data['entity_type'], 'test_intent')
        self.assertEqual(third_msg.data['lang'], 'en-us')

        self.bus.remove("register_vocab", register_vocab)

    def test_register_adapt_regex(self):
        valid_regex = "(is|as) (?P<rx_text>.*)"
        invalid_regex = "(is|as) no entity"
        called = Event()
        register_vocab = Mock(side_effect=lambda x: called.set())
        self.bus.on("register_vocab", register_vocab)
        lang = "en-gb"

        # Test valid regex
        self.intent_interface.register_adapt_regex(valid_regex, lang)
        self.assertTrue(called.wait(2))
        message = register_vocab.call_args[0][0]
        self.assertEqual(message.msg_type, "register_vocab")
        self.assertEqual(message.data['regex'], valid_regex)
        self.assertEqual(message.data['lang'], lang)
        self.assertEqual(message.context['skill_id'],
                         self.intent_interface.skill_id)

        # Test invalid regex (no validation in interface)
        called.clear()
        self.intent_interface.register_adapt_regex(invalid_regex, lang)
        self.assertTrue(called.wait(2))
        message = register_vocab.call_args[0][0]
        self.assertEqual(message.msg_type, "register_vocab")
        self.assertEqual(message.data['regex'], invalid_regex)
        self.assertEqual(message.data['lang'], lang)
        self.assertEqual(message.context['skill_id'],
                         self.intent_interface.skill_id)

        self.bus.remove("register_vocab", register_vocab)

    def test_register_adapt_intent(self):
        mock_adapt_intent = Mock()
        mock_intent_dict = {"name": "test_intent",
                            "requires": ['required_word'],
                            "at_least_one": ['opt1', 'opt2'],
                            "optional": []}
        mock_adapt_intent.__dict__ = mock_intent_dict

        event = Event()
        register_intent = Mock(side_effect=lambda x: event.set())
        self.bus.on("register_intent", register_intent)

        # Test register intent same name
        self.intent_interface.register_adapt_intent("test_intent",
                                                    mock_adapt_intent)
        self.assertTrue(event.wait(2))
        message = register_intent.call_args[0][0]
        self.assertEqual(message.msg_type, "register_intent")
        self.assertEqual(message.data, mock_intent_dict)
        self.assertEqual(message.context['skill_id'],
                         self.intent_interface.skill_id)
        self.assertEqual(self.intent_interface.registered_intents[-1],
                         ("test_intent", mock_adapt_intent))
        self.assertNotIn(("test_intent", mock_adapt_intent),
                         self.intent_interface.detached_intents)

        # Test register intent different name no longer detached
        event.clear()
        self.intent_interface.detached_intents.append(("test_detached",
                                                       mock_intent_dict))
        self.intent_interface.register_adapt_intent("test_detached",
                                                    mock_adapt_intent)
        self.assertTrue(event.wait(2))
        message = register_intent.call_args[0][0]
        self.assertEqual(message.msg_type, "register_intent")
        self.assertEqual(message.data, mock_intent_dict)
        self.assertEqual(message.context['skill_id'],
                         self.intent_interface.skill_id)
        self.assertEqual(self.intent_interface.registered_intents[-1],
                         ("test_detached", mock_adapt_intent))
        self.assertNotIn(("test_detached", mock_adapt_intent),
                         self.intent_interface.detached_intents)

        self.bus.remove("register_intent", register_intent)

    def test_remove_intent(self):
        test_name = "remove_intent"
        test_data = {"name": "remove"}

        event = Event()
        handle_detach = Mock(side_effect=lambda x: event.set())
        self.bus.on("detach_intent", handle_detach)

        # Test valid remove intent
        self.intent_interface.registered_intents.append((test_name, test_data))
        self.intent_interface.registered_intents.append((test_name, test_data))
        self.intent_interface.remove_intent(test_name)
        self.assertTrue(event.wait(2))
        handle_detach.assert_called_once()
        self.assertNotIn((test_name, test_data),
                         self.intent_interface.registered_intents)
        self.assertIn((test_name, test_data),
                      self.intent_interface.detached_intents)
        message = handle_detach.call_args[0][0]
        self.assertEqual(message.msg_type, "detach_intent")
        self.assertEqual(message.data['intent_name'],
                         f"{self.intent_interface.skill_id}:{test_name}")
        self.assertEqual(message.context['skill_id'],
                         self.intent_interface.skill_id)

        # Test invalid remove intent (no change)
        event.clear()
        self.intent_interface.remove_intent(test_name)
        self.assertTrue(event.wait(2))
        self.assertEqual(handle_detach.call_count, 2)
        new_message = handle_detach.call_args[0][0]
        self.assertEqual(message.serialize(), new_message.serialize())

        self.bus.remove("detach_intent", handle_detach)

    def test_intent_is_detached(self):
        detached_name = "is_detached"
        detached_mock = Mock()
        self.intent_interface.detached_intents.append((detached_name,
                                                       detached_mock))
        self.assertTrue(self.intent_interface.intent_is_detached(detached_name))
        self.assertFalse(self.intent_interface.intent_is_detached("not_detach"))

    def test_set_adapt_context(self):
        context = "ctx_key"
        word = "ctx_val"
        origin = "origin"

        event = Event()
        add_context = Mock(side_effect=lambda x: event.set())
        self.bus.on("add_context", add_context)

        self.intent_interface.set_adapt_context(context, word, origin)
        self.assertTrue(event.wait(2))
        add_context.assert_called_once()
        message = add_context.call_args[0][0]
        self.assertEqual(message.msg_type, "add_context")
        self.assertEqual(message.data, {"context": context,
                                        "word": word,
                                        "origin": origin})
        self.assertEqual(message.context['skill_id'],
                         self.intent_interface.skill_id)

        self.bus.remove("add_context", add_context)

    def test_remove_adapt_context(self):
        context = "ctx_key"

        event = Event()
        remove_context = Mock(side_effect=lambda x: event.set())
        self.bus.on("remove_context", remove_context)

        self.intent_interface.remove_adapt_context(context)
        self.assertTrue(event.wait(2))
        remove_context.assert_called_once()
        message = remove_context.call_args[0][0]
        self.assertEqual(message.msg_type, "remove_context")
        self.assertEqual(message.data, {"context": context})
        self.assertEqual(message.context['skill_id'],
                         self.intent_interface.skill_id)

        self.bus.remove("remove_context", remove_context)

    def test_register_padatious_intent(self):
        from pathlib import Path
        intent_name = "test"
        lang = "en-us"
        with self.assertRaises(ValueError):
            self.intent_interface.register_padatious_intent(intent_name, Path(),
                                                            lang)
        with self.assertRaises(FileNotFoundError):
            self.intent_interface.register_padatious_intent(intent_name,
                                                            "/test", lang)

        # TODO

    def test_register_padatious_entity(self):
        from pathlib import Path
        intent_name = "test"
        lang = "en-us"
        with self.assertRaises(ValueError):
            self.intent_interface.register_padatious_entity(intent_name, Path(),
                                                            lang)
        with self.assertRaises(FileNotFoundError):
            self.intent_interface.register_padatious_entity(intent_name,
                                                            "/test", lang)

        # TODO

    def test_detach_all(self):
        # TODO
        pass

    def test_get_intent(self):
        valid_intent = Mock()
        disabled_intent = Mock()
        self.intent_interface.registered_intents.append(("get_valid",
                                                         valid_intent))
        self.intent_interface.detached_intents.append(("get_disabled",
                                                       disabled_intent))
        self.assertEqual(self.intent_interface.get_intent("get_valid"),
                         valid_intent)
        self.assertEqual(self.intent_interface.get_intent("get_disabled"),
                         disabled_intent)
        self.assertIsNone(self.intent_interface.get_intent("invalid_intent"))

    def test_iter(self):
        self.intent_interface.registered_intents.append(("test_iter", Mock()))
        intents = []
        for intent in self.intent_interface:
            self.assertIn(intent, self.intent_interface.registered_intents)
            intents.append(intent)
        self.assertEqual(len(intents),
                         len(self.intent_interface.registered_intents))

    def test_contains(self):
        test_intent = ("test_contains", Mock())
        self.intent_interface.registered_intents.append(test_intent)
        self.assertTrue(test_intent[0] in self.intent_interface)
        self.assertFalse("test_not_contains" in self.intent_interface)
