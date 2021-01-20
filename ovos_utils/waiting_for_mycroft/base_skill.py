import re
from os.path import join, exists
import os
import time
from itertools import chain
from copy import deepcopy
from ovos_utils.lang import get_language_dir
from ovos_utils.intents import ConverseTracker
from ovos_utils.waiting_for_mycroft.skill_gui import SkillGUI
from ovos_utils.waiting_for_mycroft.skill_api import SkillApi
from ovos_utils.log import LOG
from ovos_utils import camel_case_split, get_handler_name, \
    create_killable_daemon, ensure_mycroft_import
from ovos_utils.messagebus import Message
import threading
from inspect import signature
from functools import wraps

# ensure mycroft can be imported
ensure_mycroft_import()

from mycroft.skills.mycroft_skill import MycroftSkill as _MycroftSkill
from mycroft.skills.fallback_skill import FallbackSkill as _FallbackSkill
from mycroft.skills.skill_data import read_vocab_file, load_vocabulary, load_regex
from mycroft.dialog import load_dialogs
from mycroft import dialog
from mycroft.util import resolve_resource_file
from mycroft.skills.mycroft_skill.event_container import create_wrapper
from mycroft.skills.settings import get_local_settings, save_settings


def get_non_properties(obj):
    """Get attibutes that are not properties from object.

    Will return members of object class along with bases down to MycroftSkill.

    Arguments:
        obj:    object to scan

    Returns:
        Set of attributes that are not a property.
    """

    def check_class(cls):
        """Find all non-properties in a class."""
        # Current class
        d = cls.__dict__
        np = [k for k in d if not isinstance(d[k], property)]
        # Recurse through base classes excluding MycroftSkill and object
        for b in [b for b in cls.__bases__ if b not in (object, MycroftSkill)]:
            np += check_class(b)
        return np

    return set(check_class(obj.__class__))


class AbortEvent(StopIteration):
    """ abort bus event handler """


class AbortIntent(AbortEvent):
    """ abort intent parsing """


class AbortQuestion(AbortEvent):
    """ gracefully abort get_response queries """


def killable_intent(msg="mycroft.skills.abort_execution",
                    callback=None, react_to_stop=True, call_stop=True):
    return killable_event(msg, AbortIntent, callback, react_to_stop, call_stop)


def killable_event(msg="mycroft.skills.abort_execution", exc=AbortEvent,
                   callback=None, react_to_stop=False, call_stop=False):

    # Begin wrapper
    def create_killable(func):

        @wraps(func)
        def call_function(*args, **kwargs):
            skill = args[0]
            t = create_killable_daemon(func, args, kwargs, autostart=False)

            def abort(_):
                if call_stop:
                    # call stop on parent skill
                    skill.stop()

                # ensure no orphan get_response daemons
                # this is the only killable daemon that core itself will
                # create, users should also account for this condition with
                # callbacks if using the decorator for other purposes
                skill._response = None
                try:
                    while t.is_alive():
                        t.raise_exc(exc)
                        time.sleep(0.1)
                except threading.ThreadError:
                    pass  # already killed
                except AssertionError:
                    pass  # could not determine thread id ?
                if callback is not None:
                    if len(signature(callback).parameters) == 1:
                        # class method, needs self
                        callback(args[0])
                    else:
                        callback()
            # save reference to threads so they can be killed later
            skill._threads.append(t)
            skill.bus.once(msg, abort)
            if react_to_stop:
                skill.bus.once(args[0].skill_id + ".stop", abort)
            t.start()
            return t

        return call_function

    return create_killable


