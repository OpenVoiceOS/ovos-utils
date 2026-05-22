import warnings
from os import listdir
from os.path import isdir, join
from typing import Optional

from ovos_utils.file_utils import resolve_resource_file
from ovos_utils.log import deprecated
from ovos_utils.version import VERSION_MAJOR


@deprecated("use 'standardize_lang' from 'ovos_spec_tools' instead",
            f"{VERSION_MAJOR + 1}.0.0")
def standardize_lang_tag(lang_code: str, macro=False) -> str:
    """Normalize a BCP-47 language tag.

    By default the region is kept (``en-US`` -> ``en-US``). With
    ``macro=True`` the region is dropped, returning the bare primary language
    subtag (``en-US`` -> ``en``).

    .. deprecated::
        Use :func:`ovos_spec_tools.standardize_lang` — the conformant OVOS
        language-tag normalizer, and what this now delegates to.
    """
    # stacklevel=3: warn() -> this body -> @deprecated wrapper -> caller
    warnings.warn("standardize_lang_tag is deprecated; use 'standardize_lang' "
                  "from 'ovos_spec_tools' instead",
                  DeprecationWarning, stacklevel=3)
    from ovos_spec_tools import standardize_lang
    tag = standardize_lang(lang_code)
    return tag.split("-")[0] if macro else tag


@deprecated("use 'closest_lang' from 'ovos_spec_tools' "
            "(or 'ovos_spec_tools.LocaleResources')",
            f"{VERSION_MAJOR + 1}.0.0")
def get_language_dir(base_path: str, lang: str = "en-US") -> Optional[str]:
    """Return the best-matching ``<lang>/`` directory under ``base_path``.

    .. deprecated::
        Use :func:`ovos_spec_tools.closest_lang` to resolve a language tag
        against the available ones, or :class:`ovos_spec_tools.LocaleResources`
        which resolves locale directories itself.
    """
    # stacklevel=3: warn() -> this body -> @deprecated wrapper -> caller
    warnings.warn("get_language_dir is deprecated; use 'closest_lang' from "
                  "'ovos_spec_tools' (or 'ovos_spec_tools.LocaleResources')",
                  DeprecationWarning, stacklevel=3)
    from ovos_spec_tools import closest_lang
    try:
        names = [f for f in listdir(base_path) if isdir(join(base_path, f))]
    except (FileNotFoundError, NotADirectoryError):
        return None
    # closest_lang accepts a tag distance below 10 — the same threshold this
    # used previously (OVOS-INTENT-2 §2.2).
    match = closest_lang(lang, names)
    return join(base_path, match) if match is not None else None


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
