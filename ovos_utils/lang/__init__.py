from os.path import expanduser, isdir, dirname, join
from os import system, makedirs, listdir
from ovos_utils.lang.detect import detect_lang
from ovos_utils.lang.translate import translate_text
from ovos_utils.file_utils import resolve_resource_file


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


def get_language_dir(base_path, lang="en-us"):
    """ checks for all language variations and returns best path """
    lang_path = join(base_path, lang)
    # base_path/en-us
    if isdir(lang_path):
        return lang_path
    if "-" in lang:
        main = lang.split("-")[0]
        # base_path/en
        general_lang_path = join(base_path, main)
        if isdir(general_lang_path):
            return general_lang_path
    else:
        main = lang
    # base_path/en-uk, base_path/en-au...
    if isdir(base_path):
        candidates = [join(base_path, f)
                      for f in listdir(base_path) if f.startswith(main)]
        paths = [p for p in candidates if isdir(p)]
        # TODO how to choose best local dialect?
        if len(paths):
            return paths[0]
    return join(base_path, lang)


def translate_word(name, lang='en-us'):
    """ Helper to get word translations
    Args:
        name (str): Word name. Returned as the default value if not translated
        lang (str, optional): an optional BCP-47 language code, if omitted
                              the default language will be used.
    Returns:
        str: translated version of resource name
    """
    filename = resolve_resource_file(join("text", lang, name + ".word"))
    if filename:
        # open the file
        try:
            with open(filename, 'r', encoding='utf8') as f:
                for line in f:
                    word = line.strip()
                    if word.startswith("#"):
                        continue  # skip comment lines
                    return word
        except Exception:
            pass
    return name  # use resource name as the word

