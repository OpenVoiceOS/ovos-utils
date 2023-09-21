import re
from dataclasses import dataclass
from os.path import exists, isfile
from typing import List, Tuple, Optional

from ovos_utils import backwards_compat
from ovos_utils.log import LOG, deprecated
from ovos_utils.messagebus import get_mycroft_bus, Message, dig_for_message, get_message_lang


# TODO - calling these or not will depend on ovos-workshop version
#  where are these called?


# used in deprecated util - file_utils.load_vocabulary
def to_alnum(skill_id: str) -> str:
    """
    Convert a skill id to only alphanumeric characters
     Non-alphanumeric characters are converted to "_"

    Args:
        skill_id (str): identifier to be converted
    Returns:
        (str) String of letters
    """
    return ''.join(c if c.isalnum() else '_' for c in str(skill_id))


# used in deprecated util - file_utils.load_regex_from_file
# used in MycroftSkill.register_regex
def munge_regex(regex: str, skill_id: str) -> str:
    """
    Insert skill id as letters into match groups.

    Args:
        regex (str): regex string
        skill_id (str): skill identifier
    Returns:
        (str) munged regex
    """
    base = '(?P<' + to_alnum(skill_id)
    return base.join(regex.split('(?P<'))


# used in MycroftSkill.register_adapt_intent
def munge_intent_parser(intent_parser, name, skill_id):
    """
    Rename intent keywords to make them skill exclusive
    This gives the intent parser an exclusive name in the
    format <skill_id>:<name>.  The keywords are given unique
    names in the format <Skill id as letters><Intent name>.

    The function will not munge instances that's already been
    munged

    Args:
        intent_parser: (IntentParser) object to update
        name: (str) Skill name
        skill_id: (int) skill identifier
    """
    # Munge parser name
    if not name.startswith(str(skill_id) + ':'):
        intent_parser.name = str(skill_id) + ':' + name
    else:
        intent_parser.name = name

    # Munge keywords
    skill_id = to_alnum(skill_id)
    # Munge required keyword
    reqs = []
    for i in intent_parser.requires:
        if not i[0].startswith(skill_id):
            kw = (skill_id + i[0], skill_id + i[0])
            reqs.append(kw)
        else:
            reqs.append(i)
    intent_parser.requires = reqs

    # Munge optional keywords
    opts = []
    for i in intent_parser.optional:
        if not i[0].startswith(skill_id):
            kw = (skill_id + i[0], skill_id + i[0])
            opts.append(kw)
        else:
            opts.append(i)
    intent_parser.optional = opts

    # Munge at_least_one keywords
    at_least_one = []
    for i in intent_parser.at_least_one:
        element = [skill_id + e.replace(skill_id, '') for e in i]
        at_least_one.append(tuple(element))
    intent_parser.at_least_one = at_least_one


def unmunge_intent_parser(intent_parser, skill_id):
    # unMunge parser name
    if intent_parser.name.startswith(f'{skill_id}:'):
        intent_parser.name = intent_parser.name.replace(f'{skill_id}:', "")

    # unMunge keywords
    skill_id = to_alnum(skill_id)
    # unMunge required keyword
    reqs = []
    for i in intent_parser.requires:
        if i[0].startswith(skill_id):
            unmunged = i[0][len(skill_id):]
            kw = (unmunged, unmunged)
            reqs.append(kw)
        else:
            reqs.append(i)
    intent_parser.requires = reqs

    # unMunge optional keywords
    opts = []
    for i in intent_parser.optional:
        if i[0].startswith(skill_id):
            unmunged = i[0][len(skill_id):]
            kw = (unmunged, unmunged)
            opts.append(kw)
        else:
            opts.append(i)
    intent_parser.optional = opts

    # unMunge at_least_one keywords
    at_least_one = []
    for i in intent_parser.at_least_one:
        element = [e[len(skill_id):] if e.startswith(skill_id) else e
                   for e in i]
        at_least_one.append(tuple(element))
    intent_parser.at_least_one = at_least_one


@dataclass
class IntentHandler:
    """ contains references to intent methods registered in the IntentServiceInterface"""
    name: str  # the intent name
    skill_id: str  # the skill_id the intent belongs to
    intent_message: str  # the bus event that triggers the intent (usually munged skill_id + name)
    register_message: Message  # to enable/disable on demand
    detached: bool = True

    def register(self, bus):
        bus.emit(self.register_message)
        self.detached = False


