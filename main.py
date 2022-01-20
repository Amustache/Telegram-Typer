#!/usr/bin/env python
# pylint: disable=C0116,W0613
from collections import Counter, defaultdict
from datetime import datetime
from time import sleep
import logging

from peewee import BigIntegerField, CharField, FloatField, IntegerField, Model, SqliteDatabase
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

from achievements import ACHIEVEMENTS, ACHIEVEMENTS_ID, MAX_ACHIEVEMENTS
from parameters import DB_PATH, RESALE_PERCENTAGE, TIME_INTERVAL
from secret import ADMIN_CHAT, BOT_NAME, BOT_TOKEN
from tlgtyper.helpers import get_si, power_10, send_typing_action
from tlgtyper.player import PlayerInstance

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

Player = PlayerInstance()

logger = logging.getLogger(__name__)

# Database
DB = SqliteDatabase(DB_PATH)

DB.bind([Player.Model])
DB.connect()
DB.create_tables([Player.Model])


def get_player_stats(player_id: int) -> dict:
    user, _ = Player.get_or_create(player_id)

    return {
        "messages": {
            "quantity": user.messages,
            "total": user.messages_total,
        },
        "contacts": {
            "id": "c",
            "unlock_at": {"messages": 10},
            "unlocked": user.contacts_state,
            "price": {"messages": 10},
            "gain": {"messages": 0.02, "contacts": 0.00001},
            "quantity": user.contacts,
            "total": user.contacts_total,
        },
        "groups": {
            "id": "g",
            "unlock_at": {"messages": 100, "contacts": 4},
            "unlocked": user.groups_state,
            "price": {"messages": 100, "contacts": 4},
            "gain": {"messages": 0.2, "contacts": 0.0001},
            "quantity": user.groups,
            "total": user.groups_total,
        },
        "channels": {
            "id": "h",
            "unlock_at": {"messages": 1000, "contacts": 16},
            "unlocked": user.channels_state,
            "price": {"messages": 1000, "contacts": 16},
            "gain": {"messages": 2, "contacts": 0.001},
            "quantity": user.channels,
            "total": user.channels_total,
        },
        "supergroups": {
            "id": "s",
            "unlock_at": {"messages": 10000, "contacts": 256, "groups": 1},
            "unlocked": user.supergroups_state,
            "price": {"messages": 10000, "contacts": 256, "groups": 1},
            "gain": {"messages": 20, "contacts": 0.01},
            "quantity": user.supergroups,
            "total": user.supergroups_total,
        },
    }


def handler_stats(update: Update, context: CallbackContext) -> None:
    logger.info("{} requested the stats".format(update.effective_user.first_name))

    stats = get_player_stats(update.effective_user.id)
    message = "*📊 Stats 📊*\n_Stats of {} as of {}\._\n\n".format(
        update.effective_user.first_name, datetime.now().strftime("%B %d, %Y at %H:%M GMT\+1")
    )

    user_achievements = get_player_achievements(update.effective_user.id)
    medals = Counter(
        [medal for id, (medal, _, _) in sorted(ACHIEVEMENTS.items()) if id in user_achievements]
    )
    message += "*Achievements*\n"
    message += "– Unlocked {} achievements out of {}\.\n".format(
        sum(medals.values()), MAX_ACHIEVEMENTS
    )
    message += "– {}\n".format(
        ", ".join(["{} {}".format(qt, medal) for medal, qt in medals.items()])
    )
    message += "\n"

    message += "*{}*\n".format("Messages")
    message += "– {} current {}\.\n".format(get_si(stats["messages"]["quantity"]), "messages")
    message += "– {} {} in total\.\n".format(get_si(stats["messages"]["total"]), "messages")
    message += "\n"

    for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
        if "unlock_at" in attrs and stats[item]["unlocked"]:
            message += "*{}*\n".format(item.capitalize())
            message += "– {} current {}\.\n".format(get_si(attrs["quantity"]), item)
            message += "– {} {} in total\.\n".format(get_si(attrs["total"]), item)
            for currency, quantity in attrs["gain"].items():
                message += "– Add {} {} per second\.\n".format(
                    get_si(attrs["quantity"] * quantity, type="f"), currency
                )
            message += "\n"

    message += BOT_NAME

    update.message.reply_text(message, parse_mode="MarkdownV2")


