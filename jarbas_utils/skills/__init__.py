from jarbas_utils.log import LOG
from jarbas_utils.messagebus import Message
from jarbas_utils.sound import wait_while_speaking
from jarbas_utils import get_mycroft_root, get_handler_name, dig_for_message
from jarbas_utils.lang.translate import detect_lang, translate_text

try:
    import mycroft.skills.mycroft_skill as mycroft_skill
    import mycroft.skills.fallback_skill as fallback_skill
except ImportError:
    import sys

    MYCROFT_ROOT_PATH = get_mycroft_root()
    if MYCROFT_ROOT_PATH is not None:
        sys.path.append(MYCROFT_ROOT_PATH)
        import mycroft.skills.mycroft_skill as mycroft_skill
        import mycroft.skills.fallback_skill as fallback_skill
    else:
        LOG.error("Could not find mycroft root path")
        raise ImportError


class MycroftSkill(mycroft_skill.MycroftSkill):
    pass


class FallbackSkill(fallback_skill.FallbackSkill):
    pass


class UniversalSkill(MycroftSkill):
    ''' Skill that auto translates input/output from any language '''

    def __init__(self, name=None, bus=None):
        super().__init__(name, bus)
        self.input_lang = self.lang
        self.translate_keys = []
        self.translate_tags = True

    def language_detect(self, utterance):
        try:
            return detect_lang(utterance)
        except:
            return self.lang.split("-")[0]

    def translate(self, text, lang=None):
        lang = lang or self.lang
        translated = translate_text(text, lang)
        LOG.info("translated " + text + " to " + translated)
        return translated

    def _translate_utterance(self, utterance="", lang=None):
        lang = lang or self.input_lang
        if utterance and lang is not None:
            ut_lang = self.language_detect(utterance)
            if lang.split("-")[0] != ut_lang:
                utterance = self.translate(utterance, lang)
        return utterance

    def _translate_message(self, message):
        ut = message.data.get("utterance")
        if ut:
            message.data["utterance"] = self._translate_utterance(ut)
        for key in self.translate_keys:
            if key in message.data:
                ut = message.data[key]
                message.data[key] = self._translate_utterance(ut)
        if self.translate_tags:
            for idx, token in enumerate(message.data["__tags__"]):
                message.data["__tags__"][idx] = self._translate_utterance(token.get("key", ""))
        return message

    def register_intent(self, intent_parser, handler):

        def universal_intent_handler(self, message):
            message = self._translate_message(message)
            LOG.info(get_handler_name(handler))
            handler(message)

        self.register_intent(intent_parser, universal_intent_handler)

    def register_intent_file(self, intent_file, handler):

        def universal_intent_handler(self, message):
            message = self._translate_message(message)
            LOG.info(get_handler_name(handler))
            handler(message)

        self.register_intent_file(intent_file, universal_intent_handler)

    def speak(self, utterance, expect_response=False, wait=False):
        # registers the skill as being active
        self.enclosure.register(self.name)
        utterance = self._translate_utterance(utterance)
        data = {'utterance': utterance,
                'expect_response': expect_response}
        message = dig_for_message()
        m = message.reply("speak", data) if message else Message("speak", data)
        self.bus.emit(m)

        if wait:
            wait_while_speaking()


class UniversalFallback(UniversalSkill, FallbackSkill):
    ''' Fallback Skill that auto translates input/output from any language '''

    def register_fallback(self, handler, priority):
        def _universal_fallback_handler(self, message):
            # auto_Translate input
            message = self._translate_message(message)
            LOG.info(self._handler_name)
            success = handler(self, message)
            if success:
                self.make_active()
            return success

        self.instance_fallback_handlers.append(_universal_fallback_handler)
        self._register_fallback(_universal_fallback_handler, priority)
