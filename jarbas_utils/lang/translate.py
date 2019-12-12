from googletrans import Translator
from jarbas_utils.sound import play_mp3, play_wav
from jarbas_utils.lang.detect import detect_lang
from os.path import expanduser, isdir, dirname
from os import system, makedirs
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


def say_in_language(sentence, lang="en-us", wav_file="/tmp/chatterbox/translated"):
    if detect_lang(sentence) != lang.split("-")[0]:
        sentence = translate_text(sentence, lang)
    ext = "mp3"
    if not wav_file.endswith(ext):
        wav_file += "." + ext
    wav_file = expanduser(wav_file)
    if not isdir(dirname(wav_file)):
        makedirs(dirname(wav_file))
    get_sentence = 'wget -q -U Mozilla -O' + wav_file + \
                   ' "https://translate.google.com/translate_tts?tl=' + \
                   lang + '&q=' + sentence + '&client=tw-ob' + '"'
    system(get_sentence)
    if ext == "mp3":
        play_mp3(wav_file)
    elif ext == "wav":
        play_wav(wav_file)
    return sentence