def handler_start(update: Update, context: CallbackContext) -> None:
    logger.info("{} started the bot".format(update.effective_user.first_name))

    _user = update.effective_user
    update.message.reply_document(
        open("./img/typing.gif", "rb"), caption="👋 Welcome, {}!".format(_user.first_name)
    )

    update.message.reply_text("Press /new_game to play!")


def handler_new(update: Update, context: CallbackContext) -> None:
    logger.info("{} started a new game".format(update.effective_user.first_name))

    _user = update.effective_user
    user, created = Player.get_or_create(_user.id)

    if created:
        user.first_name = _user.first_name
        user.save()

        Player.cache[update.effective_user.id]["achievements"].append(
            ACHIEVEMENTS_ID["misc"]["start"]["id"]
        )

        update.message.reply_text("❕ You're ready to play!")

        update.message.reply_text(
            "Use /new_game to start a new game, or to reset a blocked counter.\nUse /interface to show the interface to buy/sell things.\nUse /achievements to show your achievements.\nUse /stats to get your stats to share with your friends.\nFinally, use /end to stop the game and delete your account."
        )

        update.message.reply_text(
            "Now, I am going to pin your counter to this conversation, so that you can see your progress!"
        )

    sleep(1)  # ... Fnck you.
    counter = update.message.reply_text(
        "Send a text (not a command!) to the bot to see this message update.\n(If the pinned message does not update, please do /new_game again.)"
    )
    user.pinned_message = counter.message_id
    user.save()
    try:
        context.bot.unpin_chat_message(update.message.chat.id)
    except:
        pass
    context.bot.pin_chat_message(update.message.chat.id, counter.message_id)
    update_job(_user.id, context)


def handler_help(update: Update, context: CallbackContext) -> None:
    logger.info("{} requested the help".format(update.effective_user.first_name))

    update.message.reply_text("Help!")  # TODO


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


def handler_stop(update: Update, context: CallbackContext) -> None:
    logger.info("{} deleted their account".format(update.effective_user.first_name))

    id = update.effective_user.id
    obj = Player.Model.get(Player.Model.id == id)
    obj.delete_instance()
    Player.Model.delete().where(Player.Model.id == id).execute()
    remove_job_if_exists(str(id), context)

    try:
        context.bot.unpin_chat_message(update.message.chat.id)
    except:
        pass

    update.message.reply_text("Game stopped, account deleted.")  # TODO


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


def handler_achievements(update: Update, context: CallbackContext) -> None:
    logger.info("{} requested the achievements".format(update.effective_user.first_name))

    user_achievements = get_player_achievements(update.effective_user.id)
    question = "❔"

    if context.args:
        try:
            value = int(context.args[0], 16)
            if value < 0 or value > 0xFF:
                raise ValueError
        except ValueError:
            update.message.reply_text("Usage: `/achievement` or `/achievement number`")
            return

        try:
            medal, title, text = ACHIEVEMENTS[value]
        except ValueError:
            update.message.reply_text("Wrong achievement number.")
            return

        if not value in user_achievements:
            medal = question
            text = "\[You don't have this achievement just yet\.\.\.\]"
        message = "*{} {} {}*\n_{}_".format(medal, title, medal, text)
        update.message.reply_text(message, parse_mode="MarkdownV2")
    else:
        things = [
            "{:02X}: {}".format(id, medal if id in user_achievements else question)
            for id, (medal, _, _) in sorted(ACHIEVEMENTS.items())
        ]
        things = [things[i: i + 5] for i in range(0, len(things), 5)]
        message = "*🌟 Achievements 🌟*\n\n"
        message += "\n".join([", ".join(text) for text in things])
        message += "\n\nUse `/achievement number` to have more information\."

        update.message.reply_text(message, parse_mode="MarkdownV2")


def update_player(player_id: int, context: CallbackContext) -> None:
    set_cooldown(player_id)
    set_unlocks(player_id)
    update_pinned_message(player_id, context)
    update_achievements(player_id, context)


