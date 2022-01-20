from telegram.ext import CallbackContext


def update_cooldown_and_notify(player_id: int, players_instance, context: CallbackContext) -> bool:
    set_cooldown(player_id, players_instance)
    retry_after = players_instance.cache[player_id]["cooldown"]["retry_after"]
    if retry_after:
        if not players_instance.cache[player_id]["cooldown"]["informed"]:
            context.bot.send_message(
                player_id,
                "Oops! I have been a bit spammy...\nI have to wait about {} second{} before we can play again!".format(
                    retry_after, "s" if retry_after > 1 else ""
                ),
            )
        return True
    else:
        return False


def set_cooldown(player_id: int, players_instance, COUNTER_LIMIT=100) -> None:
    if players_instance.cache[player_id]["cooldown"]["counter"] >= COUNTER_LIMIT:
        players_instance.cache[player_id]["cooldown"]["retry_after"] = 3
        players_instance.cache[player_id]["cooldown"]["counter"] = 0
    if players_instance.cache[player_id]["cooldown"]["retry_after"]:
        players_instance.cache[player_id]["cooldown"]["retry_after"] -= 1
    if players_instance.cache[player_id]["cooldown"]["retry_after"] < 0:
        players_instance.cache[player_id]["cooldown"]["retry_after"] = 0