class MycroftSkill(_MycroftSkill):
    monkey_patched = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.public_api = {}  # pull/1822
        self.gui = SkillGUI(self)  # pull/2683
        self._threads = []

    # TODO PR for core - stops skill executing gracefully
    # this method can probably use a better refactor, we are only changing one
    # of the internal callbacks
    def add_event(self, name, handler, handler_info=None, once=False):
        """Create event handler for executing intent or other event.

        Arguments:
            name (string): IntentParser name
            handler (func): Method to call
            handler_info (string): Base message when reporting skill event
                                   handler status on messagebus.
            once (bool, optional): Event handler will be removed after it has
                                   been run once.
        """
        skill_data = {'name': get_handler_name(handler)}

        def on_error(e):
            """Speak and log the error."""
            if not isinstance(e, AbortEvent):
                # Convert "MyFancySkill" to "My Fancy Skill" for speaking
                handler_name = camel_case_split(self.name)
                msg_data = {'skill': handler_name}
                msg = dialog.get('skill.error', self.lang, msg_data)
                self.speak(msg)
                LOG.exception(msg)
            else:
                LOG.info("Skill execution aborted")
            # append exception information in message
            skill_data['exception'] = repr(e)

        def on_start(message):
            """Indicate that the skill handler is starting."""
            if handler_info:
                # Indicate that the skill handler is starting if requested
                msg_type = handler_info + '.start'
                self.bus.emit(message.forward(msg_type, skill_data))

        def on_end(message):
            """Store settings and indicate that the skill handler has completed
            """
            if self.settings != self._initial_settings:
                save_settings(self.settings_write_path, self.settings)
                self._initial_settings = deepcopy(self.settings)
            if handler_info:
                msg_type = handler_info + '.complete'
                self.bus.emit(message.forward(msg_type, skill_data))

        wrapper = create_wrapper(handler, self.skill_id,
                                 on_start, on_end, on_error)
        return self.events.add(name, wrapper, once)

    def __handle_stop(self, _):
        self.bus.emit(Message(self.skill_id + ".stop"))
        super().__handle_stop()

    # TODO PR for core - abort get_response gracefully
    def _wait_response(self, is_cancel, validator, on_fail, num_retries):
        """Loop until a valid response is received from the user or the retry
        limit is reached.

        Arguments:
            is_cancel (callable): function checking cancel criteria
            validator (callbale): function checking for a valid response
            on_fail (callable): function handling retries

        """
        self._response = False
        default_converse = self.converse  # backup original method
        self._real_wait_response(is_cancel, validator, on_fail, num_retries)
        while self._response is False:
            time.sleep(0.1)
        self.converse = default_converse  # restore original method
        return self._response

    def __get_response(self):
        """Helper to get a reponse from the user

        Returns:
            str: user's response or None on a timeout
        """
        def converse(utterances, lang=None):
            converse.response = utterances[0] if utterances else None
            converse.finished = True
            return True

        # install a temporary conversation handler
        self.make_active()
        converse.finished = False
        converse.response = None
        self.converse = converse  # restored after returning from method

        # 10 for listener, 5 for SST, then timeout
        # NOTE a threading event is not used otherwise we can't raise the
        # AbortEvent exception to kill the thread
        start = time.time()
        while time.time() - start <= 15 and not converse.finished:
            time.sleep(0.1)
            if self._response is not False:
                if self._response is None:
                    # aborted externally (if None)
                    self.log.debug("get_response aborted")
                converse.finished = True
                converse.response = self._response  # external override
        return converse.response

    def _handle_killed_wait_response(self):
        self._response = None

    @killable_event("mycroft.skills.abort_question", exc=AbortQuestion,
                    callback=_handle_killed_wait_response, react_to_stop=True)
    def _real_wait_response(self, is_cancel, validator, on_fail, num_retries):
        """Loop until a valid response is received from the user or the retry
        limit is reached.

        Arguments:
            is_cancel (callable): function checking cancel criteria
            validator (callbale): function checking for a valid response
            on_fail (callable): function handling retries

        """
        num_fails = 0
        while True:
            if self._response is not False:
                # usually None when aborted externally
                # also allows overriding returned result from other events
                return self._response

            response = self.__get_response()

            if response is None:
                # if nothing said, prompt one more time
                num_none_fails = 1 if num_retries < 0 else num_retries
                if num_fails >= num_none_fails:
                    self._response = None
                    return
            else:
                if validator(response):
                    self._response = response
                    return

                # catch user saying 'cancel'
                if is_cancel(response):
                    self._response = None
                    return

            num_fails += 1
            if 0 < num_retries < num_fails:
                self._response = None
                return

            line = on_fail(response)
            if line:
                self.speak(line, expect_response=True)
            else:
                self.bus.emit(Message('mycroft.mic.listen'))

    # https://github.com/MycroftAI/mycroft-core/pull/1335
    def init_dialog(self, root_directory):
        # If "<skill>/dialog/<lang>" exists, load from there.  Otherwise
        # load dialog from "<skill>/locale/<lang>"
        dialog_dir = get_language_dir(join(root_directory, 'dialog'),
                                      self.lang)
        locale_dir = get_language_dir(join(root_directory, 'locale'),
                                      self.lang)
        if exists(dialog_dir):
            self.dialog_renderer = load_dialogs(dialog_dir)
        elif exists(locale_dir):
            self.dialog_renderer = load_dialogs(locale_dir)
        else:
            LOG.debug('No dialog loaded')

    def load_vocab_files(self, root_directory):
        """ Load vocab files found under root_directory.

        Arguments:
            root_directory (str): root folder to use when loading files
        """
        keywords = []
        vocab_dir = get_language_dir(join(root_directory, 'vocab'),
                                     self.lang)
        locale_dir = get_language_dir(join(root_directory, 'locale'),
                                      self.lang)
        if exists(vocab_dir):
            keywords = load_vocabulary(vocab_dir, self.skill_id)
        elif exists(locale_dir):
            keywords = load_vocabulary(locale_dir, self.skill_id)
        else:
            LOG.debug('No vocab loaded')

        # For each found intent register the default along with any aliases
        for vocab_type in keywords:
            for line in keywords[vocab_type]:
                entity = line[0]
                aliases = line[1:]
                self.intent_service.register_adapt_keyword(vocab_type,
                                                           entity,
                                                           aliases)

    def load_regex_files(self, root_directory):
        """ Load regex files found under the skill directory.

        Arguments:
            root_directory (str): root folder to use when loading files
        """
        regexes = []
        regex_dir = get_language_dir(join(root_directory, 'regex'),
                                     self.lang)
        locale_dir = get_language_dir(join(root_directory, 'locale'),
                                      self.lang)
        if exists(regex_dir):
            regexes = load_regex(regex_dir, self.skill_id)
        elif exists(locale_dir):
            regexes = load_regex(locale_dir, self.skill_id)

        for regex in regexes:
            self.intent_service.register_adapt_regex(regex)

    def _find_resource(self, res_name, lang, res_dirname=None):
        """Finds a resource by name, lang and dir
        """
        if res_dirname:
            # Try the old directory (dialog/vocab/regex)
            root_path = get_language_dir(join(self.root_dir, res_dirname),
                                         lang)
            path = join(root_path, res_name)
            if exists(path):
                return path

            # Try old-style non-translated resource
            path = join(self.root_dir, res_dirname, res_name)
            if exists(path):
                return path

        # New scheme:  search for res_name under the 'locale' folder
        root_path = get_language_dir(join(self.root_dir, 'locale'), lang)
        for path, _, files in os.walk(root_path):
            if res_name in files:
                return join(path, res_name)

        # Not found
        return None

    # https://github.com/MycroftAI/mycroft-core/pull/1468
    def _deactivate_skill(self, message):
        skill_id = message.data.get("skill_id")
        if skill_id == self.skill_id:
            self.handle_skill_deactivated(message)

    def handle_skill_deactivated(self, message=None):
        """
        Invoked when the skill is removed from active skill list
        """
        pass

    # https://github.com/MycroftAI/mycroft-core/pull/1822
    # https://github.com/MycroftAI/mycroft-core/pull/1468
    def bind(self, bus):
        if bus and not isinstance(self.gui, SkillGUI):
            # needs to be available before call to self.bind, if a skill is
            # initialized with the bus argument it will miss the monkey-patch
            # AFAIK this never happens in mycroft-core but i want the patch
            # to work in non standard use cases
            self.gui = SkillGUI(self)  # pull/2683
        super().bind(bus)
        if bus:
            SkillApi.connect_bus(self.bus)  # pull/1822
            self._register_public_api()
            ConverseTracker.connect_bus(self.bus)  # pull/1468
            self.add_event("converse.skill.deactivated",
                           self._deactivate_skill)

    def _send_public_api(self, message):
        """Respond with the skill's public api."""
        self.bus.emit(message.response(data=self.public_api))

    def _register_public_api(self):
        """ Find and register api methods.
        Api methods has been tagged with the api_method member, for each
        method where this is found the method a message bus handler is
        registered.
        Finally create a handler for fetching the api info from any requesting
        skill.
        """

        def wrap_method(func):
            """Boiler plate for returning the response to the sender."""

            def wrapper(message):
                result = func(*message.data['args'], **message.data['kwargs'])
                self.bus.emit(message.response(data={'result': result}))

            return wrapper

        methods = [attr_name for attr_name in get_non_properties(self)
                   if hasattr(getattr(self, attr_name), '__name__')]

        for attr_name in methods:
            method = getattr(self, attr_name)

            if hasattr(method, 'api_method'):
                doc = method.__doc__ or ''
                name = method.__name__
                self.public_api[name] = {
                    'help': doc,
                    'type': '{}.{}'.format(self.skill_id, name),
                    'func': method
                }
        for key in self.public_api:
            if ('type' in self.public_api[key] and
                    'func' in self.public_api[key]):
                LOG.debug('Adding api method: '
                          '{}'.format(self.public_api[key]['type']))

                # remove the function member since it shouldn't be
                # reused and can't be sent over the messagebus
                func = self.public_api[key].pop('func')
                self.add_event(self.public_api[key]['type'],
                               wrap_method(func))

        if self.public_api:
            self.add_event('{}.public_api'.format(self.skill_id),
                           self._send_public_api)

    # https://github.com/MycroftAI/mycroft-core/pull/2675
    def voc_match(self, utt, voc_filename, lang=None, exact=False):
        """Determine if the given utterance contains the vocabulary provided.
        Checks for vocabulary match in the utterance instead of the other
        way around to allow the user to say things like "yes, please" and
        still match against "Yes.voc" containing only "yes". The method first
        checks in the current skill's .voc files and secondly the "res/text"
        folder of mycroft-core. The result is cached to avoid hitting the
        disk each time the method is called.
        Arguments:
            utt (str): Utterance to be tested
            voc_filename (str): Name of vocabulary file (e.g. 'yes' for
                                'res/text/en-us/yes.voc')
            lang (str): Language code, defaults to self.long
            exact (bool): comparison using "==" instead of "in"
        Returns:
            bool: True if the utterance has the given vocabulary it
        """
        lang = lang or self.lang
        cache_key = lang + voc_filename
        if cache_key not in self.voc_match_cache:
            # Check for both skill resources and mycroft-core resources
            voc = self.find_resource(voc_filename + '.voc', 'vocab')
            if not voc:  # Check for vocab in mycroft core resources
                voc = resolve_resource_file(join('text', lang,
                                                 voc_filename + '.voc'))

            if not voc or not exists(voc):
                raise FileNotFoundError(
                    'Could not find {}.voc file'.format(voc_filename))
            # load vocab and flatten into a simple list
            vocab = read_vocab_file(voc)
            self.voc_match_cache[cache_key] = list(chain(*vocab))
        if utt:
            if exact:
                # Check for exact match
                return any(i.strip() == utt
                           for i in self.voc_match_cache[cache_key])
            else:
                # Check for matches against complete words
                return any([re.match(r'.*\b' + i + r'\b.*', utt)
                            for i in self.voc_match_cache[cache_key]])
        else:
            return False

    # TODO PR not yet made
    def remove_voc(self, utt, voc_filename, lang=None):
        """ removes any entry in .voc file from the utterance """
        lang = lang or self.lang
        cache_key = lang + voc_filename

        if cache_key not in self.voc_match_cache:
            self.voc_match(utt, voc_filename, lang)

        if utt:
            # Check for matches against complete words
            for i in self.voc_match_cache[cache_key]:
                # Substitute only whole words matching the token
                utt = re.sub(r'\b' + i + r"\b", "", utt)

        return utt


class FallbackSkill(MycroftSkill, _FallbackSkill):
    """ """
