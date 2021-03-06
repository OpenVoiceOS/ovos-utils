from ovos_utils.lang.detect import detect_lang
import requests


def translate_text(text, lang="en-us", source_lang=None,
             url="https://libretranslate.com/translate"):
    """host it yourself https://github.com/uav4geo/LibreTranslate"""
    lang = lang.split("-")[0]
    if source_lang:
        source_lang = source_lang.split("-")[0]
    else:
        source_lang = detect_lang(text)
    r = requests.post(url, params={"q": text,
                                   "source": source_lang,
                                   "target": lang}).json()
    if r.get("error"):
        return None
    return r["translatedText"]