@send_typing_action
def handler_answer(update: Update, context: CallbackContext) -> None:
    id = update.effective_user.id
    if update_cooldown_and_notify(id, context):
        return

    try:
        update.message.reply_text(update.message.text)  # TODO
        if update.message.text == "J'aime les loutres":
            Player.cache[update.effective_user.id]["achievements"].append(
                ACHIEVEMENTS_ID["misc"]["loutres"]["id"]
            )
        Player.cache[update.effective_user.id]["from_chat"] += 2
        Player.cache[id]["cooldown"]["counter"] += 1
    except RetryAfter as e:
        logger.error(str(e))
        retryafter = int(e.split("in ")[1].split(".0")[0])
        Player.cache[id]["cooldown"]["retryafter"] = retryafter


def handler_quickmode(update: Update, context: CallbackContext) -> None:
    kb = [
        [KeyboardButton("Blablabla")],
    ]
    kb_markup = ReplyKeyboardMarkup(kb)
    update.message.reply_text(
        "Simply press the big keyboard button to use quickmode!", reply_markup=kb_markup
    )


def update_messages_and_contacts_from_job(context: CallbackContext) -> None:
    player_id = context.job.context
    user, _ = Player.get_or_create(player_id)
    stats = get_player_stats(player_id)

    messages_to_add = 0
    contacts_to_add = 0

    messages_to_add += Player.cache[player_id]["from_chat"]
    Player.cache[player_id]["from_chat"] = 0

    for item, attrs in stats.items():
        if "unlocked" in attrs and stats[item]["unlocked"]:
            messages_to_add += stats[item]["gain"]["messages"] * stats[item]["quantity"]
            contacts_to_add += stats[item]["gain"]["contacts"] * stats[item]["quantity"]

    messages_to_add = int(messages_to_add)
    contacts_to_add = int(contacts_to_add)

    if messages_to_add > 0 or contacts_to_add > 0:
        user.messages += TIME_INTERVAL * messages_to_add
        user.messages_total += TIME_INTERVAL * messages_to_add
        user.contacts += TIME_INTERVAL * contacts_to_add
        user.contacts_total += TIME_INTERVAL * contacts_to_add
        user.save()

        if 10 <= user.messages:
            ach = power_10(user.messages)
            while ach >= 10:
                Player.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["messages"]["quantity{}".format(ach)]["id"]
                )
                ach //= 10
        if 10 <= user.messages_total:
            ach = power_10(user.messages_total)
            while ach >= 10:
                Player.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["messages"]["total{}".format(ach)]["id"]
                )
                ach //= 10
        if 10 <= user.contacts:
            ach = power_10(user.contacts)
            while ach >= 10:
                Player.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["contacts"]["quantity{}".format(ach)]["id"]
                )
                ach //= 10
        if 10 <= user.contacts_total:
            ach = power_10(user.contacts_total)
            while ach >= 10:
                Player.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["contacts"]["total{}".format(ach)]["id"]
                )
                ach //= 10

        update_player(player_id, context)


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


def start_all_jobs(dispatcher) -> None:
    for user in Player.Model.select():
        id = user.id
        try:
            remove_job_if_exists(str(id), dispatcher)
            dispatcher.job_queue.run_repeating(
                update_messages_and_contacts_from_job, TIME_INTERVAL, context=id, name=str(id)
            )
        except (IndexError, ValueError):
            pass

from tlgtyper.handlers import AdminHandlers


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Commands
    AdminHandlers(Player, logger).add_commands(dispatcher)

    dispatcher.add_handler(CommandHandler("start", handler_start))
    dispatcher.add_handler(CommandHandler(["new_game", "new"], handler_new))
    dispatcher.add_handler(CommandHandler("help", handler_help))
    dispatcher.add_handler(
        CommandHandler(["interface", "buy", "sell", "join", "leave"], handler_interface)
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(handler_interface))
    dispatcher.add_handler(CommandHandler(["achievements", "achievement"], handler_achievements))
    dispatcher.add_handler(CommandHandler(["stats", "stat"], handler_stats))
    dispatcher.add_handler(CommandHandler(["stop", "end", "end_game"], handler_stop))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handler_answer))
    dispatcher.add_handler(CommandHandler("quickmode", handler_quickmode))


    start_all_jobs(dispatcher)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
