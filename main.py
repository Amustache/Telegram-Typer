#!/usr/bin/env python
# pylint: disable=C0116,W0613
from collections import Counter, defaultdict
from datetime import datetime
from time import sleep
import logging

from peewee import SqliteDatabase
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

from tlgtyper.achievements import ACHIEVEMENTS, ACHIEVEMENTS_ID, MAX_ACHIEVEMENTS
from parameters import DB_PATH, RESALE_PERCENTAGE, TIME_INTERVAL
from secret import ADMIN_CHAT, BOT_NAME, BOT_TOKEN
from tlgtyper.helpers import get_si, power_10, send_typing_action
from tlgtyper.player import PlayerInstance
from tlgtyper.handlers import AdminHandlers, PlayerHandlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

Player = PlayerInstance()

DB = SqliteDatabase(DB_PATH)
DB.bind([Player.Model])
DB.connect()
DB.create_tables([Player.Model])


def handler_interface(update: Update, context: CallbackContext) -> None:
    id = update.effective_user.id
    user, _ = Player.get_or_create(id)
    if update_cooldown_and_notify(id, context):
        return

    if update.callback_query and update.callback_query.data != "stop":  # Choices
        stats = get_player_stats(id)
        query = update.callback_query
        query.answer()
        data = query.data

        for item, attrs in stats.items():
            if "id" in attrs:
                if data[0] == attrs["id"]:
                    buy_price = stats[item]["price"]
                    sell_price = {k: int(v * RESALE_PERCENTAGE) for k, v in buy_price.items()}

                    if data[1] == "b":  # Buy
                        if data[2:] == "1":
                            qt = 1
                        elif data[2:] == "10":
                            qt = 10
                        else:
                            qt = 999_999_999_999_999
                            for currency, quantity in buy_price.items():
                                qt = min(qt, eval("user.{} // quantity".format(currency)))
                        for currency, quantity in buy_price.items():
                            exec("user.{} -= qt * quantity".format(currency))
                        exec("user.{} += qt".format(item))
                        exec("user.{}_total += qt".format(item))
                        user.save()
                        stats = get_player_stats(id)

                        if 10 <= stats[item]["quantity"]:
                            ach = power_10(stats[item]["quantity"])
                            while ach >= 10:
                                Player.cache[update.effective_user.id]["achievements"].append(
                                    ACHIEVEMENTS_ID[item]["quantity{}".format(ach)]["id"]
                                )
                                ach //= 10
                        if 10 <= stats[item]["total"]:
                            ach = power_10(stats[item]["total"])
                            while ach >= 10:
                                Player.cache[update.effective_user.id]["achievements"].append(
                                    ACHIEVEMENTS_ID[item]["total{}".format(ach)]["id"]
                                )
                                ach //= 10

                        update_player(id, context)
                    elif data[1] == "s":  # Sell
                        if data[2:] == "1":
                            qt = 1
                        elif data[2:] == "10":
                            qt = 10
                        else:
                            qt = eval("user.{}".format(item))
                        for currency, quantity in sell_price.items():
                            exec("user.{} += qt * quantity".format(currency))
                            exec("user.{}_total += qt * quantity".format(currency))
                        exec("user.{} -= qt".format(item))
                        user.save()
                        stats = get_player_stats(id)

                        update_player(id, context)

                    message = "*🧮 Interface 🧮*\n\n*{}*\n".format(item.capitalize())
                    message += "You have {} {}\.\n".format(get_si(stats[item]["quantity"]), item)
                    message += "📈 Join:"
                    for currency, quantity in buy_price.items():
                        message += " –{} {} ".format(quantity, currency)
                    message += "\n"
                    message += "📉 Leave:"
                    for currency, quantity in sell_price.items():
                        message += " \+{} {} ".format(quantity, currency)

                    # Select
                    buy = []
                    can_buy = 999_999_999_999_999
                    for currency, quantity in buy_price.items():
                        can_buy = min(can_buy, stats[currency]["quantity"] // quantity)
                    if can_buy >= 1:
                        buy.append(
                            InlineKeyboardButton(
                                "📈 Join 1 {}".format(item), callback_data="{}b1".format(attrs["id"])
                            )
                        )
                        if can_buy >= 10:
                            buy.append(
                                InlineKeyboardButton(
                                    "📈 Join 10 {}".format(item),
                                    callback_data="{}b10".format(attrs["id"]),
                                )
                            )
                        buy.append(
                            InlineKeyboardButton(
                                "📈 Join Max {}".format(item),
                                callback_data="{}bmax".format(attrs["id"]),
                            )
                        )

                    sell = []
                    if stats[item]["quantity"] >= 1:
                        sell.append(
                            InlineKeyboardButton(
                                "📉 Leave 1 {}".format(item),
                                callback_data="{}s1".format(attrs["id"]),
                            )
                        )
                        if stats[item]["quantity"] >= 10:
                            sell.append(
                                InlineKeyboardButton(
                                    "📉 Leave 10 {}".format(item),
                                    callback_data="{}s10".format(attrs["id"]),
                                )
                            )
                        sell.append(
                            InlineKeyboardButton(
                                "📉 Leave All {}".format(item),
                                callback_data="{}smax".format(attrs["id"]),
                            )
                        )

                    break

        reply_markup = InlineKeyboardMarkup(
            [buy, sell, [InlineKeyboardButton("Back", callback_data="stop")]]
        )

        try:
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")
        except BadRequest:  # Not edit to be done
            pass

    else:  # Main
        logger.info("{} requested the interface".format(update.effective_user.first_name))

        stats = get_player_stats(id)
        choices = []
        for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
            if "unlock_at" in attrs and stats[item]["unlocked"]:
                choices.append(
                    InlineKeyboardButton(
                        item.capitalize(), callback_data="{}x".format(stats[item]["id"])
                    )
                )

        if choices:
            message = "*🧮 Interface 🧮*\n\n"
            message += get_quantities(id)
            message += "\n\nSelect what you would like to bargain:"
            reply_markup = InlineKeyboardMarkup([choices])
        else:
            message = "*Interface*\n\nYou don't have enough messages for now\.\.\."
            reply_markup = None

        if update.callback_query:  # "stop"
            update.callback_query.edit_message_text(
                message, reply_markup=reply_markup, parse_mode="MarkdownV2"
            )
        else:
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")


def update_cooldown_and_notify(player_id: int, context: CallbackContext) -> bool:
    set_cooldown(player_id)
    retryafter = Player.cache[player_id]["cooldown"]["retryafter"]
    if retryafter:
        if not Player.cache[player_id]["cooldown"]["informed"]:
            context.bot.send_message(
                player_id,
                "Oops! I have been a bit spammy...\nI have to wait about {} second{} before we can play again!".format(
                    retryafter, "s" if retryafter > 1 else ""
                ),
            )
        return True
    else:
        return False


def set_cooldown(player_id: int, COUNTER_LIMIT=100) -> None:
    if Player.cache[player_id]["cooldown"]["counter"] >= COUNTER_LIMIT:
        Player.cache[player_id]["cooldown"]["retryafter"] = 3
        Player.cache[player_id]["cooldown"]["counter"] = 0
    if Player.cache[player_id]["cooldown"]["retryafter"]:
        Player.cache[player_id]["cooldown"]["retryafter"] -= 1
    if Player.cache[player_id]["cooldown"]["retryafter"] < 0:
        Player.cache[player_id]["cooldown"]["retryafter"] = 0


def set_unlocks(player_id: int) -> None:
    user, _ = Player.get_or_create(player_id)
    stats = get_player_stats(player_id)

    for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
        if "unlock_at" in attrs and not stats[item]["unlocked"]:
            unlock = True
            for unlock_item, unlock_quantity in attrs["unlock_at"].items():  # e.g., "messages": 10
                if stats[unlock_item]["total"] < unlock_quantity:
                    unlock = False
                    break
            if unlock:
                # Worst thing I ever wrote probably, sorry not sorry.
                exec("user.{}_state = 1".format(item))
                user.save()
                Player.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID[item]["unlocked"]["id"])


