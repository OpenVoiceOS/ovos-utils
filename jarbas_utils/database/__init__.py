from jarbas_utils.configuration import LocalConf
from jarbas_utils import fuzzy_match
from os.path import expanduser, isdir, dirname
from os import makedirs
import json
from pprint import pprint


def get_key_recursively(search_dict, field, filter_None=False):
    # TODO 0.3.0 filter_None = True by default
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():
        if value is None and filter_None:
            continue
        if key == field:
            fields_found.append(search_dict)

        elif isinstance(value, dict):
            fields_found += get_key_recursively(value, field, filter_None)

        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    try:
                        item = item.__dict__
                        if get_key_recursively(item, field, filter_None):
                            fields_found.append(search_dict)
                    except:
                        continue  # can't parse
                else:
                    fields_found += get_key_recursively(item, field, filter_None)

    return fields_found


def get_key_recursively_fuzzy(search_dict, field, thresh=0.6, filter_None=False):
    # TODO 0.3.0 filter_None = True by default
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    if not isinstance(search_dict, dict) and not isinstance(search_dict, list):  # TODO check for generic iterable
        try:
            search_dict = search_dict.__dict__
        except:
            pass  # probably can't parse

    fields_found = []

    for key, value in search_dict.items():
        if value is None and filter_None:
            continue
        score = 0
        if isinstance(key, str):
            score = fuzzy_match(key, field)

        if score >= thresh:
            fields_found.append((search_dict, score))
        elif isinstance(value, dict):
            fields_found += get_key_recursively_fuzzy(value, field, thresh, filter_None)

        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    try:
                        item = item.__dict__
                        if get_key_recursively_fuzzy(item, field, thresh, filter_None):
                            fields_found.append((search_dict, score))
                    except:
                        continue  # can't parse
                else:
                    fields_found += get_key_recursively_fuzzy(item, field, thresh, filter_None)
    return sorted(fields_found, key = lambda i: i[1],reverse=True)


def get_value_recursively(search_dict, field, target_value):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():

        if key == field and value == target_value:
            fields_found.append(search_dict)

        elif isinstance(value, dict):
            fields_found += get_value_recursively(value, field, target_value)

        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    try:
                        item = item.__dict__
                        if get_value_recursively(item, field, target_value):
                            fields_found.append(search_dict)
                    except:
                        continue  # can't parse
                else:
                    fields_found += get_value_recursively(item, field, target_value)

    return fields_found


def get_value_recursively_fuzzy(search_dict, field, target_value, thresh=0.6):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []
    for key, value in search_dict.items():
        if key == field:
            if isinstance(value, str):
                score = fuzzy_match(target_value, value)
                if score >= thresh:
                    fields_found.append((search_dict, score))
            elif isinstance(value, list):
                for item in value:
                    score = fuzzy_match(target_value, item)
                    if score >= thresh:
                        fields_found.append((search_dict, score))
        elif isinstance(value, dict):
            fields_found += get_value_recursively_fuzzy(value, field, target_value, thresh)

        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    try:
                        found = get_value_recursively_fuzzy(item.__dict__, field, target_value, thresh)
                        if len(found):
                            fields_found.append((item, found[0][1]))
                    except:
                        continue  # can't parse
                else:
                    fields_found += get_value_recursively_fuzzy(item, field, target_value, thresh)

    return sorted(fields_found, key = lambda i: i[1],reverse=True)


def jsonify_recursively(thing):
    if isinstance(thing, list):
        jsonified = thing
        for idx, item in enumerate(thing):
            jsonified[idx] = jsonify_recursively(item)
    elif isinstance(thing, dict):
        if isinstance(thing, JsonDatabase):
            jsonified = dict(thing.db)
        else:
            jsonified = dict(thing)
        for key in jsonified.keys():
            value = jsonified[key]
            jsonified[key] = jsonify_recursively(value)
    else:
        try:
            jsonified = thing.__dict__
        except:
            jsonified = thing
    return jsonified


class JsonDatabase(LocalConf):
    def __init__(self, name, path=None):
        super().__init__(path)
        self.name = name
        self.db = LocalConf(None)
        self.db[name] = []

    def __repr__(self):
        return str(jsonify_recursively(self))

    def __getitem__(self, item):
        return self.get_key(item)

    def __setitem__(self, key, value):
        self.add_item({key: value})

    def get_key(self, key):
        return self.db.get(key)

    def add_item(self, value):
        self.db[self.name] += [value]

    def search_by_key(self, key, fuzzy=False, thresh=0.7, include_empty=True):
        # TODO 0.3.0 include_empty=False by default
        if fuzzy:
            return get_key_recursively_fuzzy(self.db, key, thresh, not include_empty)
        return get_key_recursively(self.db, key, not include_empty)

    def search_by_value(self, key, value, fuzzy=False, thresh=0.7):
        if fuzzy:
            return get_value_recursively_fuzzy(self.db, key, value, thresh)
        return get_value_recursively(self.db, key, value)

    def commit(self):
        self.store()

    def reset(self):
        self.reload()

    # those are overrides for compatibility, you should not use them directly
    def reload(self):
        if not self.path:
            raise ValueError("database path not set")
        self.db.load_local(self.path)

    def store(self, path=None):
        """
            store the configuration locally.
        """
        path = path or self.path
        path = expanduser(path)
        if not path:
            raise ValueError("database path not set")
        if not isdir(dirname(path)):
            makedirs(dirname(path))
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(jsonify_recursively(self), f, indent=4, ensure_ascii=False)

    def print(self):
        pprint(jsonify_recursively(self))


if __name__ == "__main__":
    db = JsonDatabase("users")
    for user in [
            {"name": "bob", "age": 12},
            {"name": "bobby"},
            {"name": ["joe", "jony"]},
            {"name": "john"},
            {"name": "jones", "age": 35},
            {"name": "jorge"},
            {"name": "joey",  "birthday": "may 12"} ]:
        db.add_item(user)


    print(db.search_by_key("age"))
    print(db.search_by_key("birth", fuzzy=True))

    print(db.search_by_value("age", 12))
    print(db.search_by_value("name", "jon", fuzzy=True))