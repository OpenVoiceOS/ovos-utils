import re
import string
import unicodedata

def camel_case_split(identifier: str) -> str:
    """
    Split a camel case string into words.

    Args:
        identifier (str): The camel case string to split.

    Returns:
        str: A string with words separated by spaces.
    """
    regex = '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)'
    matches = re.finditer(regex, identifier)
    return ' '.join([m.group(0) for m in matches])

def collapse_whitespaces(text: str) -> str:
    """
    Collapse multiple consecutive whitespace characters into a single space.

    Args:
        text (str): The input string.

    Returns:
        str: The string with collapsed whitespace.
    """
    return re.sub(r'\s+', ' ', text)

def rm_parentheses(text: str) -> str:
    """
    Remove text enclosed in parentheses from the given string.

    Args:
        text (str): Input string.

    Returns:
        str: String with parentheses and their contents removed.
    """
    return re.sub(r"\((.*?)\)", "", text).replace("  ", " ")

def remove_accents_and_punct(input_str: str) -> str:
    """
    Normalize the input string by removing accents and punctuation (except for '{' and '}').

    Args:
        input_str (str): The input string to be processed.

    Returns:
        str: The processed string with accents and punctuation removed.
    """
    rm_chars = [c for c in string.punctuation if c not in ("{", "}")]
    # Normalize to NFD (Normalization Form Decomposed), which separates characters and diacritical marks
    nfkd_form = unicodedata.normalize('NFD', input_str)
    # Remove characters that are not ASCII letters or punctuation we want to keep
    return ''.join([char for char in nfkd_form
                    if unicodedata.category(char) != 'Mn' and char not in rm_chars])
