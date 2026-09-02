from os.path import join

from ovos_utils.file_utils import resolve_resource_file


def translate_word(name, lang='en-US'):
    """ Helper to get word translations
    Args:
        name (str): Word name. Returned as the default value if not translated
        lang (str, optional): an optional BCP-47 language code, if omitted
                              the default language will be used.
    Returns:
        str: translated version of resource name
    """
    filename = resolve_resource_file(join("text", lang, name + ".word"))
    if filename:
        # open the file
        try:
            with open(filename, 'r', encoding='utf8') as f:
                for line in f:
                    word = line.strip()
                    if word.startswith("#"):
                        continue  # skip comment lines
                    return word
        except Exception:
            pass
    return name  # use resource name as the word
