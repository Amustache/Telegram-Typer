from tlgtyper.helpers import get_si


HELP_COMMANDS = (
    "– Use /new to start a new game\n"
    "– Use /reset to reset a blocked counter.\n"
    "– Use /interface to show the interface.\n"
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
    user, _ = players_instance.get_or_create(player_id)
    message = "– 💬 Messages: {}".format(get_si(user.messages))
    if user.contacts_state:
        message += "\n– 📇 Contacts: {}".format(get_si(user.contacts))
    if user.groups_state:
        message += "\n– 👥 Groups: {}".format(get_si(user.groups))
    if user.channels_state:
        message += "\n– 📰 Channels: {}".format(get_si(user.channels))
    if user.supergroups_state:
        message += "\n– 👥 Supergroups: {}".format(get_si(user.supergroups))

    return message
