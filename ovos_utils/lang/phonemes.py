from phoneme_guesser import guess_phonemes as _guess_phonemes, \
    get_phonemes as _get_phonemes

# Backwards compat, TODO deprecate?


def guess_phonemes(word, lang="en-us"):
    return _guess_phonemes(word, lang)


def get_phonemes(name, lang="en-us"):
    return _get_phonemes(name, lang)


if __name__ == "__main__":

    words = ["hey mycroft", "hey chatterbox", "alexa", "siri", "cortana"]
    for w in words:
        print(w, get_phonemes(w))

    """
    hey mycroft HH EY1 . M Y K R OW F T
    hey chatterbox HH EY1 . CH AE T EH R B OW K S
    alexa AH0 L EH1 K S AH0
    siri S IH1 R IY0
    cortana K OW R T AE N AE
    """