from jarbas_utils.configuration import LocalConf
from jarbas_utils.json_helper import get_value_recursively_fuzzy, get_value_recursively, \
    get_key_recursively, get_key_recursively_fuzzy, jsonify_recursively
from os.path import expanduser, isdir, dirname
from os import makedirs
import json
from pprint import pprint


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

    def search_by_key(self, key, fuzzy=False, thresh=0.7, include_empty=False):
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