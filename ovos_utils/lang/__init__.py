from os import listdir
from os.path import isdir, join
from typing import Optional

from langcodes import tag_distance, standardize_tag as std

from ovos_utils.file_utils import resolve_resource_file


def standardize_lang_tag(lang_code: str, macro=True) -> str:
    """https://langcodes-hickford.readthedocs.io/en/sphinx/index.html"""
    try:
        return str(std(lang_code, macro=macro))
    except:
        if macro:
            return lang_code.split("-")[0].lower()
        if "-" in lang_code:
            a, b = lang_code.split("-", 2)
            return f"{a.lower()}-{b.upper()}"
        return lang_code.lower()


def get_language_dir(base_path: str, lang: str ="en-US") -> Optional[str]:
    """ checks for all language variations and returns best path """
    lang = standardize_lang_tag(lang)

    candidates = []
    for f in listdir(base_path):
        if isdir(f"{base_path}/{f}"):
            try:
                score = tag_distance(lang, f)
            except:  # not a valid language code
                continue
                # https://langcodes-hickford.readthedocs.io/en/sphinx/index.html#distance-values
                # 0 -> These codes represent the same language, possibly after filling in values and normalizing.
                # 1- 3 -> These codes indicate a minor regional difference.
                # 4 - 10 -> These codes indicate a significant but unproblematic regional difference.
            if score < 10:
                candidates.append((f"{base_path}/{f}", score))
    if not candidates:
        return None
    # sort by distance to target lang code
    candidates = sorted(candidates, key=lambda k: k[1])
    return candidates[0][0]


def translate_word(name, lang='en-US'):
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
