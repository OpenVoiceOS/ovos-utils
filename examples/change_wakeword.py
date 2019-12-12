from jarbas_utils.configuration import update_mycroft_config
from jarbas_utils.lang.phonemes import get_phonemes


def create_wakeword(word, sensitivity):
    # sensitivity is a bitch to do automatically
    # IDEA make some web ui or whatever to tweak it experimentally
    phonemes = get_phonemes(word)
    config = {
        "listener": {
            "wake_word": word
        },
        word: {
            "andromeda": {
                "module": "pocketsphinx",
                "phonemes": phonemes,
                "sample_rate": 16000,
                "threshold": sensitivity,
                "lang": "en-us"
            }
        }
    }
    update_mycroft_config(config)


create_wakeword("andromeda", "1e-25")