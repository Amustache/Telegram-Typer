from parameters import FACTOR

ITEMS = {
    "messages": {
        "id": "m",
        "unlock_at": None,
        "base_price": None,
        "gain": None,
    },
    "contacts": {
        "id": "c",
        "unlock_at": {"messages": 10},
        "base_price": {"messages": 10},
        "gain": {"messages": 0.02, "contacts": 0.00001},
    },
    "groups": {
        "id": "g",
        "unlock_at": {"messages": 100, "contacts": 4},
        "base_price": {"messages": 100, "contacts": 4},
        "gain": {"messages": 0.2, "contacts": 0.0001},
    },
    "channels": {
        "id": "h",
        "unlock_at": {"messages": 1000, "contacts": 16},
        "base_price": {"messages": 1000, "contacts": 16},
        "gain": {"messages": 2, "contacts": 0.001},
    },
    "supergroups": {
        "id": "s",
        "unlock_at": {"messages": 10000, "contacts": 256, "groups": 1},
        "base_price": {"messages": 10000, "contacts": 256, "groups": 1},
        "gain": {"messages": 20, "contacts": 0.01},
    },
}


def get_price(base_price: int, cur_items: int) -> float:
    return base_price * FACTOR ** cur_items


def get_price_for_n(base_price: int, cur_items: int, wanted_items: int) -> float:
    # See https://en.wikipedia.org/wiki/Geometric_progression#Geometric_series
    return base_price * ((FACTOR ** cur_items) - (FACTOR ** wanted_items)) / (1 - FACTOR)
