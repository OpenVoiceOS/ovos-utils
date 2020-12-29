from ovos_utils.sound import play_mp3
from ovos_utils.lang.detect import detect_lang
from ovos_utils.lang import get_tts
from ovos_utils.log import LOG

import requests

try:
    from google_trans_new import google_translator
except ImportError:
    google_translator = None

import logging

logging.getLogger("hpack").setLevel("ERROR")
logging.getLogger("chardet").setLevel("ERROR")


def translate_text(text, lang="en-us", source_lang=None):
    tx = translate_apertium(text, lang, source_lang)
    if not tx:
        LOG.warning("Falling back to google translate")
        return translate_google(text, lang, source_lang)
    return tx


def translate_to_mp3(sentence, lang="en-us", mp3_file=None):
    if detect_lang(sentence) != lang.split("-")[0]:
        sentence = translate_text(sentence, lang)
    return get_tts(sentence, lang, mp3_file)


def say_in_language(sentence, lang="en-us", mp3_file=None):
    mp3_file = translate_to_mp3(sentence, lang, mp3_file)
    play_mp3(mp3_file)
    return sentence


def translate_apertium(text, lang="en-us", source_lang=None):
    lang_pair = lang
    if source_lang:
        lang_pair = source_lang + "|" + lang
    r = requests.get("https://www.apertium.org/apy/translate",
                     params={"q": text, "langpair": lang_pair}).json()
    if r.get("status", "") == "error":
        LOG.error(r["explanation"])
        return None
    return r["responseData"]["translatedText"]


def translate_google(text, lang="en-us", source_lang=None):
    if google_translator is None:
        LOG.debug("run pip install google_trans_new")
        raise ImportError("google_trans_new not installed")
    translator = google_translator()
    lang = lang.split("-")[0]
    if source_lang:
        source_lang = source_lang.split("-")[0]
        tx = translator.translate(text, lang_src=source_lang, lang_tgt=lang)
    else:
        tx = translator.translate(text,  lang_tgt=lang)
    return tx.strip()

