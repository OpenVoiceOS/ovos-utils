from typing import Optional

from ovos_utils.lang import translate_word


def join_list(items: list, connector: str, sep: Optional[str] = None,
              lang: Optional[str] = '') -> str:
    """
    Join a list into a phrase using the given connector word
    Examples:
        join_list([1,2,3], "and") ->  "1, 2 and 3"
        join_list([1,2,3], "and", ";") ->  "1; 2 and 3"
    Args:
        items (array): items to be joined
        connector (str): connecting word (resource name), like "and" or "or"
        sep (str, optional): separator character, default = ","
        lang (str, optional): an optional BCP-47 language code, if omitted
                              the default language will be used.
    Returns:
        str: the connected list phrase
    """

    if not items:
        return ""
    if len(items) == 1:
        return str(items[0])

    if not sep:
        sep = ", "
    else:
        sep += " "
    return (sep.join(str(item) for item in items[:-1]) +
            " " + translate_word(connector, lang) +
            " " + items[-1])
