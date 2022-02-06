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
        "base_price": {"messages": 2},
        "gain": {"messages": 0.02, "contacts": 0.0},
    },
    "groups": {
        "id": "g",
        "symbol": "👥",
        "unlock_at": {"messages": 100, "contacts": 4},
        "base_price": {"messages": 100, "contacts": 4},
        "gain": {"messages": 0.2, "contacts": 0.001},
    },
    "channels": {
        "id": "h",
        "symbol": "📰",
        "unlock_at": {"messages": 1000, "contacts": 16},
        "base_price": {"messages": 1000, "contacts": 16},
        "gain": {"messages": 2.0, "contacts": 0.01},
    },
    "supergroups": {
        "id": "s",
        "symbol": "👥",
        "unlock_at": {"messages": 10000, "contacts": 256, "groups": 1},
        "base_price": {"messages": 10000, "contacts": 256, "groups": 1},
        "gain": {"messages": 20.0, "contacts": 0.1},
    },
}


def get_price(base_price: int, cur_items: int) -> int:
    try:
        return ceil(base_price * FACTOR ** cur_items)
    except OverflowError:
        return CAP


def get_price_for_n(base_price: int, cur_items: int, wanted_items: int) -> int:
    try:
        # See https://en.wikipedia.org/wiki/Geometric_progression#Geometric_series
        return ceil(abs(base_price * ((FACTOR ** cur_items) - (FACTOR ** (cur_items + wanted_items))) / (1 - FACTOR)))
    except OverflowError:
        return CAP


def get_max_to_buy(base_price: int, cur_items: int, max_price: int) -> int:
    try:
        value = 1 - (max_price / base_price) * (1 - FACTOR) / (FACTOR ** cur_items)
        return floor(log(value, FACTOR))
    except OverflowError:
        return CAP


def id_to_item_name(item_id: str):
    for item, attrs in ITEMS.items():
        if attrs["id"] == item_id:
            return item
    return None


