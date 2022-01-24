from telegram.ext import CallbackContext


from tlgtyper.jobs import remove_job_if_exists, update_job


def update_cooldown_and_notify(player_id: int, players_instance, context: CallbackContext) -> bool:
    set_cooldown(player_id, players_instance)
    retry_after = players_instance.cache[player_id]["cooldown"]["retry_after"]
    if retry_after:
        remove_job_if_exists(str(player_id), context)
        if not players_instance.cache[player_id]["cooldown"]["informed"]:
            players_instance.cache[player_id]["cooldown"]["informed"] = True
            context.bot.send_message(
                player_id,
                "Oops! I have been a bit spammy...\n"
                "I have to wait about {} second{} before we can play again!".format(
                    retry_after, "s" if retry_after > 1 else ""
                ),
            )
        return True
    else:
        if players_instance.cache[player_id]["cooldown"]["informed"]:
            players_instance.cache[player_id]["cooldown"]["informed"] = False
            update_job(player_id, context, players_instance)
        return False


def set_cooldown(player_id: int, players_instance, COUNTER_LIMIT=1000) -> None:
    if players_instance.cache[player_id]["cooldown"]["counter"] >= COUNTER_LIMIT:
        players_instance.cache[player_id]["cooldown"]["retry_after"] = 3
        players_instance.cache[player_id]["cooldown"]["counter"] = 0
    if players_instance.cache[player_id]["cooldown"]["retry_after"]:
        players_instance.cache[player_id]["cooldown"]["retry_after"] -= 1
    if players_instance.cache[player_id]["cooldown"]["retry_after"] < 0:
        players_instance.cache[player_id]["cooldown"]["retry_after"] = 0