class IntentServiceInterface:
    """
    Interface to communicate with the Mycroft intent service.

    This class wraps the messagebus interface of the intent service allowing
    for easier interaction with the service. It wraps both the Adapt and
    Padatious parts of the intent services.
    """

    def __init__(self, bus=None, skill_id=None):
        self._bus = bus
        self.skill_id = skill_id or self.__class__.__name__
        self.intents: List[IntentHandler] = []

    @property
    def alphanumeric_skill_id(self) -> str:
        """
        Skill id converted to only alphanumeric characters and "_".
        Non alphanumeric characters are converted to "_"
        """
        return ''.join(c if c.isalnum() else '_'
                       for c in str(self.skill_id))

    @property
    @deprecated("self.registered_intents has been deprecated, iterate over self.intents instead", "0.1.0")
    def registered_intents(self) -> List[Tuple[str, object]]:
        return [(e.name, e) for e in self.intents if not e.detached]

    @property
    @deprecated("self.detached_intents has been deprecated, iterate over self.intents instead", "0.1.0")
    def detached_intents(self) -> List[Tuple[str, object]]:
        return [(e.name, e) for e in self.intents if e.detached]

    def enable_intent(self, name: str):
        for intent in self.intents:
            if intent.name == name and intent.detached:
                intent.register(self.bus)
                return True
        return False

    def disable_intent(self, name: str):
        for intent in self.intents:
            if intent.name == name and not intent.detached:
                self.remove_intent(name)
                return True
        return False

    @property
    def intent_names(self) -> List[str]:
        """
        Get a list of intent names (both registered and disabled).
        """
        return [a.name for a in self.intents]

    # initialization
    @property
    def bus(self):
        if not self._bus:
            raise RuntimeError("bus not set. call `set_bus()` before trying to"
                               "interact with the Messagebus")
        return self._bus

    @bus.setter
    def bus(self, val):
        self.set_bus(val)

    def set_bus(self, bus=None):
        self._bus = bus or get_mycroft_bus()

    def set_id(self, skill_id: str):
        self.skill_id = skill_id

    # VUI - skills/apps use these to register intents
    @deprecated("register_adapt_keyword has been deprecated,"
                " use register_keyword and register_keyword_intent instead", "0.1.0")
    def register_adapt_keyword(self, vocab_type: str, entity: str,
                               aliases: Optional[List[str]] = None,
                               lang: str = None):
        """
        Send a message to the intent service to add an Adapt keyword.
        @param vocab_type: Keyword reference (file basename)
        @param entity: Primary keyword value
        @param aliases: List of alternative keyword values
        @param lang: BCP-47 language code of entity and aliases
        """
        # keyword_type = self.alphanumeric_skill_id + entity_type
        vocab_type = vocab_type.replace(self.alphanumeric_skill_id, "")  # unmunge
        return self.register_keyword(name=vocab_type, samples=[entity] + aliases, lang=lang)

    def __register_keyword_classic(self, name: str, samples: list,
                                   lang: str = None, skill_id: str = None):
        skill_id = skill_id or self.skill_id
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = skill_id

        # munge as expected by classic core
        name = self.alphanumeric_skill_id + name
        for s in samples:
            entity_data = {'entity_value': s,
                           'entity_type': name,
                           "skill_id": skill_id,
                           'lang': lang}
            compatibility_data = {'start': s, 'end': name}  # very old mycroft-core

            self.bus.emit(msg.forward("register_vocab",
                                      {**entity_data, **compatibility_data}))

    @backwards_compat(pre_008=__register_keyword_classic,
                      classic_core=__register_keyword_classic,
                      no_core=__register_keyword_classic)  # TODO - drop no_core once widely used in the wild
    def register_keyword(self, name: str, samples: list, lang: str = None, skill_id: str = None):
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        self.bus.emit(msg.forward("intent.service:register_keyword",
                                  {"name": name,
                                   "skill_id": skill_id or self.skill_id,
                                   "lang": lang or get_message_lang(msg),
                                   "samples": samples}
                                  ))

    @deprecated("register_adapt_regex has been deprecated,"
                " use register_regex_entity and register_keyword_intent instead", "0.1.0")
    def register_adapt_regex(self, regex: str, lang: str = None):
        """
        Register a regex string with the intent service.
        @param regex: Regex to be registered; Adapt extracts keyword references
            from named match group.
        @param lang: BCP-47 language code of regex
        """
        unmunged = regex  # TODO undo output of munge_regex()
        name = ""  # TODO - get from regex_str
        re.compile(unmunged)  # validate regex
        self.register_regex_entity(name=name, samples=[unmunged], lang=lang)

    def __register_regex_entity_classic(self, name: str, samples: list,
                                        lang: str = None, skill_id: str = None):
        skill_id = skill_id or self.skill_id
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        regex = samples[0]
        re.compile(regex)  # validate regex
        self.bus.emit(msg.forward("register_vocab",
                                  {'regex': regex,
                                   'lang': lang,
                                   "entity_type": name,  # ignored in adapt, name comes from regex itself
                                   "skill_id": skill_id
                                   }))

    @backwards_compat(pre_008=__register_regex_entity_classic,
                      classic_core=__register_regex_entity_classic,
                      no_core=__register_regex_entity_classic)  # TODO - drop no_core once widely used in the wild
    def register_regex_entity(self, name: str, samples: list, lang: str = None, skill_id: str = None):
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        for regex in samples:
            re.compile(regex)  # validate regex
        self.bus.emit(msg.forward("intent.service:register_regex_entity",
                                  {"name": name,
                                   "skill_id": skill_id or self.skill_id,
                                   "lang": lang or get_message_lang(msg),
                                   "samples": samples}
                                  ))

    @deprecated("register_adapt_intent has been deprecated,"
                " use register_keyword_intent instead", "0.1.0")
    def register_adapt_intent(self, name: str, intent_parser: object) -> IntentHandler:
        """
        Register an Adapt intent parser object. Serializes the intent_parser
        and sends it over the messagebus to registered.
        @param name: string intent name (without skill_id prefix)
        @param intent_parser: Adapt Intent object
        """
        # undo munge_intent_parser()
        intent_parser = unmunge_intent_parser(intent_parser, self.skill_id)
        return self.register_keyword_intent(name=name,
                                            required=intent_parser.requires,
                                            at_least_one=intent_parser.at_least_one,
                                            optional=intent_parser.optional)

    def __register_keyword_intent_classic(self, name: str, required: list,
                                          optional: list = None, at_least_one: list = None,
                                          excluded: list = None, lang=None, skill_id: str = None) -> IntentHandler:
        skill_id = skill_id or self.skill_id
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id

        if excluded:
            LOG.error(f"excluded keywords only available in ovos-core >= 0.0.8,"
                      f" intent {name} may misbehave")
        msg = msg.forward("register_intent",
                          {"name": name,
                           "skill_id": skill_id,
                           "lang": lang or get_message_lang(msg),
                           "optional": optional,
                           "excludes": excluded,
                           "requires": required,
                           "at_least_one": at_least_one}
                          )
        self.bus.emit(msg)
        return self._add_intent(name, skill_id, msg)

    @backwards_compat(pre_008=__register_keyword_intent_classic,
                      classic_core=__register_keyword_intent_classic,
                      no_core=__register_keyword_intent_classic)  # TODO - drop no_core once widely used in the wild
    def register_keyword_intent(self, name: str, required: list,
                                optional: list = None, at_least_one: list = None,
                                excluded: list = None, lang=None, skill_id: str = None) -> IntentHandler:
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        msg = msg.forward("intent.service.register_keyword_intent",
                          {"name": name,
                           "skill_id": skill_id or self.skill_id,
                           "lang": lang or get_message_lang(msg),
                           "optional": optional,
                           "excludes": excluded,
                           "requires": required,
                           "at_least_one": at_least_one}
                          )
        self.bus.emit(msg)
        return self._add_intent(name, skill_id, msg)

    @deprecated(f"detach_intent replaced by remove_intent", "0.1.0")
    def detach_intent(self, intent_name: str):
        """
        intent_name: munged intent_name  f'{self.skill_id}:{name}'

        DEPRECATED: Use `remove_intent` instead, all other methods from this
        class expect intent_name; this was the weird one expecting the internal
        munged intent_name with skill_id.
        """
        # used in MycroftSkill.detach
        name = intent_name.split(':')[1]
        self.remove_intent(name)

    def __old_remove_intent(self, intent_name: str):
        """
        Remove an intent from the intent service. The intent is saved in the
        list of detached intents for use when re-enabling an intent. A
        `detach_intent` Message is emitted for the intent service to handle.
        @param intent_name: Registered intent to remove/detach (no skill_id)
        """
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id

        for intent in self.intents:
            if intent.name == intent_name:
                intent.detached = True

        self.bus.emit(msg.forward("detach_intent",
                                  {"intent_name": f"{self.skill_id}:{intent_name}"}))

    @backwards_compat(classic_core=__old_remove_intent, pre_008=__old_remove_intent)
    def remove_intent(self, intent_name: str):
        """
        Remove an intent from the intent service. The intent is saved in the
        list of detached intents for use when re-enabling an intent. A
        `detach_intent` Message is emitted for the intent service to handle.
        @param intent_name: Registered intent to remove/detach (no skill_id)
        """
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id

        for intent in self.intents:
            if intent.name == intent_name:
                intent.detached = True

        self.bus.emit(msg.forward("intent.service:detach_intent",
                                  {"intent_name": intent_name,
                                   "skill_id": self.skill_id}))

    def intent_is_detached(self, intent_name: str) -> bool:
        """
        Determine if an intent is detached.
        @param intent_name: String intent reference to check (without skill_id)
        @return: True if intent is in detached_intents, else False.
        """
        for intent in self.intents:
            if intent.name == intent_name:
                return intent.detached
        return False

    @deprecated("set_adapt_context has been deprecated,"
                " use set_context instead", "0.1.0")
    def set_adapt_context(self, context: str, word: str, origin: str):
        """
        Set an Adapt context.
        @param context: context keyword name to add/update
        @param word: word to register (context keyword value)
        @param origin: original origin of the context (for cross context)
        """
        # unmunge context = self._alphanumeric_skill_id + context
        context = context[len(self.alphanumeric_skill_id):]
        self.set_context(context, word, origin)

    def _set_context_old(self, context: str, word: str, origin: str):
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        # munge as expected by classic core
        context = self.alphanumeric_skill_id + context
        self.bus.emit(msg.forward('add_context',
                                  {'context': context, 'word': word,
                                   'origin': origin}))

    @backwards_compat(classic_core=_set_context_old,
                      pre_008=_set_context_old,
                      no_core=_set_context_old)
    def set_context(self, context: str, word: str, origin: str):
        """
        Set a Session context.
        @param context: context keyword name to add/update
        @param word: word to register (context keyword value)
        @param origin: original origin of the context (for cross context)
        """
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        self.bus.emit(msg.forward('add_context',
                                  {'context': context, 'word': word,
                                   'origin': origin}))

    @deprecated("remove_adapt_context has been deprecated,"
                " use remove_context instead", "0.1.0")
    def remove_adapt_context(self, context: str):
        """
        Remove an Adapt context.
        @param context: context keyword name to remove
        """
        # unmunge context = self._alphanumeric_skill_id + context
        context = context[len(self.alphanumeric_skill_id):]
        self.remove_context(context)

    def _remove_context_old(self, context: str):
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        # munge as expected by classic core
        context = self.alphanumeric_skill_id + context
        self.bus.emit(msg.forward('remove_context', {'context': context}))

    @backwards_compat(classic_core=_remove_context_old,
                      pre_008=_remove_context_old,
                      no_core=_remove_context_old)
    def remove_context(self, context: str):
        """
        Remove a Session Context.
        @param context: context keyword name to remove
        """
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        self.bus.emit(msg.forward('remove_context', {'context': context}))

    @deprecated("register_padatious_intent has been deprecated,"
                " use register_intent instead", "0.1.0")
    def register_padatious_intent(self, intent_name: str, filename: str,
                                  lang: str) -> IntentHandler:
        """
        Register a Padatious intent file with the intent service.
        @param intent_name: Unique intent identifier
            (usually `skill_id`:`filename`)
        @param filename: Absolute file path to entity file
        @param lang: BCP-47 language code of registered intent
        """
        if not isinstance(filename, str):
            raise ValueError('Filename path must be a string')
        if not exists(filename):
            raise FileNotFoundError(f'Unable to find "{filename}"')
        with open(filename) as f:
            samples = [_ for _ in f.read().split("\n") if _
                       and not _.startswith("#")]
        skill_id, intent_file = intent_name.split(":")  # munged
        intent_name = intent_file.replace(".intent", "")
        return self.register_intent(name=intent_name, samples=samples,
                                    lang=lang, skill_id=skill_id)

    def __register_intent_classic(self, name: str, samples: list,
                                  lang=None, skill_id: str = None) -> IntentHandler:
        """ does not support 'samples' only 'file_name',
        old namespace,
        core expects munged name"""
        skill_id = skill_id or self.skill_id
        filename = f"/tmp/{name}_{skill_id}_{lang}.intent"
        with open(filename, "w") as f:
            f.write("\n".join(samples))

        data = {'file_name': filename,  # samples not supported
                'name': f"{skill_id}:{name}",  # old core expects munged name
                "skill_id": skill_id,
                'lang': lang}
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        msg = msg.forward("padatious:register_intent", data)
        self.bus.emit(msg)
        return self._add_intent(name, skill_id, msg)

    def __register_intent_old(self, name: str, samples: list,
                              lang=None, skill_id: str = None) -> IntentHandler:
        """ old namespace, core expects munged name"""
        skill_id = skill_id or self.skill_id
        data = {"samples": samples,
                'name': f"{skill_id}:{name}",  # old core expects munged name
                "skill_id": skill_id,
                'lang': lang}
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        msg = msg.forward("padatious:register_intent", data)
        self.bus.emit(msg)
        return self._add_intent(name, skill_id, msg)

    @backwards_compat(pre_008=__register_intent_old,
                      no_core=__register_intent_old,
                      classic_core=__register_intent_classic)
    def register_intent(self, name: str, samples: list,
                        lang=None, skill_id: str = None) -> IntentHandler:
        skill_id = skill_id or self.skill_id
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        msg = msg.forward("intent.service:register_intent",
                          {"name": name,  # not munged
                           "skill_id": skill_id,
                           "lang": lang or get_message_lang(msg),
                           "samples": samples}
                          )
        self.bus.emit(msg)
        return self._add_intent(name, skill_id, msg)

    def _add_intent(self, name: str, skill_id: str, message: Message) -> IntentHandler:
        for intent in self.intents:
            if intent.name == name and intent.skill_id == skill_id:  # intent in detached mode
                intent.detached = False  # mark as re-enabled
                return intent
        else:  # new intent
            intent_message = f"{name}:{skill_id}"
            intent = IntentHandler(name=name, intent_message=intent_message,
                                   skill_id=skill_id, detached=False,
                                   register_message=message)
            self.intents.append(intent)
            return intent

    @deprecated("register_padatious_entity has been deprecated,"
                " use register_entity instead", "0.1.0")
    def register_padatious_entity(self, entity_name: str, filename: str,
                                  lang: str):
        """
        Register a Padatious entity file with the intent service.
        @param entity_name: Unique entity identifier
            (usually `skill_id`:`filename`)
        @param filename: Absolute file path to entity file
        @param lang: BCP-47 language code of registered intent
        """
        #             name = f"{self.skill_id}:{basename(entity_file)}_" \
        #                    f"{md5(entity_file.encode('utf-8')).hexdigest()}"
        skill_id, entity_name = entity_name.split(":")
        if not isinstance(filename, str):
            raise ValueError('Filename path must be a string')
        if not exists(filename):
            raise FileNotFoundError('Unable to find "{}"'.format(filename))
        with open(filename) as f:
            samples = [_ for _ in f.read().split("\n") if _
                       and not _.startswith("#")]
        self.register_entity(name=entity_name, samples=samples,
                             lang=lang, skill_id=skill_id)

    def __register_entity_classic(self, name: str, samples: list, lang: str = None, skill_id: str = None):
        """file_name instead of samples, old bus api, old namespace"""
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        filename = f"/tmp/{name}_{skill_id}_{lang}.entity"
        with open(filename, "w") as f:
            f.write("\n".join(samples))
        # expects munged name
        name = f"{skill_id}:{name}"
        self.bus.emit(msg.forward("padatious:register_entity",
                                  {"name": name,
                                   "skill_id": skill_id or self.skill_id,
                                   "lang": lang or get_message_lang(msg),
                                   "file_name": filename}
                                  ))

    def __register_entity_old(self, name: str, samples: list, lang: str = None, skill_id: str = None):
        """old bus api, old namespace"""
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        # expects munged name
        name = f"{skill_id}:{name}"
        self.bus.emit(msg.forward("padatious:register_entity",
                                  {"name": name,
                                   "skill_id": skill_id or self.skill_id,
                                   "lang": lang or get_message_lang(msg),
                                   "samples": samples}
                                  ))

    @backwards_compat(pre_008=__register_entity_old,
                      classic_core=__register_entity_classic,
                      no_core=__register_entity_old)  # TODO - drop no_core once widely used in the wild
    def register_entity(self, name: str, samples: list, lang: str = None, skill_id: str = None):
        msg = dig_for_message() or Message("")
        msg.context["skill_id"] = self.skill_id
        self.bus.emit(msg.forward("intent.service:register_entity",
                                  {"name": name,
                                   "skill_id": skill_id or self.skill_id,
                                   "lang": lang or get_message_lang(msg),
                                   "samples": samples}
                                  ))

    @deprecated("Reference `self.intent_names` property instead", "0.1.0")
    def get_intent_names(self):
        return self.intent_names

    def detach_all(self):
        """
        Detach all intents associated with this interface and remove all
        internal references to intents and handlers.
        """
        for name in self.intent_names:
            self.remove_intent(name)
        self.intents = []  # Explicitly remove all intent references

    def __old_get_intent(self, intent_name: str) -> Optional[object]:
        """
        Get an intent object by name. This will find both enabled and disabled
        intents.
        @param intent_name: name of intent to find (without skill_id)
        @return: intent object if found, else None
        """
        for intent in self.intents:
            if intent.name == intent_name:
                return intent  # TODO - what is the return type here?

    @backwards_compat(classic_core=__old_get_intent, pre_008=__old_get_intent)
    def get_intent(self, intent_name: str) -> Optional[IntentHandler]:
        for intent in self.intents:
            if intent.name == intent_name:
                return intent

    def __iter_old(self):
        """Iterator over the registered intents.
        Returns an iterator returning name-handler pairs of the registered
        intent handlers.
        """
        return iter((i.name, {}) for i in self.intents)  # TODO - what is the return type here?

    @backwards_compat(classic_core=__iter_old, pre_008=__iter_old)
    def __iter__(self):
        """Iterator over the registered intents.

        Returns an iterator returning IntentHandler objects
        """
        return iter(self.intents)

    def __contains__(self, val):
        """
        Checks if an intent name has been registered.
        """
        return val in [i.name for i in self.intents]


