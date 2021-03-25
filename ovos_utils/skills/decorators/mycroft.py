from ovos_utils import ensure_mycroft_import

ensure_mycroft_import()

from mycroft.skills.mycroft_skill.decorators import intent_handler, \
    intent_file_handler, resting_screen_handler, skill_api_method
