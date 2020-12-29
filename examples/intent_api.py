from ovos_utils.intents import IntentQueryApi
from pprint import pprint


intents = IntentQueryApi()

pprint(intents.get_skill("who are you"))
pprint(intents.get_skill("set volume to 100%"))

exit()
# loaded skills
pprint(intents.get_skills_manifest())
pprint(intents.get_active_skills())

# intent parsing
pprint(intents.get_adapt_intent("who are you"))
pprint(intents.get_padatious_intent("who are you"))
pprint(intents.get_intent("who are you"))  # intent that will trigger

# skill from utterance
pprint(intents.get_skill("who are you"))

# registered intents
pprint(intents.get_adapt_manifest())
pprint(intents.get_padatious_manifest())
pprint(intents.get_intent_manifest())  # all of the above

# registered vocab
pprint(intents.get_entities_manifest())  # padatious entities / .entity files
pprint(intents.get_vocab_manifest())  # adapt vocab / .voc files
pprint(intents.get_regex_manifest())  # adapt regex / .rx files
pprint(intents.get_keywords_manifest())  # all of the above