def get_quantities(player_id: int) -> str:
    user, _ = Player.get_or_create(player_id)
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


def update_pinned_message(player_id: int, context: CallbackContext) -> None:
    user, _ = Player.get_or_create(player_id)
    if update_cooldown_and_notify(player_id, context):
        return

    message = get_quantities(player_id)

    try:
        context.bot.edit_message_text(message, player_id, user.pinned_message)
    except RetryAfter as e:
        logger.error(str(e))
        retryafter = int(str(e).split("in ")[1].split(".0")[0])
        Player.cache[player_id]["cooldown"]["retryafter"] = retryafter
    except BadRequest as e:  # Edit problem
        context.bot.send_message(
            player_id,
            "Oops\! It seems like I did not find the pinned message\. Could you use /new\_game again, please\?",
            parse_mode="MarkdownV2",
        )
        logger.error(str(e))
        remove_job_if_exists(str(player_id), context)


def get_player_achievements(player_id: int) -> list:
    user, _ = Player.get_or_create(player_id)
    return [int(num) for num in user.achievements.split(",") if num]


def update_achievements(player_id: int, context: CallbackContext) -> None:
    user, _ = Player.get_or_create(player_id)
    user_achievements = get_player_achievements(player_id)
    data = list(set(Player.cache[player_id]["achievements"]))
    Player.cache[player_id]["achievements"] = []
    user.achievements = ",".join([str(num) for num in list(set(user_achievements + data))])
    user.save()

    for achievement in data:
        if achievement not in user_achievements:
            medal, title, text = ACHIEVEMENTS[achievement]
            message = "*{} {} {}*\n_{}_".format(medal, title, medal, text)
            context.bot.send_message(player_id, message, parse_mode="MarkdownV2")


def update_player(player_id: int, context: CallbackContext) -> None:
    set_cooldown(player_id)
    set_unlocks(player_id)
    update_pinned_message(player_id, context)
    update_achievements(player_id, context)


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Commands
    PlayerHandlers(Player, logger).add_commands(dispatcher)
    AdminHandlers(Player, logger).add_commands(dispatcher)

    dispatcher.add_handler(
        CommandHandler(["interface", "buy", "sell", "join", "leave"], handler_interface)
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(handler_interface))

    start_all_jobs(dispatcher)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
