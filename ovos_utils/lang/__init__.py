from os.path import expanduser, isdir, dirname
from os import system, makedirs


def get_tts(sentence, lang="en-us", mp3_file="/tmp/google_tx_tts.mp3"):
    # TODO privacy issues - https://github.com/OpenVoiceOS/ovos_utils/issues/2
    ext = "mp3"
    if not mp3_file.endswith(ext):
        mp3_file += "." + ext
    mp3_file = expanduser(mp3_file)
    if not isdir(dirname(mp3_file)):
        makedirs(dirname(mp3_file))
    get_sentence = 'wget -q -U Mozilla -O' + mp3_file + \
                   ' "https://translate.google.com/translate_tts?tl=' + \
                   lang + '&q=' + sentence + '&client=tw-ob' + '"'
    system(get_sentence)
    return mp3_file
