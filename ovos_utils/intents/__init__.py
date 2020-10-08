from ovos_utils.log import LOG
from ovos_utils.messagebus import get_mycroft_bus, Message
import time
from os.path import isfile


class IntentApi:
    """
    Query Intent Service at runtime
    """

    def __init__(self, bus=None, timeout=5):
        self.bus = bus or get_mycroft_bus()
        self.timeout = timeout
        self.bus.on('intent.service.padatious.reply', self._receive_data)
        self.bus.on('intent.service.adapt.reply', self._receive_data)
        self.bus.on('intent.service.intent.reply', self._receive_data)
        self.bus.on('intent.service.skills.reply', self._receive_data)
        self.bus.on('intent.service.padatious.manifest', self._receive_data)
        self.bus.on('intent.service.adapt.manifest', self._receive_data)
        self.bus.on('intent.service.adapt.vocab.manifest', self._receive_data)
        self.bus.on('intent.service.padatious.entities.manifest',
                    self._receive_data)
        self._response = None
        self.waiting = False

    def _receive_data(self, message):
        self.waiting = False
        self._response = message.data

    def get_adapt_intent(self, utterance):
        """ get best adapt intent for utterance """
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.adapt.get",
                              {"utterance": utterance},
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        return self._response["intent"]

    def get_padatious_intent(self, utterance):
        """ get best padatious intent for utterance """
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.padatious.get",
                              {"utterance": utterance},
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        return self._response["intent"]

    def get_intent(self, utterance):
        """ get best intent for utterance """
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.intent.get",
                              {"utterance": utterance},
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        return self._response["intent"]

    def get_skills(self):
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.skills.get",
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        return self._response["skills"]

    def get_active_skills(self):
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.active_skills.get",
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        return self._response["skills"]

    def get_adapt_manifest(self):
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.adapt.manifest.get",
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        return self._response["intents"]

    def get_padatious_manifest(self):
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.padatious.manifest.get",
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        return self._response["intents"]

    def get_intent_manifest(self):
        padatious = self.get_padatious_manifest()
        adapt = self.get_adapt_manifest()
        return {"adapt": adapt,
                "padatious": padatious}

    def get_vocab_manifest(self):
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.adapt.vocab.manifest.get",
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        vocab = {}
        for voc in self._response["vocab"]:
            if voc.get("regex"):
                continue
            if voc["end"] not in vocab:
                vocab[voc["end"]] = {"samples": []}
            vocab[voc["end"]]["samples"].append(voc["start"])
        return [{"name": voc, "samples": vocab[voc]["samples"]}
                for voc in vocab]

    def get_regex_manifest(self):
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.adapt.vocab.manifest.get",
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None

        vocab = {}
        for voc in self._response["vocab"]:
            if not voc.get("regex"):
                continue
            name = voc["regex"].split("(?P<")[-1].split(">")[0]
            if name not in vocab:
                vocab[name] = {"samples": []}
            vocab[name]["samples"].append(voc["regex"])
        return [{"name": voc, "regexes": vocab[voc]["samples"]}
                for voc in vocab]

    def get_entities_manifest(self):
        start = time.time()
        self._response = None
        self.waiting = True
        self.bus.emit(Message("intent.service.padatious.entities.manifest.get",
                              context={"destination": "intent_service",
                                       "source": "intent_api"}))
        while self.waiting and time.time() - start <= self.timeout:
            time.sleep(0.3)
        if time.time() - start > self.timeout:
            LOG.error("Intent Service timed out!")
            return None
        entities = []
        # read files
        for ent in self._response["entities"]:
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

