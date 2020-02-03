from jarbas_utils.intents import BaseIntentEngine
from jarbas_utils.skills.intent_provider import IntentEngineSkill

from mycroft.configuration.config import Configuration
from mycroft.skills.core import MycroftSkill, Message

from padaos import IntentContainer


class PadaosEngine(BaseIntentEngine):
    def __init__(self):
        self.name = "padaos"
        BaseIntentEngine.__init__(self, self.name)
        self.config = Configuration.get().get(self.name, {})
        self.container = IntentContainer()

    def add_intent(self, name, samples):
        self.container.add_intent(name, samples)

    def remove_intent(self, name):
        self.container.remove_intent(name)

    def add_entity(self, name, samples):
        self.container.add_entity(name, samples)

    def remove_entity(self, name):
        self.container.remove_entity(name)

    def train(self, single_thread=False):
        """ train all registered intents and entities"""
        # Padaos is simply regex, it handles this when registering
        pass

    def calc_intent(self, query):
        """ return best intent for this query  """
        data = {"conf": 0,
                "utterance": query,
                "name": None}
        data.update(self.container.calc_intent(query))
        return data


# engine skill for mycroft
class PadaosEngineSkill(IntentEngineSkill):
    def initialize(self):
        priority = 4
        engine = PadaosEngine()
        self.bind_engine(engine, priority)


class PadaosSkill(MycroftSkill):
    def register_padaos_intent(self, name, samples, handler):
        message = "padaos:register_intent"
        name = str(self.skill_id) + ':' + name
        data = {"name": name, "samples": samples}

        self.bus.emit(Message(message, data))
        self.add_event(name, handler, 'mycroft.skill.handler')

    def register_padaos_entity(self, name, samples):
        message = "padaos:register_entity"
        name = str(self.skill_id) + ':' + name
        data = {"name": name, "samples": samples}
        self.bus.emit(Message(message, data))


def create_skill():
    return PadaosSkill()


# install this file as a regular skill (padaos_engine/__init__.py)

## to import and create padaos skills

#    from os.path import dirname
#    skills_dir = dirname(dirname(__file__))
#    import sys
#    sys.path.append(skills_dir)
#    from padaos_engine import PadaosSkill