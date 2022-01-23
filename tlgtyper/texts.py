from tlgtyper.helpers import get_si


HELP_COMMANDS = (
    "– Use /new to start a new game\n"
    "– Use /reset to reset a blocked counter.\n"
    "– Use /shop to show the shop.\n"
    "– Use /achievements to show your achievements.\n"
    "– Use /stats to get your stats.\n"
    "– Finally, use /end to stop the game and delete your account."
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
