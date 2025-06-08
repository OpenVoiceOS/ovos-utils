import re
from difflib import SequenceMatcher
from enum import IntEnum, auto

from ovos_utils.log import LOG

try:
    import rapidfuzz
except ImportError:
    rapidfuzz = None


class MatchStrategy(IntEnum):
    SIMPLE_RATIO = auto()
    RATIO = auto()
    PARTIAL_RATIO = auto()
    TOKEN_SORT_RATIO = auto()
    TOKEN_SET_RATIO = auto()
    PARTIAL_TOKEN_RATIO = auto()
    PARTIAL_TOKEN_SORT_RATIO = auto()
    PARTIAL_TOKEN_SET_RATIO = auto()
    DAMERAU_LEVENSHTEIN_SIMILARITY = auto()


def _validate_matching_strategy(strategy):
    if rapidfuzz is None and strategy != MatchStrategy.SIMPLE_RATIO:
        LOG.error("rapidfuzz is not installed, "
                  "falling back to SequenceMatcher for all match strategies")
        LOG.warning("pip install rapidfuzz")
        return MatchStrategy.SIMPLE_RATIO
    return strategy


def fuzzy_match(x, against, strategy=MatchStrategy.SIMPLE_RATIO):
    """
    Calculates a fuzzy similarity score between two strings using the specified strategy.
    
    Args:
        x: The first string to compare.
        against: The second string to compare.
        strategy: The matching strategy to use (default is SIMPLE_RATIO).
    
    Returns:
        A float between 0.0 and 1.0 indicating the similarity, where 1.0 is a perfect match.
    """
    strategy = _validate_matching_strategy(strategy)
    # LOG.debug(f"matching strategy: {strategy}")
    if strategy == MatchStrategy.RATIO:
        score = rapidfuzz.fuzz.ratio(x, against) / 100
    elif strategy == MatchStrategy.PARTIAL_RATIO:
        score = rapidfuzz.fuzz.partial_ratio(x, against) / 100
    elif strategy == MatchStrategy.TOKEN_SORT_RATIO:
        score = rapidfuzz.fuzz.token_sort_ratio(x, against) / 100
    elif strategy == MatchStrategy.TOKEN_SET_RATIO:
        score = rapidfuzz.fuzz.token_set_ratio(x, against) / 100
    elif strategy == MatchStrategy.PARTIAL_TOKEN_SORT_RATIO:
        score = rapidfuzz.fuzz.partial_token_sort_ratio(x, against) / 100
    elif strategy == MatchStrategy.PARTIAL_TOKEN_SET_RATIO:
        score = rapidfuzz.fuzz.partial_token_set_ratio(x, against) / 100
    elif strategy == MatchStrategy.PARTIAL_TOKEN_RATIO:
        score = rapidfuzz.fuzz.partial_token_ratio(x, against) / 100
    elif strategy == MatchStrategy.DAMERAU_LEVENSHTEIN_SIMILARITY:
        score = rapidfuzz.distance.DamerauLevenshtein.normalized_similarity(x, against)
    else:
        score = SequenceMatcher(None, x, against).ratio()

    return score


def match_one(query, choices, match_func=None, strategy=MatchStrategy.SIMPLE_RATIO, ignore_case=False):
    """
    Finds the best matching entry for a query from a list or dictionary of choices.
    
    Args:
        query: The string to match against the choices.
        choices: A list or dictionary of possible matches.
        match_func: Optional custom function for computing match scores.
        strategy: Matching strategy to use.
        ignore_case: If True, performs case-insensitive matching.
    
    Returns:
        A tuple containing the best match and its score.
    """
    return match_all(query, choices, match_func, strategy, ignore_case)[0]


def match_all(query, choices, match_func=None, strategy=MatchStrategy.SIMPLE_RATIO, ignore_case=False):
    """
    Computes fuzzy match scores for a query against all choices in a list or dictionary.
    
    Args:
        query: The string to match against the choices.
        choices: A list or dictionary of possible matches. If a dictionary, matches are performed against the keys, but the returned matches are the corresponding values.
        match_func: Optional custom function to compute match scores. Defaults to `fuzzy_match`.
        strategy: The matching strategy to use.
        ignore_case: If True, performs case-insensitive matching.
    
    Returns:
        A list of tuples (match, score), sorted by descending score.
    """
    strategy = _validate_matching_strategy(strategy)
    match_func = match_func or fuzzy_match
    if isinstance(choices, dict):
        _choices = list(choices.keys())
    elif isinstance(choices, list):
        _choices = choices
    else:
        raise ValueError('a list or dict of choices must be provided')
    matches = []
    for c in _choices:
        score = match_func(query.lower() if ignore_case else query, 
                       c.lower() if ignore_case else c, 
                       strategy)
        matches.append((choices[c] if isinstance(choices, dict) else c, score))

    # TODO solve ties

    return sorted(matches, key=lambda k: k[1], reverse=True)


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
