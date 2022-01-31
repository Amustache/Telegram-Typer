from tlgtyper.helpers import get_si


HELP_COMMANDS = (
    "– Use /new to start a new game\n"
    "– Use /reset to reset a blocked counter.\n"
    "– Use /shop to show the shop.\n"
    "– Use /achievements to show your achievements.\n"
    "– Use /stats to get your stats.\n"
    "– Finally, use /end to stop the game and delete your account."
)

SUFFIXES_MEANING = (
    "Suffixes:\n"
    "– 1 k = One thousand\n"
    "– 1 M = One million\n"
    "– 1 G = One milliard\n"
    "– 1 T = One billion\n"
    "– 1 P = One billiard\n"
    "– 1 E = One trillion\n"
    "– 1 Z = One trilliard\n"
    "– 1 Y = One quadrillion\n"
    "... And then it gets weird..."
    "– 1 AA = 10²⁷\n"
    "– 1 AAA = 10¹⁰²\n"
    "– 1 AAAA = 10¹⁸⁰\n"
)

BLABLA_TEXT = [
    "Something",
    "Whatsoever",
    "Blah blah blah",
    "So and so",
    "The like",
    "And so forth",
    "All that jazz",
    "Etc.",
    "Suchlike",
    "Whatever",
    "Et cetera",
    "And on and on",
    "And so on and so forth",
    "And all",
    "Yada yada yada",
    "Stuff and nonsense",
    "Gobbledegook",
    "Blether",
    "Claptrap",
    "Rubbish",
]


def get_quantities(player_id: int, players_instance) -> str:
    stats = players_instance.get_stats(player_id)

    message = "– {} Messages: {}".format(stats["messages"]["symbol"], get_si(stats["messages"]["quantity"]))
    for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
        if "unlock_at" in attrs and stats[item]["unlocked"]:
            message += "\n– {} {}: {}".format(stats[item]["symbol"], item.capitalize(), get_si(stats[item]["quantity"]))

    return message
