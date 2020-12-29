from difflib import SequenceMatcher
import re
from inflection import singularize as _singularize_en


def singularize(word, lang="en"):
    if lang.startswith("en"):
        return _singularize_en(word)
    return word.rstrip("s")


def split_sentences(text, new_lines=False):
    if new_lines:
        return text.split("\n")

    # normalize ambiguous cases
    words = text.split(" ")
    for idx, w in enumerate(words):
        # prev_w = words[idx-1] if idx > 0 else ""
        # next_w = words[idx + 1] if idx < len(words) - 1 else ""
        if w == ".":
            # handled ambiguous cases
            # "hello . He said" # regex handles these next

            # ignored ambiguous cases
            # "hello . he said"
            pass
        elif "." in w:
            # ignored ambiguous cases
            # "hello. he said"  # could be "Jones Jr. thinks ..."
            # "hello.he said"  # could be  "www.hello.com"
            # "hellO.He said"  # could be  "A.E.I.O.U"

            # handled cases
            # "hello.He said"
            if len(w.split(".")) == 2:
                prev_w, next_w = w.split(".")
                if prev_w and next_w and prev_w[-1].islower() and \
                        next_w[0].isupper():
                    words[idx] = w.replace(".", ";")
    text = " ".join(words)
    # ignored ambiguous cases
    # "hello. he said"  # could be "Jones Jr. thinks ..."
    #

    # handle punctuation delimiters except .
    delims = ["\n", ";", "!", "?"]
    _sentences = [s.strip() for s in re.split(r'(!|\?|\;|\n)*', text) if s not in
                  delims and s.strip()]

    sentences = []
    # handle . but be careful with numbers / names / websites?
    for sent in _sentences:
        sentences += [s.strip() for s in
                      re.split(r'(?<=[^A-Z].[.]) +(?=[A-Z])', sent) if
                      s.strip()]

    return sentences


def fuzzy_match(x, against):
    """Perform a 'fuzzy' comparison between two strings.
    Returns:
        float: match percentage -- 1.0 for perfect match,
               down to 0.0 for no match at all.
    """
    return SequenceMatcher(None, x, against).ratio()


def match_one(query, choices):
    """
        Find best match from a list or dictionary given an input

        Arguments:
            query:   string to test
            choices: list or dictionary of choices

        Returns: tuple with best match, score
    """
    if isinstance(choices, dict):
        _choices = list(choices.keys())
    elif isinstance(choices, list):
        _choices = choices
    else:
        raise ValueError('a list or dict of choices must be provided')

    best = (_choices[0], fuzzy_match(query, _choices[0]))
    for c in _choices[1:]:
        score = fuzzy_match(query, c)
        if score > best[1]:
            best = (c, score)

    if isinstance(choices, dict):
        return (choices[best[0]], best[1])
    else:
        return best


def remove_parentheses(answer):
    # remove [xx] (xx) {xx}
    answer = re.sub(r'\[[^)]*\]', '', answer)
    answer = re.sub(r'\([^)]*\)', '', answer)
    answer = re.sub(r'\{[^)]*\}', '', answer)
    answer = answer.replace("(", "").replace(")", "") \
        .replace("[", "").replace("]", "").replace("{", "") \
        .replace("}", "").strip()
    # remove extra spaces
    words = [w for w in answer.split(" ") if w.strip()]
    answer = " ".join(words)
    if not answer:
        return None
    return answer


def summarize(answer):
    if not answer:
        return None
    return remove_parentheses(split_sentences(answer)[0])


def search_in_text(query, text, lang="en", all_matches=False,
                   thresh=0.1, paragraphs=True):
    words = query.split(" ")
    for idx, word in enumerate(words):
        words[idx] = singularize(word).lower().strip()
    query = " ".join(words)

    # search text inside sections
    candidates = split_sentences(text, paragraphs)
    scores = [0 for i in range(len(candidates))]
    for idx, c in enumerate(candidates):
        if len(c.split(" ")) < 4:
            continue
        score = scores[idx]
        for word in c.split():
            # total half assed scoring metric #1
            # each time query appears in sentence/paragraph boost score
            if len(word) < 3:
                continue
            word = word.lower().strip()
            singular_word = singularize(word, lang).lower().strip()

            if query == word:
                # magic numbers are bad
                score += 0.4
            elif query == singular_word:
                # magic numbers are bad
                score += 0.3
            # partial match
            elif query in word or word in query:
                score += 0.15
            elif query in singular_word or singular_word in query:
                score += 0.1

        scores[idx] = score

    # total half assed scoring metric #3
    # give preference to short sentences
    if not paragraphs:
        for idx, c in enumerate(candidates):
            scores[idx] = scores[idx] / (len(c) / 200 + 0.3)
    else:
        for idx, c in enumerate(candidates):
            scores[idx] = scores[idx] / (len(split_sentences(c)) + 0.1)

    best_score = max(scores)

    # this is a fake percent, sorry folks
    if best_score > 1:
        dif = best_score - 1
        scores = [s - dif for s in scores]
        scores = [s if s > 0 else 0.0001 for s in scores]
        best_score = 1

    if not all_matches:
        best = candidates[scores.index(best_score)]
        return best, best_score

    data = []
    for idx, c in enumerate(candidates):
        if c.strip() and scores[idx] >= thresh:
            data.append((c, scores[idx]))
    data.sort(key=lambda k: k[1], reverse=True)
    return data


def extract_sentences(query, text, lang="en"):
    return search_in_text(query, text, lang,
                          all_matches=True, paragraphs=False)


def extract_paragraphs(query, text, lang="en"):
    return search_in_text(query, text, lang,
                          all_matches=True, paragraphs=True)


if __name__ == "__main__":


    print("## Searching: intent")
    for sent, score in extract_sentences("intent", wiki_dump):
        if score > 0.3:
            print(sent)

    print("## Searching: precise")
    for sent, score in extract_paragraphs("precise", wiki_dump):
        if score > 0.3:
            print(sent)
    exit(0)
    s = "hello. He said"
    for s in split_sentences(s):
        print(s)
    s = "hello . He said"
    for s in split_sentences(s):
        print(s)

    # no splitting
    s = "hello.com"
    for s in split_sentences(s):
        print(s)
    s = "A.E:I.O.U"
    for s in split_sentences(s):
        print(s)

    # ambiguous, but will split
    s = "hello.He said"
    for s in split_sentences(s):
        print(s)

    # ambiguous, no split
    s = "hello. he said"  # could be "Jones Jr. thinks ..."
    for s in split_sentences(s):
        print(s)
    s = "hello.he said"  # could be  "www.hello.com"
    for s in split_sentences(s):
        print(s)
    s = "hello . he said"  # TODO maybe split this one?
    for s in split_sentences(s):
        print(s)

    # test all
    s = "Mr. Smith bought cheapsite.com for 1.5 million dollars, i.e. he paid a lot for it. Did he mind? Adam Jones Jr. thinks he didn't. In any case, this isn't true... Well, with a probability of .9 it isn't.I know right\nOK"
    print(summarize(s))
    for s in split_sentences(s):
        print(s)

    s = "this is {remove me}     the first sentence "
    print(summarize(s))
    s = "       this is (remove me) second. and the 3rd"
    print(summarize(s))
    s = "this       is [remove me] number 4! number5? number6. number 7 \n " \
        "number N"
    print(summarize(s))
