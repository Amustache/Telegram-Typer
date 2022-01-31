from telegram.ext import CallbackContext


from parameters import CAP, TIME_INTERVAL
from tlgtyper.achievements import ACHIEVEMENTS_ID
from tlgtyper.helpers import power_10
from tlgtyper.items import accumulate_upgrades


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def update_job(player_id: int, context: CallbackContext, players_instance) -> None:
    try:
        remove_job_if_exists(str(player_id), context)
        context.job_queue.run_repeating(
            update_messages_and_contacts_from_job,
            TIME_INTERVAL,
            context=(player_id, players_instance),
            name=str(player_id),
        )
    except (IndexError, ValueError):
        return


def start_all_jobs(dispatcher, players_instance) -> None:
    for player in players_instance.Model.select():
        player_id = player.id
        # try:
        remove_job_if_exists(str(player_id), dispatcher)
        dispatcher.job_queue.run_repeating(
            update_messages_and_contacts_from_job,
            TIME_INTERVAL,
            context=(player_id, players_instance),
            name=str(player_id),
        )
        # except (IndexError, ValueError) as e:
        #     pass


def update_messages_and_contacts_from_job(context: CallbackContext) -> None:
    player_id, players_instance = context.job.context
    stats = players_instance.get_stats(player_id)

    messages_to_add = 0
    contacts_to_add = 0

    messages_to_add += players_instance.cache[player_id]["from_chat"]
    players_instance.cache[player_id]["from_chat"] = 0

    for item, attrs in stats.items():
        if "unlock_at" in attrs and stats[item]["unlocked"]:
            messages_to_add += (
                accumulate_upgrades(item, stats[item]["upgrades"], stats[item]["gain"]["messages"])
                * stats[item]["quantity"]
            )
            contacts_to_add += (
                accumulate_upgrades(item, stats[item]["upgrades"], stats[item]["gain"]["contacts"])
                * stats[item]["quantity"]
            )

    try:
        messages_to_add = int(messages_to_add)
    except OverflowError as e:
        messages_to_add = CAP

    try:
        contacts_to_add = int(contacts_to_add)
    except OverflowError as e:
        contacts_to_add = CAP

    if messages_to_add > 0:
        players_instance.add_to_item(player_id, TIME_INTERVAL * messages_to_add, "messages")

        if 10 <= players_instance.get_item(player_id, "messages") <= 10_000_000:
            ach = power_10(players_instance.get_item(player_id, "messages"))
            while ach >= 10:
                try:
                    players_instance.cache[player_id]["achievements"].append(
                        ACHIEVEMENTS_ID["messages"]["quantity{}".format(ach)]["id"]
                    )
                except KeyError as e:
                    pass
                ach //= 10
        if 10 <= players_instance.get_item_total(player_id, "messages") <= 10_000_000:
            ach = power_10(players_instance.get_item_total(player_id, "messages"))
            while ach >= 10:
                try:
                    players_instance.cache[player_id]["achievements"].append(
                        ACHIEVEMENTS_ID["messages"]["total{}".format(ach)]["id"]
                    )
                except KeyError as e:
                    pass
                ach //= 10

    if contacts_to_add > 0:
        players_instance.add_to_item(player_id, TIME_INTERVAL * contacts_to_add, "contacts")

        if 10 <= players_instance.get_item(player_id, "contacts") <= 10_000_000:
            ach = power_10(players_instance.get_item(player_id, "contacts"))
            while ach >= 10:
                try:
                    players_instance.cache[player_id]["achievements"].append(
                        ACHIEVEMENTS_ID["contacts"]["quantity{}".format(ach)]["id"]
                    )
                except KeyError as e:
                    pass
                ach //= 10
        if 10 <= players_instance.get_item_total(player_id, "contacts") <= 10_000_000:
            ach = power_10(players_instance.get_item_total(player_id, "contacts"))
            while ach >= 10:
                try:
                    players_instance.cache[player_id]["achievements"].append(
                        ACHIEVEMENTS_ID["contacts"]["total{}".format(ach)]["id"]
                    )
                except KeyError as e:
                    pass
                ach //= 10

    if messages_to_add > 0 or contacts_to_add > 0:
        players_instance.update(player_id, context)
