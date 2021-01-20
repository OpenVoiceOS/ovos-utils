import json
from json_database.utils import is_jsonifiable, get_key_recursively, \
    get_key_recursively_fuzzy, get_value_recursively_fuzzy, \
    get_value_recursively, jsonify_recursively


def merge_dict(base, delta, merge_lists=False, skip_empty=False,
               no_dupes=True, new_only=False):
    """
        Recursively merges two dictionaries
        including dictionaries within dictionaries.

        Args:
            base:  Target for merge
            delta: Dictionary to merge into base
            merge_lists: if a list is found merge contents instead of replacing
            skip_empty: if an item in delta is empty, dont overwrite base
            no_dupes: when merging lists deduplicate entries
            new_only: only merge keys not yet in base
    """

    for k, d in delta.items():
        b = base.get(k)
        if isinstance(d, dict) and isinstance(b, dict):
            merge_dict(b, d, merge_lists, skip_empty, no_dupes, new_only)
        else:
            if new_only and k in base:
                continue
            if skip_empty and d in [None, "", []]:
                # dont replace if new entry is empty
                # False and 0 should still be replaced
                pass
            elif all((isinstance(b, list), isinstance(d, list), merge_lists)):
                if no_dupes:
                    base[k] += [item for item in d if item not in base[k]]
                else:
                    base[k] += d
            else:
                base[k] = d
    return base


def load_commented_json(filename):
    """ Loads an JSON file, ignoring comments

    Supports a trivial extension to the JSON file format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.

    NOTE: A file created with these style comments will break strict JSON
          parsers.  This is similar to but lighter-weight than "human json"
          proposed at https://hjson.org

    Args:
        filename (str):  path to the commented JSON file

    Returns:
        obj: decoded Python object
    """
    with open(filename) as f:
        contents = f.read()

    return json.loads(uncomment_json(contents))


def uncomment_json(commented_json_str):
    """ Removes comments from a JSON string.

    Supporting a trivial extension to the JSON format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.

    Example...
       {
         // comment
         'name' : 'value'
       }

    Args:
        commented_json_str (str):  a JSON string

    Returns:
        str: uncommented, legal JSON
    """
    lines = commented_json_str.splitlines()
    # remove all comment lines, starting with // or #
    nocomment = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        nocomment.append(line)

    return " ".join(nocomment)

