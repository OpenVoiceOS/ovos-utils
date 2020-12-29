from ovos_utils.log import LOG

try:
    from google_trans_new import google_translator
except ImportError:
    google_translator = None

try:
    import pycld2 as cld2
except ImportError:
    cld2 = None

try:
    import cld3
except ImportError:
    cld3 = None


def code_to_name(lang_code):
    lang_code = lang_code.lower()
    for name, code in cld2.LANGUAGES:
        if code == lang_code:
            return name.lower().capitalize()
    lang_code = lang_code.split("-")[0]
    for name, code in cld2.LANGUAGES:
        if code == lang_code:
            return name.lower().capitalize()
    return "Unknown"


def detect_lang_naive(text, return_multiple=False, return_dict=False,
                      hint_language=None, filter_unreliable=False):
    """

    :param text:
    :param return_multiple bool if True return a list of all languages detected, else the top language
    :param return_dict: bool  if True returns all data, E.g.,  pt -> {'lang': 'Portuguese', 'lang_code': 'pt', 'conf': 0.96}
    :param hint_language: str  E.g., 'ITALIAN' or 'it' boosts Italian
    :return:
    """
    if cld2 is None:
        LOG.debug("run pip install pycld2")
        raise ImportError("pycld2 not installed")
    isReliable, textBytesFound, details = cld2.detect(text, hintLanguage=hint_language)
    languages = []

    # filter unreliable predictions
    if not isReliable and filter_unreliable:
        return None

    # select first language only
    if not return_multiple:
        details = [details[0]]

    for name, code, score, _ in details:
        if code == "un":
            continue
        if return_dict:
            languages.append({"lang": name.lower().capitalize(), "lang_code": code, "conf": score / 100})
        else:
            languages.append(code)

    # return top language only
    if not return_multiple:
        if not len(languages):
            return None
        return languages[0]
    return languages


def detect_lang_neural(text, return_multiple=False, return_dict=False,
                       hint_language=None, filter_unreliable=False):
    if cld3 is None:
        LOG.debug("run pip install pycld3")
        raise ImportError("pycld3 not installed")
    languages = []
    if return_multiple or hint_language:
        preds = sorted(cld3.get_frequent_languages(text, num_langs=5), key=lambda i: i.probability, reverse=True)
        for pred in preds:
            if filter_unreliable and not pred.is_reliable:
                continue
            if return_dict:
                languages += [{"lang_code": pred.language,
                               "lang": code_to_name(pred.language),
                               "conf": pred.probability}]
            else:
                languages.append(pred.language)

            if hint_language and hint_language == pred.language:
                languages = [languages[-1]]
                break
    else:
        pred = cld3.get_language(text)
        if filter_unreliable and not pred.is_reliable:
            pass
        elif return_dict:
            languages = [{"lang_code": pred.language,
                          "lang": code_to_name(pred.language),
                          "conf": pred.probability}]
        else:
            languages = [pred.language]

    # return top language only
    if not return_multiple:
        if not len(languages):
            return None
        return languages[0]
    return languages


def detect_lang_google(text, return_dict=False):
    if google_translator is None:
        LOG.debug("run pip install google_trans_new")
        raise ImportError("google_trans_new not installed")
    translator = google_translator()
    tx = translator.detect(text)
    if return_dict:
        return {"lang_code": tx[0], "lang": tx[1]}
    return tx[0]


def detect_lang(text, return_dict=False):
    if cld2 is not None:
        return detect_lang_naive(text, return_dict=return_dict)
    return detect_lang_google(text, return_dict=return_dict)


if __name__ == "__main__":
    assert detect_lang_google("olá eu chamo-me joaquim") == "pt"
    assert detect_lang_naive("olá eu chamo-me joaquim", return_dict=True) == \
           {'lang': 'Portuguese', 'lang_code': 'pt', 'conf': 0.96}

    assert detect_lang_naive("hello world") == "en"

    fr_en = """\
    France is the largest country in Western Europe and the third-largest in Europe as a whole.
    A accès aux chiens et aux frontaux qui lui ont été il peut consulter et modifier ses collections
    et exporter Cet article concerne le pays européen aujourd’hui appelé République française.
    Pour d’autres usages du nom France, Pour une aide rapide et effective, veuiller trouver votre aide
    dans le menu ci-dessus.
    Motoring events began soon after the construction of the first successful gasoline-fueled automobiles.
    The quick brown fox jumped over the lazy dog."""

    assert detect_lang_naive(fr_en) == "fr"
    assert detect_lang_naive(fr_en, return_multiple=True) == ['fr', 'en']

    assert detect_lang_naive(fr_en, hint_language="en", return_dict=True) == \
           {'lang': 'English', 'lang_code': 'en', 'conf': 0.6}  # boost english score

    assert detect_lang_naive(fr_en, return_dict=True, return_multiple=True)[1][
               "conf"] == 0.41  # compare conf with non boosted result

    assert detect_lang_naive(fr_en, return_dict=True) == \
           {'lang': 'French', 'lang_code': 'fr', 'conf': 0.58}
    assert detect_lang_neural(fr_en, return_dict=True) == \
           {'lang_code': 'fr', 'lang': 'French', 'conf': 0.9675191640853882}

    assert detect_lang_neural("This piece of text is in English. Този текст е на Български.",
                              return_dict=True,
                              return_multiple=True) == [
        {'lang_code': 'en', 'lang': 'English', 'conf': 0.9999790191650391},
        {'lang_code': 'bg', 'lang': 'Bulgarian', 'conf': 0.9173873066902161}
        ]

    assert detect_lang_neural("This piece of text is in English. Този текст е на Български.") == "en"
    assert detect_lang_neural("This piece of text is in English. Този текст е на Български.", return_dict=True, hint_language="bg") == \
           {'lang_code': 'bg', 'lang': 'Bulgarian', 'conf': 0.9173873066902161} # Boost bulgarian