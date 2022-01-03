MEDALS = {
    1: "🎖",  # Star
    2: "🏅",  # Special
    3: "🥇",  # Gold
    4: "🥈",  # Silver
    5: "🥉",  # Bronze
}

ACHIEVEMENTS_ID = {
    "misc": {
        "loutres": {
            "id": 7,
            "medal": MEDALS[1],
            "title": "J'aime les loutres",
            "text": "Tu as exprimé ton amour pour les loutres\!",
        },
    },
    "messages": {
    },
    "contacts": {
        "unlocked": {
            "id": 2,
            "medal": MEDALS[5],
            "title": "Do I know you\?",
            "text": "You can know get Contacts\!",
        },
    },
    "groups": {
        "unlocked": {
            "id": 3,
            "medal": MEDALS[5],
            "title": "These Are People",
            "text": "You can know get Groups\!",
        },
    },
    "channels": {
        "unlocked": {
            "id": 4,
            "medal": MEDALS[5],
            "title": "From One Legend to Another",
            "text": "You can know get Channels\!",
        },
    },
    "supergroups": {
        "unlocked": {
            "id": 5,
            "medal": MEDALS[5],
            "title": "These Are More People",
            "text": "You can know get Supergroups\!",
        },
    },
}


def reverse_achievements(achievements_id=None):
    if achievements_id is None:
        achievements_id = ACHIEVEMENTS_ID
    data = {}
    for category in achievements_id.values():
        for achievement in category.values():
            data.update({achievement["id"]: (achievement["medal"], achievement["title"], achievement["text"])})
    return data


ACHIEVEMENTS = reverse_achievements()

MAX_ACHIEVEMENTS = len(ACHIEVEMENTS)
