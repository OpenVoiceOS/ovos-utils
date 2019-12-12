from jarbas_utils.database import JsonDatabase

db = JsonDatabase("users", "~/databases/users.json")

users = [
    {
        "email": "something@mail.net",
        "secret_key": None,
        "data": {
            "name": "jonas",
            "birthday": "12 May"
        }
    },
    {
        "email": "second@mail.net",
        "key": "secret",
        "data": {
            "name": ["joe", "jony"],
            "age": 12
        }
    }
]

for user in users:
    db.add_item(user)

# search entries with non empty secret_key
print(db.search_by_key("secret_key", include_empty=False))

# search in user provided data
print(db.search_by_key("birth", fuzzy=True))

# search entries with a certain value
print(db.search_by_value("age", 12))
print(db.search_by_value("name", "jon", fuzzy=True))
