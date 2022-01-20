from telegram.ext import CallbackContext

from parameters import TIME_INTERVAL
from tlgtyper.achievements import ACHIEVEMENTS_ID
from tlgtyper.helpers import power_10


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def update_job(player_id: int, context: CallbackContext) -> None:
    try:
        remove_job_if_exists(str(player_id), context)
        context.job_queue.run_repeating(
            update_messages_and_contacts_from_job, TIME_INTERVAL, context=player_id, name=str(player_id)
        )
    except (IndexError, ValueError):
        return


def start_all_jobs(dispatcher, player_instance) -> None:
    for player in player_instance.Model.select():
        player_id = player.id
        # try:
        remove_job_if_exists(str(player_id), dispatcher)
        dispatcher.job_queue.run_repeating(
            update_messages_and_contacts_from_job, TIME_INTERVAL, context=(player_id, player_instance), name=str(player_id)
        )
        # except (IndexError, ValueError) as e:
        #     pass


def update_messages_and_contacts_from_job(context: CallbackContext) -> None:
    player_id, player_instance = context.job.context
    player, _ = player_instance.get_or_create(player_id)
    stats = player_instance.get_stats(player_id)

    messages_to_add = 0
    contacts_to_add = 0

    messages_to_add += player_instance.cache[player_id]["from_chat"]
    player_instance.cache[player_id]["from_chat"] = 0

    for item, attrs in stats.items():
        if "unlocked" in attrs and stats[item]["unlocked"]:
            messages_to_add += stats[item]["gain"]["messages"] * stats[item]["quantity"]
            contacts_to_add += stats[item]["gain"]["contacts"] * stats[item]["quantity"]

    messages_to_add = int(messages_to_add)
    contacts_to_add = int(contacts_to_add)

    if messages_to_add > 0 or contacts_to_add > 0:
        player.messages += TIME_INTERVAL * messages_to_add
        player.messages_total += TIME_INTERVAL * messages_to_add
        player.contacts += TIME_INTERVAL * contacts_to_add
        player.contacts_total += TIME_INTERVAL * contacts_to_add
        player.save()

        if 10 <= player.messages:
            ach = power_10(player.messages)
            while ach >= 10:
                player_instance.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["messages"]["quantity{}".format(ach)]["id"]
                )
                ach //= 10
        if 10 <= player.messages_total:
            ach = power_10(player.messages_total)
            while ach >= 10:
                player_instance.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["messages"]["total{}".format(ach)]["id"]
                )
                ach //= 10
        if 10 <= player.contacts:
            ach = power_10(player.contacts)
            while ach >= 10:
                player_instance.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["contacts"]["quantity{}".format(ach)]["id"]
                )
                ach //= 10
        if 10 <= player.contacts_total:
            ach = power_10(player.contacts_total)
            while ach >= 10:
                player_instance.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["contacts"]["total{}".format(ach)]["id"]
                )
                ach //= 10

        update_player(player_id, context)