# TODO - update whole class
class IntentQueryApi:
    """
    Query Intent Service at runtime
    """

    def __init__(self, bus=None, timeout=5):
        if bus is None:
            bus = get_mycroft_bus()
        self.bus = bus
        self.timeout = timeout

    def get_adapt_intent(self, utterance, lang="en-us"):
        """ get best adapt intent for utterance """
        msg = Message("intent.service.adapt.get",
                      {"utterance": utterance, "lang": lang},
                      context={"destination": "intent_service",
                               "source": "intent_api"})

        resp = self.bus.wait_for_response(msg,
                                          'intent.service.adapt.reply',
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None
        return data["intent"]

    def get_padatious_intent(self, utterance, lang="en-us"):
        """ get best padatious intent for utterance """
        msg = Message("intent.service.padatious.get",
                      {"utterance": utterance, "lang": lang},
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        resp = self.bus.wait_for_response(msg,
                                          'intent.service.padatious.reply',
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None
        return data["intent"]

    def get_intent(self, utterance, lang="en-us"):
        """ get best intent for utterance """
        msg = Message("intent.service.intent.get",
                      {"utterance": utterance, "lang": lang},
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        resp = self.bus.wait_for_response(msg,
                                          'intent.service.intent.reply',
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None
        return data["intent"]

    def get_skill(self, utterance, lang="en-us"):
        """ get skill that utterance will trigger """
        intent = self.get_intent(utterance, lang)
        if not intent:
            return None
        # theoretically skill_id might be missing
        if intent.get("skill_id"):
            return intent["skill_id"]
        # retrieve skill from munged intent name
        if intent.get("intent_name"):  # padatious + adapt
            return intent["name"].split(":")[0]
        if intent.get("intent_type"):  # adapt
            return intent["intent_type"].split(":")[0]
        return None  # raise some error here maybe? this should never happen

    def get_skills_manifest(self):
        msg = Message("intent.service.skills.get",
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        resp = self.bus.wait_for_response(msg,
                                          'intent.service.skills.reply',
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None
        return data["skills"]

    def get_active_skills(self, include_timestamps=False):
        msg = Message("intent.service.active_skills.get",
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        resp = self.bus.wait_for_response(msg,
                                          'intent.service.active_skills.reply',
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None
        if include_timestamps:
            return data["skills"]
        return [s[0] for s in data["skills"]]

    def get_adapt_manifest(self):
        msg = Message("intent.service.adapt.manifest.get",
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        resp = self.bus.wait_for_response(msg,
                                          'intent.service.adapt.manifest',
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None
        return data["intents"]

    def get_padatious_manifest(self):
        msg = Message("intent.service.padatious.manifest.get",
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        resp = self.bus.wait_for_response(msg,
                                          'intent.service.padatious.manifest',
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None
        return data["intents"]

    def get_intent_manifest(self):
        padatious = self.get_padatious_manifest()
        adapt = self.get_adapt_manifest()
        return {"adapt": adapt,
                "padatious": padatious}

    def get_vocab_manifest(self):
        msg = Message("intent.service.adapt.vocab.manifest.get",
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        reply_msg_type = 'intent.service.adapt.vocab.manifest'
        resp = self.bus.wait_for_response(msg,
                                          reply_msg_type,
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None

        vocab = {}
        for voc in data["vocab"]:
            if voc.get("regex"):
                continue
            if voc["end"] not in vocab:
                vocab[voc["end"]] = {"samples": []}
            vocab[voc["end"]]["samples"].append(voc["start"])
        return [{"name": voc, "samples": vocab[voc]["samples"]}
                for voc in vocab]

    def get_regex_manifest(self):
        msg = Message("intent.service.adapt.vocab.manifest.get",
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        reply_msg_type = 'intent.service.adapt.vocab.manifest'
        resp = self.bus.wait_for_response(msg,
                                          reply_msg_type,
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None

        vocab = {}
        for voc in data["vocab"]:
            if not voc.get("regex"):
                continue
            name = voc["regex"].split("(?P<")[-1].split(">")[0]
            if name not in vocab:
                vocab[name] = {"samples": []}
            vocab[name]["samples"].append(voc["regex"])
        return [{"name": voc, "regexes": vocab[voc]["samples"]}
                for voc in vocab]

    def get_entities_manifest(self):
        msg = Message("intent.service.padatious.entities.manifest.get",
                      context={"destination": "intent_service",
                               "source": "intent_api"})
        reply_msg_type = 'intent.service.padatious.entities.manifest'
        resp = self.bus.wait_for_response(msg,
                                          reply_msg_type,
                                          timeout=self.timeout)
        data = resp.data if resp is not None else {}
        if not data:
            LOG.error("Intent Service timed out!")
            return None

        entities = []
        # read files
        for ent in data["entities"]:
            if isfile(ent["file_name"]):
                with open(ent["file_name"]) as f:
                    lines = f.read().replace("(", "").replace(")", "").split(
                        "\n")
                samples = []
                for l in lines:
                    samples += [a.strip() for a in l.split("|") if a.strip()]
                entities.append({"name": ent["name"], "samples": samples})
        return entities

    def get_keywords_manifest(self):
        padatious = self.get_entities_manifest()
        adapt = self.get_vocab_manifest()
        regex = self.get_regex_manifest()
        return {"adapt": adapt,
                "padatious": padatious,
                "regex": regex}


def open_intent_envelope(message):
    """
    Convert dictionary received over messagebus to Intent.
    """
    # TODO can this method be fully removed from ovos_utils ?
    from adapt.intent import Intent

    intent_dict = message.data
    return Intent(intent_dict.get('name'),
                  intent_dict.get('requires'),
                  intent_dict.get('at_least_one'),
                  intent_dict.get('optional'))
