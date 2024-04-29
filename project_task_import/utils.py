import itertools

__all__ = [
    "prepare_tags",
    "extract_tags",
    "set_tags",
    "extract",
    "set_parents",
    "set_key",
]


def prepare_tags(vals_list, keys, mode="value"):
    """
    mode 'value': [{'key 1': 'a', 'key 2': 'b']}, ...] => [{'tags': ['a', 'b']}, ...]
    mode 'key': [{'key 3': 1.0, 'key 4': None]}, ...] => [{'tags': ['key 3']}, ...]
    """

    def apply(vals):
        vals.setdefault("tags", [])
        if mode == "value":
            tags = [v for k, v in vals.items() if v and k in keys]
        else:
            tags = [k for k, v in vals.items() if v and k in keys]
        vals["tags"] += tags

        return vals

    return list(map(apply, vals_list))


def extract_tags(vals_list):
    """
    [{'tags': ['a', 'b']}, {'tags': ['b', 'c']}]
        => ['a', 'b', 'c']
    """

    def search(vals):
        return vals.get("tags", [])

    return set(itertools.chain(*map(search, vals_list)))


def set_tags(vals_list, mapping):
    """
    [{'tags': ['a', 'b']}, {'tags': ['b', 'c']}]
        => [{'tag_ids': [6, False, [1,2]]}, {'tag_ids': [6, False, [2,3]]}]
    """

    def apply(vals: dict):
        names = vals.pop("tags")
        if not names:
            return vals

        tags = [mapping.get(k) for k in names]
        tags = list(filter(bool, tags))
        vals["tag_ids"] = [(6, False, tags)] if tags else False
        return vals

    return list(map(apply, vals_list))


def extract(vals_list, key, default=False):
    """
    [{'key': 'a'}, {'key': 'a'}, {'key': False}] => ['a']
    """

    def search(vals):
        return vals.get(key, default)

    return list(set(filter(bool, map(search, vals_list))))


def set_key(vals_list, key, value, default=False):
    """Set key/value on list of dicts"""

    def apply(vals: dict):
        vals[key] = value
        return vals

    return list(map(apply, vals_list))


def set_parents(vals_list, mapping, key, default=False):
    """Retrieve and set parent ID from mapping dict"""

    def apply(vals: dict):
        vals["parent_id"] = mapping.get(vals.get(key, default), default)
        return vals

    return list(map(apply, vals_list))
