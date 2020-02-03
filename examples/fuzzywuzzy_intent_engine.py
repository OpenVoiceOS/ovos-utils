from jarbas_utils.intents import BaseIntentEngine
from jarbas_utils.skills.intent_provider import IntentEngineSkill

from mycroft.configuration.config import Configuration
from mycroft.skills.core import MycroftSkill, Message

from fuzzywuzzy import process


class FuzzyEngine(BaseIntentEngine):
    def __init__(self):
        self.name = "fuzzy"
        BaseIntentEngine.__init__(self, self.name)
        self.config = Configuration.get().get(self.name, {})

    def calc_intent(self, query):
        """ return best intent for this query  """
        data = {"conf": 0,
                "utterance": query,
                "name": None}

        best_match = None
        best_score = 0
        for intent in self.intent_samples:
            samples = self.intent_samples[intent]
            match, score = process.extractOne(query, samples)
            if score > best_score:
                best_score = score
                best_match = (intent, match)

        if best_match is not None:
            intent, match = best_match
            data["name"] = intent
            data["match"] = match
            data["conf"] = best_score

        entities = []
        for entity in self.entity_samples:
            samples = self.entity_samples
            for s in samples:
                if s in query:
                    entities.append((entity, s))

        data["entities"] = [{entity: s} for entity, s in entities]
        return data


# engine skill for mycroft
class FuzzyEngineSkill(IntentEngineSkill):
    def initialize(self):
        priority = 5
        engine = FuzzyEngine()
        self.bind_engine(engine, priority)


class FuzzySkill(MycroftSkill):
    def register_fuzzy_intent(self, name, samples, handler):
        message = "fuzzy:register_intent"
        name = str(self.skill_id) + ':' + name
        data = {"name": name, "samples": samples}

        self.bus.emit(Message(message, data))
        self.add_event(name, handler, 'mycroft.skill.handler')

    def register_fuzzy_entity(self, name, samples):
        message = "fuzzy:register_entity"
        name = str(self.skill_id) + ':' + name
        data = {"name": name, "samples": samples}
        self.bus.emit(Message(message, data))


def create_skill():
    return FuzzySkill()

# install this file as a regular skill (fuzzy_engine/__init__.py)

## to import and create fuzzy skills

#    from os.path import dirname
#    skills_dir = dirname(dirname(__file__))
#    import sys
#    sys.path.append(skills_dir)
#    from fuzzy_engine import PadaosSkill