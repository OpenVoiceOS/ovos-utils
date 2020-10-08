from googletrans import Translator
from ovos_utils.sound import play_mp3
from ovos_utils.lang.detect import detect_lang
from ovos_utils.lang import get_tts
import logging

logging.getLogger("hyper").setLevel("ERROR")
logging.getLogger("hpack").setLevel("ERROR")
logging.getLogger("chardet").setLevel("ERROR")


def translate_text(text, lang="en-us", source_lang=None):
    translator = Translator()
    lang = lang.split("-")[0]
    if source_lang:
        source_lang = source_lang.split("-")[0]
        tx = translator.translate(text, src=source_lang, dest=lang)
    else:
        tx = translator.translate(text,  dest=lang)
    return tx.text


def translate_to_mp3(sentence, lang="en-us", mp3_file="/tmp/mycroft/tts.mp3"):
    if detect_lang(sentence) != lang.split("-")[0]:
        sentence = translate_text(sentence, lang)
    return get_tts(sentence, lang, mp3_file)


def say_in_language(sentence, lang="en-us", mp3_file="/tmp/mycroft/tts.mp3"):
    mp3_file = translate_to_mp3(sentence, lang, mp3_file)
    play_mp3(mp3_file)
    return sentence