UPGRADES = {
    "messages": {
        0xFF: {
            "title": "Test",
            "text": "Magic messages\!",
            "conditions": {"messages": 1},
            "cost": {"messages": 1000},
            "effect": lambda x: x + 1,
        },
    },
    "contacts": {
        0x01: {
            "title": "Exponential",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 1},
            "cost": {"messages": 1000},
            "effect": lambda x: 2 * x,
        },
        0x02: {
            "title": "Aggressive",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 5},
            "cost": {"messages": 5000},
            "effect": lambda x: 2 * x,
        },
        0x03: {
            "title": "Ascending",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 10},
            "cost": {"messages": 10000},
            "effect": lambda x: 2 * x,
        },
        0x04: {
            "title": "Epidemic",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 25},
            "cost": {"messages": 50000},
            "effect": lambda x: 2 * x,
        },
        0x05: {
            "title": "Augmented",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 50},
            "cost": {"messages": 100000},
            "effect": lambda x: 2 * x,
        },
        0x06: {
            "title": "Expanding",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 75},
            "cost": {"messages": 500000},
            "effect": lambda x: 2 * x,
        },
        0x07: {
            "title": "Growing",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 100},
            "cost": {"messages": 1000000},
            "effect": lambda x: 2 * x,
        },
        0x08: {
            "title": "Mounting",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 150},
            "cost": {"messages": 5000000},
            "effect": lambda x: 2 * x,
        },
        0x09: {
            "title": "Rampant",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 200},
            "cost": {"messages": 10000000},
            "effect": lambda x: 2 * x,
        },
        0x0A: {
            "title": "Spreading",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 250},
            "cost": {"messages": 50000000},
            "effect": lambda x: 2 * x,
        },
        0x0B: {
            "title": "Wanton",
            "text": "Contacts are twice as efficient\!",
            "conditions": {"contacts": 500},
            "cost": {"messages": 100000000},
            "effect": lambda x: 2 * x,
        },
    },
    "groups": {
        0x21: {
            "title": "Cool Name",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 1},
            "cost": {"messages": 1000},
            "effect": lambda x: 2 * x,
        },
        0x22: {
            "title": "Polls",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 5},
            "cost": {"messages": 5000},
            "effect": lambda x: 2 * x,
        },
        0x23: {
            "title": "Chat History",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 10},
            "cost": {"messages": 10000},
            "effect": lambda x: 2 * x,
        },
        0x24: {
            "title": "Invite Link",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 25},
            "cost": {"messages": 50000},
            "effect": lambda x: 2 * x,
        },
        0x25: {
            "title": "Changing the Profile Pic",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 50},
            "cost": {"messages": 100000},
            "effect": lambda x: 2 * x,
        },
        0x26: {
            "title": "Description is Optional",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 75},
            "cost": {"messages": 500000},
            "effect": lambda x: 2 * x,
        },
        0x27: {
            "title": "Reactions",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 100},
            "cost": {"messages": 1000000},
            "effect": lambda x: 2 * x,
        },
        0x28: {
            "title": "Now with Bots",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 150},
            "cost": {"messages": 5000000},
            "effect": lambda x: 2 * x,
        },
        0x29: {
            "title": "Moderators",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 200},
            "cost": {"messages": 10000000},
            "effect": lambda x: 2 * x,
        },
        0x2A: {
            "title": "Funny Memes Generator",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 250},
            "cost": {"messages": 50000000},
            "effect": lambda x: 2 * x,
        },
        0x2B: {
            "title": "Shitposting Contests",
            "text": "Groups are twice as efficient\!",
            "conditions": {"groups": 500},
            "cost": {"messages": 100000000},
            "effect": lambda x: 2 * x,
        },
    },
    "channels": {
        0x41: {
            "title": "Notifications On",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 1},
            "cost": {"messages": 1000},
            "effect": lambda x: 2 * x,
        },
        0x42: {
            "title": "Scheduled Messages",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 5},
            "cost": {"messages": 5000},
            "effect": lambda x: 2 * x,
        },
        0x43: {
            "title": "Anonymous Polls",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 10},
            "cost": {"messages": 10000},
            "effect": lambda x: 2 * x,
        },
        0x44: {
            "title": "Discussion Group",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 25},
            "cost": {"messages": 50000},
            "effect": lambda x: 2 * x,
        },
        0x45: {
            "title": "Channel is now Public",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 50},
            "cost": {"messages": 100000},
            "effect": lambda x: 2 * x,
        },
        0x46: {
            "title": "Sign your Messages",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 75},
            "cost": {"messages": 500000},
            "effect": lambda x: 2 * x,
        },
        0x47: {
            "title": "Reactions are RAD",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 100},
            "cost": {"messages": 1000000},
            "effect": lambda x: 2 * x,
        },
        0x48: {
            "title": "Keep Track of Recent Actions",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 150},
            "cost": {"messages": 5000000},
            "effect": lambda x: 2 * x,
        },
        0x49: {
            "title": "Moar Admins",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 200},
            "cost": {"messages": 10000000},
            "effect": lambda x: 2 * x,
        },
        0x4A: {
            "title": "Automating with Bots",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 250},
            "cost": {"messages": 50000000},
            "effect": lambda x: 2 * x,
        },
        0x4B: {
            "title": "In a Collective",
            "text": "Channels are twice as efficient\!",
            "conditions": {"channels": 500},
            "cost": {"messages": 100000000},
            "effect": lambda x: 2 * x,
        },
    },
    "supergroups": {
        0x61: {
            "title": "Public Link",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 1},
            "cost": {"messages": 1000},
            "effect": lambda x: 2 * x,
        },
        0x62: {
            "title": "Recent Actions",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 5},
            "cost": {"messages": 5000},
            "effect": lambda x: 2 * x,
        },
        0x63: {
            "title": "Bots Bots Bots",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 10},
            "cost": {"messages": 10000},
            "effect": lambda x: 2 * x,
        },
        0x64: {
            "title": "Custom Admin Titles",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 25},
            "cost": {"messages": 50000},
            "effect": lambda x: 2 * x,
        },
        0x65: {
            "title": "Fast Mode",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 50},
            "cost": {"messages": 100000},
            "effect": lambda x: 2 * x,
        },
        0x66: {
            "title": "Gameee",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 75},
            "cost": {"messages": 500000},
            "effect": lambda x: 2 * x,
        },
        0x67: {
            "title": "Group Stickers",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 100},
            "cost": {"messages": 1000000},
            "effect": lambda x: 2 * x,
        },
        0x68: {
            "title": "Permanent Link",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 150},
            "cost": {"messages": 5000000},
            "effect": lambda x: 2 * x,
        },
        0x69: {
            "title": "Banning Nazis",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 200},
            "cost": {"messages": 10000000},
            "effect": lambda x: 2 * x,
        },
        0x6A: {
            "title": "Weekly Contest",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 250},
            "cost": {"messages": 50000000},
            "effect": lambda x: 2 * x,
        },
        0x6B: {
            "title": "Durov is In There",
            "text": "Supergroups are twice as efficient\!",
            "conditions": {"supergroups": 500},
            "cost": {"messages": 100000000},
            "effect": lambda x: 2 * x,
        },
    },
}


def accumulate_upgrades(item: str, upgrades_ids: str, base_value: float) -> float:
    if upgrades_ids:
        upgrades_ids = [int(upgrade_id) for upgrade_id in upgrades_ids.split(",") if upgrade_id]
        result = base_value
        for fun in [UPGRADES[item][upgrade_id]["effect"] for upgrade_id in upgrades_ids]:
            result = fun(result)
        return result
    return base_value
