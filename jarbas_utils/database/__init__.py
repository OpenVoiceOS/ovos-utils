from jarbas_utils.configuration import LocalConf
from jarbas_utils import fuzzy_match


def get_key_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():

        if key == field:
            fields_found.append(search_dict)

        elif isinstance(value, dict):
            fields_found += get_key_recursively(value, field)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    fields_found += get_key_recursively(item, field)

    return fields_found


def get_key_recursively_fuzzy(search_dict, field, thresh=0.6):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():
        score = 0
        if isinstance(key, str):
            score = fuzzy_match(key, field)

        if score >= thresh:
            fields_found.append((search_dict, score))
        elif isinstance(value, dict):
            fields_found += get_key_recursively_fuzzy(value, field, thresh)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    fields_found += get_key_recursively_fuzzy(item, field, thresh)

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
                if isinstance(item, dict):
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
                if isinstance(item, dict):
                    fields_found += get_value_recursively_fuzzy(item, field, target_value, thresh)

    return sorted(fields_found, key = lambda i: i[1],reverse=True)


class JsonDatabase(LocalConf):
    def __init__(self, name, path=None):
        super().__init__(path)
        self.name = name
        self.db = LocalConf(None)
        self.db[name] = []

    def __repr__(self):
        return str(self.db)

    def __getitem__(self, item):
        return self.get_key(item)

    def __setitem__(self, key, value):
        self.add_item({key: value})

    def get_key(self, key):
        return self.db.get(key)

    def add_item(self, value):
        self.db[self.name] += [value]

    def search_by_key(self, key, fuzzy=False, thresh=0.7):
        if fuzzy:
            return get_key_recursively_fuzzy(self.db, key, thresh)
        return get_key_recursively(self.db, key)

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
        if not path:
            raise ValueError("database path not set")
        self.db.store(self.path)


if __name__ == "__main__":
    db = JsonDatabase(None)
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