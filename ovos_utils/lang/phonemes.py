from phoneme_guesser import guess_phonemes as _guess_phonemes, \
    get_phonemes as _get_phonemes


def guess_phonemes(word, lang="en-us"):
    return _guess_phonemes(word, lang)


def get_phonemes(name, lang="en-us"):
    return _get_phonemes(name, lang)

########################################################################
# ARPABET was invented for English.
# The standard dictionary written in ARPABET is the CMU dictionary.

arpabet2ipa = {
    'AA': 'ɑ',
    'AE': 'æ',
    'AH': 'ʌ',
    'AH0': 'ə',
    'AO': 'ɔ',
    'AW': 'aʊ',
    'AY': 'aɪ',
    'EH': 'ɛ',
    'ER': 'ɝ',
    'ER0': 'ɚ',
    'EY': 'eɪ',
    'IH': 'ɪ',
    'IH0': 'ɨ',
    'IY': 'i',
    'OW': 'oʊ',
    'OY': 'ɔɪ',
    'UH': 'ʊ',
    'UW': 'u',
    'B': 'b',
    'CH': 'tʃ',
    'D': 'd',
    'DH': 'ð',
    'EL': 'l̩ ',
    'EM': 'm̩',
    'EN': 'n̩',
    'F': 'f',
    'G': 'ɡ',
    'HH': 'h',
    'JH': 'dʒ',
    'K': 'k',
    'L': 'l',
    'M': 'm',
    'N': 'n',
    'NG': 'ŋ',
    'P': 'p',
    'Q': 'ʔ',
    'R': 'ɹ',
    'S': 's',
    'SH': 'ʃ',
    'T': 't',
    'TH': 'θ',
    'V': 'v',
    'W': 'w',
    'WH': 'ʍ',
    'Y': 'j',
    'Z': 'z',
    'ZH': 'ʒ'
}

ipa2arpabet = {v: k for k, v in arpabet2ipa.items()}
