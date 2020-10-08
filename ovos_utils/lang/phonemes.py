import pronouncing


def guess_phonemes(word):
    word = word.lower()
    basic_pronunciations = {'a': ['AE'], 'b': ['B'], 'c': ['K'],
                           'd': ['D'],
                           'e': ['EH'], 'f': ['F'], 'g': ['G'],
                           'h': ['HH'],
                           'i': ['IH'],
                           'j': ['JH'], 'k': ['K'], 'l': ['L'],
                           'm': ['M'],
                           'n': ['N'], 'o': ['OW'], 'p': ['P'],
                           'qu': ['K', 'W'], 'r': ['R'],
                           's': ['S'], 't': ['T'], 'u': ['AH'],
                           'v': ['V'],
                           'w': ['W'], 'x': ['K', 'S'], 'y': ['Y'],
                           'z': ['Z'], 'ch': ['CH'],
                           'sh': ['SH'], 'th': ['TH'], 'dg': ['JH'],
                           'dge': ['JH'], 'psy': ['S', 'AY'],
                           'oi': ['OY'],
                           'ee': ['IY'],
                           'ao': ['AW'], 'ck': ['K'], 'tt': ['T'],
                           'nn': ['N'], 'ai': ['EY'], 'eu': ['Y', 'UW'],
                           'ue': ['UW'],
                           'ie': ['IY'], 'ei': ['IY'], 'ea': ['IY'],
                           'ght': ['T'], 'ph': ['F'], 'gn': ['N'],
                           'kn': ['N'], 'wh': ['W'],
                           'wr': ['R'], 'gg': ['G'], 'ff': ['F'],
                           'oo': ['UW'], 'ua': ['W', 'AO'], 'ng': ['NG'],
                           'bb': ['B'],
                           'tch': ['CH'], 'rr': ['R'], 'dd': ['D'],
                           'cc': ['K', 'S'], 'oe': ['OW'],
                           'igh': ['AY'], 'eigh': ['EY']}
    phones = []

    progress = len(word) - 1
    while progress >= 0:
        if word[0:3] in basic_pronunciations.keys():
            for phone in basic_pronunciations[word[0:3]]:
                phones.append(phone)
            word = word[3:]
            progress -= 3
        elif word[0:2] in basic_pronunciations.keys():
            for phone in basic_pronunciations[word[0:2]]:
                phones.append(phone)
            word = word[2:]
            progress -= 2
        elif word[0] in basic_pronunciations.keys():
            for phone in basic_pronunciations[word[0]]:
                phones.append(phone)
            word = word[1:]
            progress -= 1
        else:
            return None
    return phones


def get_phonemes(name):
    name = name.lower()
    phonemes = None
    if " " in name:
        total_phonemes = []
        names = name.split(" ")
        for name in names:
            phon = get_phonemes(name)
            if phon is None:
                return None
            total_phonemes.extend(phon)
            total_phonemes.append(" . ")
        if total_phonemes[-1] == " . ":
            total_phonemes = total_phonemes[:-1]
        phonemes = "".join(total_phonemes)
    elif len(pronouncing.phones_for_word(name)):
        phonemes = "".join(pronouncing.phones_for_word(name)[0])
    else:
        guess = guess_phonemes(name)
        if guess is not None:
            phonemes = " ".join(guess)

    return phonemes


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