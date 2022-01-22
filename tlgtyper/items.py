from math import ceil, floor, log


from parameters import CAP, FACTOR


ITEMS = {
    "messages": {
        "id": "m",
        "symbol": "💬",
        "unlock_at": None,
        "base_price": None,
        "gain": None,
    },
    "contacts": {
        "id": "c",
        "symbol": "📇",
        "unlock_at": {"messages": 10},
        "base_price": {"messages": 10},
        "gain": {"messages": 0.02, "contacts": 0.00001},
    },
    "groups": {
        "id": "g",
        "symbol": "👥",
        "unlock_at": {"messages": 100, "contacts": 4},
        "base_price": {"messages": 100, "contacts": 4},
        "gain": {"messages": 0.2, "contacts": 0.0001},
    },
    "channels": {
        "id": "h",
        "symbol": "📰",
        "unlock_at": {"messages": 1000, "contacts": 16},
        "base_price": {"messages": 1000, "contacts": 16},
        "gain": {"messages": 2, "contacts": 0.001},
    },
    "supergroups": {
        "id": "s",
        "symbol": "👥",
        "unlock_at": {"messages": 10000, "contacts": 256, "groups": 1},
        "base_price": {"messages": 10000, "contacts": 256, "groups": 1},
        "gain": {"messages": 20, "contacts": 0.01},
    },
}

UPGRADES = {
    "messages": {None},
    "contacts": {
        0x01: {
            "title": "Test",
            "text": "Contacts are twice as efficient\!",
            "effect": lambda x: 2 * x,
        },
    },
}


def accumulate_upgrades(item: str, upgrades_ids: str, base_value: int) -> float:
    if upgrades_ids:
        upgrades_ids = [int(upgrade_id) for upgrade_id in upgrades_ids.split(",") if upgrade_id]
        result = base_value
        for fun in [UPGRADES[item][upgrade_id]["effect"] for upgrade_id in upgrades_ids]:
            result = fun(result)
        return result
    return base_value


def get_price(base_price: int, cur_items: int) -> int:
    try:
        return int(base_price * FACTOR ** cur_items)
    except OverflowError:
        return CAP


def get_price_for_n(base_price: int, cur_items: int, wanted_items: int) -> int:
    try:
        # See https://en.wikipedia.org/wiki/Geometric_progression#Geometric_series
        return int(abs(base_price * ((FACTOR ** cur_items) - (FACTOR ** (cur_items + wanted_items))) / (1 - FACTOR)))
    except OverflowError:
        return CAP


def get_max_to_buy(base_price: int, cur_items: int, max_price: int) -> int:
    try:
        value = 1 - (max_price / base_price) * (1 - FACTOR) / (FACTOR ** cur_items)
        return floor(log(value, FACTOR))
    except OverflowError:
        return CAP
