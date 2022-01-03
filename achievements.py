MEDALS = {
    1: "🎖",  # Star
    2: "🏅",  # Special
    3: "🥇",  # Gold
    4: "🥈",  # Silver
    5: "🥉",  # Bronze
}

ACHIEVEMENTS_ID = {
    "misc": {
        "start": {
            "id": 0x00,
            "medal": MEDALS[2],
            "title": "Le Début de la Fin",
            "text": "You started a new game\.",
        },
        "loutres": {
            "id": 0xff,
            "medal": MEDALS[2],
            "title": "J'aime les Loutres",
            "text": "Tu as exprimé ton amour pour les loutres\!",
        },
    },
    "messages": {
        "total10": {
            "id": 0x01,
            "medal": MEDALS[5],
            "title": "Chatty",
            "text": "You made more than 10 messages\!",
        },
        "total100": {
            "id": 0x02,
            "medal": MEDALS[5],
            "title": "Talky",
            "text": "You made more than 100 messages\!",
        },
        "total1000": {
            "id": 0x03,
            "medal": MEDALS[4],
            "title": "Verbose",
            "text": "You made more than 1'000 messages\!",
        },
        "total10000": {
            "id": 0x04,
            "medal": MEDALS[4],
            "title": "Mouthy",
            "text": "You made more than 10'000 messages\!",
        },
        "total100000": {
            "id": 0x05,
            "medal": MEDALS[3],
            "title": "Prolix",
            "text": "You made more than 100'000 messages\!",
        },
        "total1000000": {
            "id": 0x06,
            "medal": MEDALS[3],
            "title": "Chattering",
            "text": "You made more than 1'000'000 messages\!",
        },
        "quantity10": {
            "id": 0x07,
            "medal": MEDALS[5],
            "title": "Eager",
            "text": "You had more than 10 messages at the same time\!",
        },
        "quantity100": {
            "id": 0x08,
            "medal": MEDALS[5],
            "title": "Avid",
            "text": "You had more than 100 messages at the same time\!",
        },
        "quantity1000": {
            "id": 0x09,
            "medal": MEDALS[4],
            "title": "Craving",
            "text": "You had more than 1'000 messages at the same time\!",
        },
        "quantity10000": {
            "id": 0x0a,
            "medal": MEDALS[4],
            "title": "Grabby",
            "text": "You had more than 10'000 messages at the same time\!",
        },
        "quantity100000": {
            "id": 0x0b,
            "medal": MEDALS[3],
            "title": "Hoggish",
            "text": "You had more than 100'000 messages at the same time\!",
        },
        "quantity1000000": {
            "id": 0x0c,
            "medal": MEDALS[3],
            "title": "Desirous",
            "text": "You had more than 1'000'000 messages at the same time\!",
        },
    },
    "contacts": {
        "unlocked": {
            "id": 0x20,
            "medal": MEDALS[5],
            "title": "Do I know you\?",
            "text": "You can now get Contacts\!",
        },
        "total10": {
            "id": 0x21,
            "medal": MEDALS[5],
            "title": "Sociable",
            "text": "You made more than 10 Contacts\!",
        },
        "total100": {
            "id": 0x22,
            "medal": MEDALS[5],
            "title": "Approchable",
            "text": "You made more than 100 Contacts\!",
        },
        "total1000": {
            "id": 0x23,
            "medal": MEDALS[4],
            "title": "Clubby",
            "text": "You made more than 1'000 Contacts\!",
        },
        "total10000": {
            "id": 0x24,
            "medal": MEDALS[4],
            "title": "Social",
            "text": "You made more than 10'000 Contacts\!",
        },
        "total100000": {
            "id": 0x25,
            "medal": MEDALS[3],
            "title": "Accessible",
            "text": "You made more than 100'000 Contacts\!",
        },
        "total1000000": {
            "id": 0x26,
            "medal": MEDALS[3],
            "title": "Conversable",
            "text": "You made more than 1'000'000 Contacts\!",
        },
        "quantity10": {
            "id": 0x27,
            "medal": MEDALS[5],
            "title": "Extrovert",
            "text": "You had more than 10 Contacts at the same time\!",
        },
        "quantity100": {
            "id": 0x28,
            "medal": MEDALS[5],
            "title": "Trendy",
            "text": "You had more than 100 Contacts at the same time\!",
        },
        "quantity1000": {
            "id": 0x29,
            "medal": MEDALS[4],
            "title": "Approved",
            "text": "You had more than 1'000 Contacts at the same time\!",
        },
        "quantity10000": {
            "id": 0x2a,
            "medal": MEDALS[4],
            "title": "Faddish",
            "text": "You had more than 10'000 Contacts at the same time\!",
        },
        "quantity100000": {
            "id": 0x2b,
            "medal": MEDALS[3],
            "title": "Prominent",
            "text": "You had more than 100'000 Contacts at the same time\!",
        },
        "quantity1000000": {
            "id": 0x2c,
            "medal": MEDALS[3],
            "title": "Famous",
            "text": "You had more than 1'000'000 Contacts at the same time\!",
        },
    },
    "groups": {
        "unlocked": {
            "id": 0x40,
            "medal": MEDALS[5],
            "title": "These Are People",
            "text": "You can now get Groups\!",
        },
        "total10": {
            "id": 0x41,
            "medal": MEDALS[5],
            "title": "Syndicate",
            "text": "You made more than 10 Groups\!",
        },
        "total100": {
            "id": 0x42,
            "medal": MEDALS[5],
            "title": "Suite",
            "text": "You made more than 100 Groups\!",
        },
        "total1000": {
            "id": 0x43,
            "medal": MEDALS[4],
            "title": "Sort",
            "text": "You made more than 1'000 Groups\!",
        },
        "total10000": {
            "id": 0x44,
            "medal": MEDALS[4],
            "title": "Set",
            "text": "You made more than 10'000 Groups\!",
        },
        "total100000": {
            "id": 0x45,
            "medal": MEDALS[3],
            "title": "Posse",
            "text": "You made more than 100'000 Groups\!",
        },
        "total1000000": {
            "id": 0x46,
            "medal": MEDALS[3],
            "title": "Pool",
            "text": "You made more than 1'000'000 Groups\!",
        },
        "quantity10": {
            "id": 0x47,
            "medal": MEDALS[5],
            "title": "Platoon",
            "text": "You had more than 10 Groups at the same time\!",
        },
        "quantity100": {
            "id": 0x48,
            "medal": MEDALS[5],
            "title": "Passel",
            "text": "You had more than 100 Groups at the same time\!",
        },
        "quantity1000": {
            "id": 0x49,
            "medal": MEDALS[4],
            "title": "Parcel",
            "text": "You had more than 1'000 Groups at the same time\!",
        },
        "quantity10000": {
            "id": 0x4a,
            "medal": MEDALS[4],
            "title": "Pack",
            "text": "You had more than 10'000 Groups at the same time\!",
        },
        "quantity100000": {
            "id": 0x4b,
            "medal": MEDALS[3],
            "title": "League",
            "text": "You had more than 100'000 Groups at the same time\!",
        },
        "quantity1000000": {
            "id": 0x4c,
            "medal": MEDALS[3],
            "title": "Gathering",
            "text": "You had more than 1'000'000 Groups at the same time\!",
        },
    },
    "channels": {
        "unlocked": {
            "id": 0x60,
            "medal": MEDALS[5],
            "title": "From One Legend to Another",
            "text": "You can now get Channels\!",
        },
        "total10": {
            "id": 0x61,
            "medal": MEDALS[5],
            "title": "Journalist",
            "text": "You made more than 10 Channels\!",
        },
        "total100": {
            "id": 0x62,
            "medal": MEDALS[5],
            "title": "Broadcaster",
            "text": "You made more than 100 Channels\!",
        },
        "total1000": {
            "id": 0x63,
            "medal": MEDALS[4],
            "title": "Columnist",
            "text": "You made more than 1'000 Channels\!",
        },
        "total10000": {
            "id": 0x64,
            "medal": MEDALS[4],
            "title": "Commentator",
            "text": "You made more than 10'000 Channels\!",
        },
        "total100000": {
            "id": 0x65,
            "medal": MEDALS[3],
            "title": "Editor",
            "text": "You made more than 100'000 Channels\!",
        },
        "total1000000": {
            "id": 0x66,
            "medal": MEDALS[3],
            "title": "Reporter",
            "text": "You made more than 1'000'000 Channels\!",
        },
        "quantity10": {
            "id": 0x67,
            "medal": MEDALS[5],
            "title": "Writer",
            "text": "You had more than 10 Channels at the same time\!",
        },
        "quantity100": {
            "id": 0x68,
            "medal": MEDALS[5],
            "title": "Announcer",
            "text": "You had more than 100 Channels at the same time\!",
        },
        "quantity1000": {
            "id": 0x69,
            "medal": MEDALS[4],
            "title": "Contributor",
            "text": "You had more than 1'000 Channels at the same time\!",
        },
        "quantity10000": {
            "id": 0x6a,
            "medal": MEDALS[4],
            "title": "Cub",
            "text": "You had more than 10'000 Channels at the same time\!",
        },
        "quantity100000": {
            "id": 0x6b,
            "medal": MEDALS[3],
            "title": "Publicist",
            "text": "You had more than 100'000 Channels at the same time\!",
        },
        "quantity1000000": {
            "id": 0x6c,
            "medal": MEDALS[3],
            "title": "Scribe",
            "text": "You had more than 1'000'000 Channels at the same time\!",
        },
    },
    "supergroups": {
        "unlocked": {
            "id": 0x80,
            "medal": MEDALS[5],
            "title": "These Are More People",
            "text": "You can now get Supergroups\!",
        },
        "total10": {
            "id": 0x81,
            "medal": MEDALS[5],
            "title": "Super Syndicate",
            "text": "You made more than 10 Supergroups\!",
        },
        "total100": {
            "id": 0x82,
            "medal": MEDALS[5],
            "title": "Super Suite",
            "text": "You made more than 100 Supergroups\!",
        },
        "total1000": {
            "id": 0x83,
            "medal": MEDALS[4],
            "title": "Super Sort",
            "text": "You made more than 1'000 Supergroups\!",
        },
        "total10000": {
            "id": 0x84,
            "medal": MEDALS[4],
            "title": "Super Set",
            "text": "You made more than 10'000 Supergroups\!",
        },
        "total100000": {
            "id": 0x85,
            "medal": MEDALS[3],
            "title": "Super Posse",
            "text": "You made more than 100'000 Supergroups\!",
        },
        "total1000000": {
            "id": 0x86,
            "medal": MEDALS[3],
            "title": "Super Pool",
            "text": "You made more than 1'000'000 Supergroups\!",
        },
        "quantity10": {
            "id": 0x87,
            "medal": MEDALS[5],
            "title": "Super Platoon",
            "text": "You had more than 10 Supergroups at the same time\!",
        },
        "quantity100": {
            "id": 0x88,
            "medal": MEDALS[5],
            "title": "Super Passel",
            "text": "You had more than 100 Supergroups at the same time\!",
        },
        "quantity1000": {
            "id": 0x89,
            "medal": MEDALS[4],
            "title": "Super Parcel",
            "text": "You had more than 1'000 Supergroups at the same time\!",
        },
        "quantity10000": {
            "id": 0x8a,
            "medal": MEDALS[4],
            "title": "Super Pack",
            "text": "You had more than 10'000 Supergroups at the same time\!",
        },
        "quantity100000": {
            "id": 0x8b,
            "medal": MEDALS[3],
            "title": "Super League",
            "text": "You had more than 100'000 Supergroups at the same time\!",
        },
        "quantity1000000": {
            "id": 0x8c,
            "medal": MEDALS[3],
            "title": "Super Gathering",
            "text": "You had more than 1'000'000 Supergroups at the same time\!",
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
