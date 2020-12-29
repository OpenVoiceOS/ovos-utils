from phoneme_guesser import guess_phonemes as _guess_phonemes, \
    get_phonemes as _get_phonemes

# Backwards compat, TODO deprecate?


def guess_phonemes(word, lang="en-us"):
    return _guess_phonemes(word, lang)


def get_phonemes(name, lang="en-us"):
    return _get_phonemes(name, lang)

