import requests


def detect_lang(text, return_dict=False, key=None,
                url="https://libretranslate.com/detect"):
    """host it yourself https://github.com/uav4geo/LibreTranslate"""
    params = {"q": text}
    if key:
        params["api_key"] = key
    res = requests.post(url, params=params).json()
    if return_dict:
        return res[0]
    return res[0]["language"]


if __name__ == "__main__":
    assert detect_lang("olá eu chamo-me joaquim") == "pt"

    assert detect_lang("olá eu chamo-me joaquim", return_dict=True) == \
           {'confidence': 0.9999939001351439, 'language': 'pt'}

    assert detect_lang("hello world") == "en"

    fr_en = """\
    France is the largest country in Western Europe and the third-largest in Europe as a whole.
    A accès aux chiens et aux frontaux qui lui ont été il peut consulter et modifier ses collections
    et exporter Cet article concerne le pays européen aujourd’hui appelé République française.
    Pour d’autres usages du nom France, Pour une aide rapide et effective, veuiller trouver votre aide
    dans le menu ci-dessus.
    Motoring events began soon after the construction of the first successful gasoline-fueled automobiles.
    The quick brown fox jumped over the lazy dog."""

    assert detect_lang(fr_en) == "fr"

    assert detect_lang("This piece of text is in English. Този текст е на Български.",
                              return_dict=True) == {'confidence': 0.28571342657428966, 'language': 'en'}
