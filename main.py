#!/usr/bin/env python
# pylint: disable=C0116,W0613
import logging

from peewee import BigIntegerField, CharField, FloatField, IntegerField, Model, SqliteDatabase
from random import random, randint
from datetime import datetime, timedelta
from functools import wraps
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, ChatAction
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.error import BadRequest

from secret import BOT_TOKEN

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Database
main_db = SqliteDatabase("./main.db")

RESALE_PERCENTAGE = 0.77
TIME_INTERVAL = 1


class Players(Model):
    # Self
    id = BigIntegerField(unique=True)
    first_name = CharField(null=True)
    pinned_message = BigIntegerField(null=True)

    # Stats
    messages = FloatField(default=0)
    messages_total = FloatField(default=0)

    contacts = FloatField(default=0)
    contacts_state = IntegerField(default=0)
    contacts_total = FloatField(default=0)

    groups = FloatField(default=0)
    groups_state = IntegerField(default=0)
    groups_total = FloatField(default=0)

    channels = FloatField(default=0)
    channels_state = IntegerField(default=0)
    channels_total = FloatField(default=0)

    supergroups = FloatField(default=0)
    supergroups_state = IntegerField(default=0)
    supergroups_total = FloatField(default=0)

    class Meta:
        database = main_db


main_db.connect()
main_db.create_tables([Players])


def get_si(number, type="'", size=3):
    if number < 1:
        return "0"
    if type == "s":
        suf = {
            0: "",
            1: " k",
            2: " M",
            3: " G",
            4: " T",
            5: " P",
            6: " E",
            7: " Z",
            8: " Y",
            9: " A",
            10: " AA",
            11: " AAA",
            12: " stop",
        }
        exp = 0
        while number // 10 ** (exp * size):
            exp += 1
        exp -= 1
        return "{:.2f}".format(int(number / 10 ** (exp * size))).rstrip('0').rstrip('.') + "{}".format(suf[exp])
    elif type == "'":
        return "{:,}".format(int(number)).replace(",", "'")
    else:
        return number


def get_or_create_user(id: int):
    return Players.get_or_create(id=id)


def get_stats(id: int):
    user, _ = get_or_create_user(id)

    return {
        "messages": {
            "unlocked": True,
            "price": None,
            "quantity": user.messages,
            "total": user.messages_total,
        },
        "contacts": {
            "unlock_at": {"messages": 10},
            "unlocked": user.contacts_state,
            "price": {"messages": 10},
            "gain": {"messages": 0.02, "contacts": 0.00001},
            "quantity": user.contacts,
            "total": user.contacts_total,
        },
        "groups": {
            "unlock_at": {"messages": 100, "contacts": 4},
            "unlocked": user.groups_state,
            "price": {"messages": 100, "contacts": 4},
            "gain": {"messages": 0.2, "contacts": 0.0001},
            "quantity": user.groups,
            "total": user.groups_total,
        },
        "channels": {
            "unlock_at": {"messages": 1000, "contacts": 16},
            "unlocked": user.channels_state,
            "price": {"messages": 1000, "contacts": 16},
            "gain": {"messages": 2, "contacts": 0.001},
            "quantity": user.channels,
            "total": user.channels_total,
        },
        "supergroups": {
            "unlock_at": {"messages": 10000, "contacts": 256, "groups": 1},
            "unlocked": user.supergroups_state,
            "price": {"messages": 10000, "contacts": 256, "groups": 1},
            "gain": {"messages": 20, "contacts": 0.01},
            "quantity": user.supergroups,
            "total": user.supergroups_total,
        },
    }


def update_pinned_message(id: int, context: CallbackContext):
    user, _ = get_or_create_user(id)

    message = "– 💬 Messages: {}".format(get_si(user.messages))
    if user.contacts_state:
        message += "\n– 📇 Contacts: {}".format(get_si(user.contacts))
    if user.groups_state:
        message += "\n– 👥 Groups: {}".format(get_si(user.groups))
    if user.channels_state:
        message += "\n– 📰 Channels: {}".format(get_si(user.channels))
    if user.supergroups_state:
        message += "\n– 👥 Supergroups: {}".format(get_si(user.supergroups))

    try:
        context.bot.edit_message_text(message, user.id, user.pinned_message)
    except BadRequest:  # Not edit to be done
        return


def check_unlocks(id: int, context: CallbackContext):
    user, _ = get_or_create_user(id)
    stats = get_stats(id)

    for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
        if "unlock_at" in attrs and not stats[item]["unlocked"]:
            unlock = True
            for unlock_item, unlock_quantity in attrs["unlock_at"].items():  # e.g., "messages": 10
                if stats[unlock_item]["total"] < unlock_quantity:
                    unlock = False
                    break
            if unlock:
                exec("user.{}_state = 1".format(item))  # Worst thing I ever wrote probably, sorry not sorry.
                user.save()
                context.bot.send_message(user.id, "🏅 Unlocked {}!".format(item))


def pinned_and_achievements(id: int, context: CallbackContext):
    """
    Because I'm lazy.
    """
    update_pinned_message(id, context)
    check_unlocks(id, context)


def start(update: Update, context: CallbackContext) -> None:
    _user = update.effective_user
    user, created = get_or_create_user(_user.id)

    user.first_name = _user.first_name
    user.save()
    update.message.reply_text("Welcome, {}!".format(user.first_name))

    update.message.reply_text("== Placeholder for the tutorial ==")

    update.message.reply_text("You're ready to play!")

    update.message.reply_text(
        "Now, I am going to pin your counter to this conversation, so that you can see your progress!")
    counter = update.message.reply_text("Start talking to play!")
    user.pinned_message = counter.message_id
    user.save()

    try:
        context.bot.unpin_chat_message(update.message.chat.id)
    except:
        pass

    context.bot.pin_chat_message(update.message.chat.id, counter.message_id)

    update_job(_user.id, context)


def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def interface(update: Update, context: CallbackContext) -> None:
    _user = update.effective_user
    user, _ = get_or_create_user(_user.id)

    if update.callback_query and update.callback_query.data != "stop":  # Choices
        stats = get_stats(_user.id)
        query = update.callback_query
        query.answer()
        data = query.data

        # _C_ontacts
        if data[0] == "c":
            buy_price = stats["contacts"]["price"]["messages"]
            sell_price = int(buy_price * RESALE_PERCENTAGE)

            if data[1] == "b":  # Buy
                if data[2:] == "1":
                    user.messages -= buy_price
                    user.contacts += 1
                    user.contacts_total += 1
                elif data[2:] == "10":
                    user.messages -= 10 * buy_price
                    user.contacts += 10
                    user.contacts_total += 10
                else:
                    qt = user.messages // buy_price
                    user.messages -= buy_price * qt
                    user.contacts += qt
                    user.contacts_total += qt
                user.save()
                stats = get_stats(_user.id)
            elif data[1] == "s":  # Sell
                if data[2:] == "1":
                    user.messages += sell_price
                    user.messages_total += sell_price
                    user.contacts -= 1
                elif data[2:] == "10":
                    user.messages -= 10 * sell_price
                    user.messages_total += 10 * sell_price
                    user.contacts -= 10
                else:
                    qt = user.contacts * sell_price
                    user.messages += qt
                    user.messages_total += qt
                    user.contacts -= user.contacts
                user.save()
                stats = get_stats(_user.id)

            message = "**Contacts**\n" \
                      "You have {} Contacts.\n" \
                      "Find: -{} messages.\n" \
                      "Forfeit: +{} messages.".format(
                get_si(stats["contacts"]["quantity"]), get_si(buy_price), get_si(sell_price))

            # Select
            buy = []
            if stats["messages"]["quantity"] >= buy_price:
                buy.append(InlineKeyboardButton("Find 1 Contact", callback_data="cb1"))
                if stats["messages"]["quantity"] >= 10 * buy_price:
                    buy.append(InlineKeyboardButton("Find 10 Contacts", callback_data="cb10"))
                buy.append(InlineKeyboardButton("Find Max Contacts", callback_data="cbmax"))

            sell = []
            if stats["contacts"]["quantity"] >= 1:
                sell.append(InlineKeyboardButton("Forfeit 1 Contact", callback_data="cs1"))
                if stats["contacts"]["quantity"] >= 10:
                    sell.append(InlineKeyboardButton("Forfeit 10 Contacts", callback_data="cs10"))
                sell.append(InlineKeyboardButton("Forfeit All Contacts", callback_data="csmax"))

        # _G_roups
        elif data[0] == "g":
            buy_price = stats["groups"]["price"]
            sell_price = {k: int(v * RESALE_PERCENTAGE) for k, v in buy_price.items()}

            if data[1] == "b":  # Buy
                if data[2:] == "1":
                    user.messages -= buy_price["messages"]
                    user.contacts -= buy_price["contacts"]

                    user.groups += 1
                    user.groups_total += 1
                elif data[2:] == "10":
                    user.messages -= 10 * buy_price["messages"]
                    user.contacts -= 10 * buy_price["contacts"]

                    user.groups += 10
                    user.groups_total += 10
                else:
                    qt = min(user.messages // buy_price["messages"], user.contacts // buy_price["contacts"])
                    user.messages -= buy_price["messages"] * qt
                    user.contacts -= buy_price["contacts"] * qt

                    user.groups += qt
                    user.groups_total += qt
                user.save()
                stats = get_stats(_user.id)
            elif data[1] == "s":  # Sell
                if data[2:] == "1":
                    user.messages += sell_price["messages"]
                    user.messages_total += sell_price["messages"]
                    user.contacts += sell_price["contacts"]
                    user.contacts_total += sell_price["contacts"]

                    user.groups -= 1
                elif data[2:] == "10":
                    user.messages -= 10 * sell_price["messages"]
                    user.messages_total += 10 * sell_price["messages"]
                    user.contacts -= 10 * sell_price["contacts"]
                    user.contacts_total += 10 * sell_price["contacts"]

                    user.groups -= 10
                else:
                    qt_messages = user.groups * sell_price["messages"]
                    user.messages += qt_messages
                    user.messages_total += qt_messages
                    qt_contacts = user.groups * sell_price["contacts"]
                    user.contacts += qt_contacts
                    user.contacts_total += qt_contacts

                    user.groups -= user.groups
                user.save()
                stats = get_stats(_user.id)

            message = "**Groups**\n" \
                      "You have {} Groups.\n" \
                      "Join: -{} messages, -{} contacts.\n" \
                      "Leave: +{} messages, +{} contacts.".format(get_si(stats["groups"]["quantity"]),
                                                                  get_si(buy_price["messages"]), get_si(buy_price["contacts"]),
                                                                  get_si(sell_price["messages"]), get_si(sell_price["contacts"]))

            # Select
            buy = []
            if stats["messages"]["quantity"] >= buy_price["messages"] and stats["contacts"]["quantity"] >= buy_price[
                "contacts"]:
                buy.append(InlineKeyboardButton("Join 1 Group", callback_data="gb1"))
                if stats["messages"]["quantity"] >= 10 * buy_price["messages"] and stats["contacts"]["quantity"] >= 10 * \
                        buy_price["contacts"]:
                    buy.append(InlineKeyboardButton("Join 10 Groups", callback_data="gb10"))
                buy.append(InlineKeyboardButton("Join Max Groups", callback_data="gbmax"))

            sell = []
            if stats["groups"]["quantity"] >= 1:
                sell.append(InlineKeyboardButton("Leave 1 Group", callback_data="gs1"))
                if stats["groups"]["quantity"] >= 10:
                    sell.append(InlineKeyboardButton("Leave 10 Groups", callback_data="gs10"))
                sell.append(InlineKeyboardButton("Leave All Groups", callback_data="gsmax"))

        # C_h_annels
        elif data[0] == "h":
            buy_price = stats["channels"]["price"]
            sell_price = {k: int(v * RESALE_PERCENTAGE) for k, v in buy_price.items()}

            if data[1] == "b":  # Buy
                if data[2:] == "1":
                    user.messages -= buy_price["messages"]
                    user.contacts -= buy_price["contacts"]

                    user.channels += 1
                    user.channels_total += 1
                elif data[2:] == "10":
                    user.messages -= 10 * buy_price["messages"]
                    user.contacts -= 10 * buy_price["contacts"]

                    user.channels += 10
                    user.channels_total += 10
                else:
                    qt = min(user.messages // buy_price["messages"], user.contacts // buy_price["contacts"])
                    user.messages -= buy_price["messages"] * qt
                    user.contacts -= buy_price["contacts"] * qt

                    user.channels += qt
                    user.channels_total += qt
                user.save()
                stats = get_stats(_user.id)
            elif data[1] == "s":  # Sell
                if data[2:] == "1":
                    user.messages += sell_price["messages"]
                    user.messages_total += sell_price["messages"]
                    user.contacts += sell_price["contacts"]
                    user.contacts_total += sell_price["contacts"]

                    user.channels -= 1
                elif data[2:] == "10":
                    user.messages -= 10 * sell_price["messages"]
                    user.messages_total += 10 * sell_price["messages"]
                    user.contacts -= 10 * sell_price["contacts"]
                    user.contacts_total += 10 * sell_price["contacts"]

                    user.channels -= 10
                else:
                    qt_messages = user.channels * sell_price["messages"]
                    user.messages += qt_messages
                    user.messages_total += qt_messages
                    qt_contacts = user.channels * sell_price["contacts"]
                    user.contacts += qt_contacts
                    user.contacts_total += qt_contacts

                    user.channels -= user.channels
                user.save()
                stats = get_stats(_user.id)

            message = "**Channels**\n" \
                      "You have {} Channels.\n" \
                      "Join: -{} messages, -{} contacts.\n" \
                      "Leave: +{} messages, +{} contacts.".format(get_si(stats["channels"]["quantity"]),
                                                                  get_si(buy_price["messages"]),
                                                                  get_si(buy_price["contacts"]),
                                                                  get_si(sell_price["messages"]), get_si(sell_price["contacts"]))

            # Select
            buy = []
            if stats["messages"]["quantity"] >= buy_price["messages"] and stats["contacts"]["quantity"] >= buy_price[
                "contacts"]:
                buy.append(InlineKeyboardButton("Join 1 Channel", callback_data="hb1"))
                if stats["messages"]["quantity"] >= 10 * buy_price["messages"] and stats["contacts"]["quantity"] >= 10 * \
                        buy_price["contacts"]:
                    buy.append(InlineKeyboardButton("Join 10 Channels", callback_data="hb10"))
                buy.append(InlineKeyboardButton("Join Max Channels", callback_data="hbmax"))

            sell = []
            if stats["channels"]["quantity"] >= 1:
                sell.append(InlineKeyboardButton("Leave 1 Channel", callback_data="hs1"))
                if stats["channels"]["quantity"] >= 10:
                    sell.append(InlineKeyboardButton("Leave 10 Channels", callback_data="hs10"))
                sell.append(InlineKeyboardButton("Leave All Channels", callback_data="hsmax"))

        # _S_upergroups
        elif data[0] == "s":
            buy_price = stats["supergroups"]["price"]
            sell_price = {k: int(v * RESALE_PERCENTAGE) for k, v in buy_price.items()}

            if data[1] == "b":  # Buy
                if data[2:] == "1":
                    user.messages -= buy_price["messages"]
                    user.contacts -= buy_price["contacts"]
                    user.groups -= buy_price["groups"]

                    user.supergroups += 1
                    user.supergroups_total += 1
                elif data[2:] == "10":
                    user.messages -= 10 * buy_price["messages"]
                    user.contacts -= 10 * buy_price["contacts"]
                    user.groups -= 10 * buy_price["groups"]

                    user.supergroups += 10
                    user.supergroups_total += 10
                else:
                    qt = min(user.messages // buy_price["messages"], user.contacts // buy_price["contacts"],
                             user.groups // buy_price["groups"])
                    user.messages -= buy_price["messages"] * qt
                    user.contacts -= buy_price["contacts"] * qt
                    user.groups -= buy_price["groups"] * qt

                    user.supergroups += qt
                    user.supergroups_total += qt
                user.save()
                stats = get_stats(_user.id)
            elif data[1] == "s":  # Sell
                if data[2:] == "1":
                    user.messages += sell_price["messages"]
                    user.messages_total += sell_price["messages"]
                    user.contacts += sell_price["contacts"]
                    user.contacts_total += sell_price["contacts"]
                    user.groups += sell_price["groups"]
                    user.groups_total += sell_price["groups"]

                    user.supergroups -= 1
                elif data[2:] == "10":
                    user.messages -= 10 * sell_price["messages"]
                    user.messages_total += 10 * sell_price["messages"]
                    user.contacts -= 10 * sell_price["contacts"]
                    user.contacts_total += 10 * sell_price["contacts"]
                    user.groups -= 10 * sell_price["groups"]
                    user.groups_total += 10 * sell_price["groups"]

                    user.supergroups -= 10
                else:
                    qt_messages = user.supergroups * sell_price["messages"]
                    user.messages += qt_messages
                    user.messages_total += qt_messages
                    qt_contacts = user.supergroups * sell_price["contacts"]
                    user.contacts += qt_contacts
                    user.contacts_total += qt_contacts
                    qt_groups = user.supergroups * sell_price["groups"]
                    user.groups += qt_groups
                    user.groups_total += qt_groups

                    user.supergroups -= user.supergroups
                user.save()
                stats = get_stats(_user.id)

            message = "**Supergroups**\n" \
                      "You have {} Supergroups.\n" \
                      "Join: -{} messages, -{} contacts, -{} groups.\n" \
                      "Leave: +{} messages, +{} contacts, +{} groups.".format(get_si(stats["supergroups"]["quantity"]),
                                                                              get_si(buy_price["messages"]),
                                                                              get_si(buy_price["contacts"]),
                                                                              get_si(buy_price["groups"]),
                                                                              get_si(sell_price["messages"]),
                                                                              get_si(sell_price["contacts"]),
                                                                              get_si(sell_price["groups"]))

            # Select
            buy = []
            if stats["messages"]["quantity"] >= buy_price["messages"] and stats["contacts"]["quantity"] >= buy_price[
                "contacts"] and stats["groups"]["quantity"] >= buy_price[
                "groups"]:
                buy.append(InlineKeyboardButton("Join 1 Supergroup", callback_data="sb1"))
                if stats["messages"]["quantity"] >= 10 * buy_price["messages"] and stats["contacts"]["quantity"] >= 10 * \
                        buy_price["contacts"] and stats["groups"]["quantity"] >= 10 * \
                        buy_price["groups"]:
                    buy.append(InlineKeyboardButton("Join 10 Supergroups", callback_data="sb10"))
                buy.append(InlineKeyboardButton("Join Max Supergroups", callback_data="sbmax"))

            sell = []
            if stats["supergroups"]["quantity"] >= 1:
                sell.append(InlineKeyboardButton("Leave 1 Supergroup", callback_data="ss1"))
                if stats["supergroups"]["quantity"] >= 10:
                    sell.append(InlineKeyboardButton("Leave 10 Supergroups", callback_data="ss10"))
                sell.append(InlineKeyboardButton("Leave All Supergroups", callback_data="ssmax"))
        else:
            raise ValueError("Invalid argument: {}.".format(data))

        reply_markup = InlineKeyboardMarkup([buy, sell, [InlineKeyboardButton("Back", callback_data="stop")]])

        try:
            query.edit_message_text(message, reply_markup=reply_markup)
        except BadRequest:  # Not edit to be done
            pass

    else:  # Main
        stats = get_stats(_user.id)
        choices = []
        if stats["contacts"]["unlocked"]:
            choices.append(InlineKeyboardButton("Contacts", callback_data="cx"))
        if stats["groups"]["unlocked"]:
            choices.append(InlineKeyboardButton("Groups", callback_data="gx"))
        if stats["channels"]["unlocked"]:
            choices.append(InlineKeyboardButton("Channels", callback_data="hx"))
        if stats["supergroups"]["unlocked"]:
            choices.append(InlineKeyboardButton("Supergroups", callback_data="sx"))

        if choices:
            message = "**Interface**\n" \
                      "Select what you would like to bargain:"
            reply_markup = InlineKeyboardMarkup([choices])
        else:
            message = "You don't have enough messages for now..."
            reply_markup = None

        if update.callback_query:  # "stop"
            update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        else:
            update.message.reply_text(message, reply_markup=reply_markup)

    pinned_and_achievements(user.id, context)


def stop(update: Update, context: CallbackContext) -> None:
    Players.delete().where(Players.id == update.effective_user.id).execute()
    update.message.reply_text('Stop!')


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        sleep(len(update.effective_message.text) // 10)  # This is based on my max WPM hehe.
        return func(update, context,  *args, **kwargs)

    return command_func


@send_typing_action
def answer(update: Update, context: CallbackContext) -> None:
    context.bot.send_chat_action(chat_id=update.message.chat.id, action=ChatAction.TYPING)
    update.message.reply_text(update.message.text)

    _user = update.effective_user
    user, _ = get_or_create_user(_user.id)
    user.messages += 2
    user.messages_total += 2
    user.save()

    pinned_and_achievements(user.id, context)


def update_from_job(context: CallbackContext) -> None:
    id = context.job.context
    user, _ = get_or_create_user(id)
    stats = get_stats(id)

    messages_to_add = 0
    contacts_to_add = 0

    if stats["contacts"]["unlocked"]:
        messages_to_add += stats["contacts"]["gain"]["messages"] * stats["contacts"]["quantity"]
        contacts_to_add += stats["contacts"]["gain"]["contacts"] * stats["contacts"]["quantity"]
    if stats["groups"]["unlocked"]:
        messages_to_add += stats["groups"]["gain"]["messages"] * stats["groups"]["quantity"]
        contacts_to_add += stats["groups"]["gain"]["contacts"] * stats["groups"]["quantity"]
    if stats["channels"]["unlocked"]:
        messages_to_add += stats["channels"]["gain"]["messages"] * stats["channels"]["quantity"]
        contacts_to_add += stats["channels"]["gain"]["contacts"] * stats["channels"]["quantity"]
    if stats["supergroups"]["unlocked"]:
        messages_to_add += stats["supergroups"]["gain"]["messages"] * stats["supergroups"]["quantity"]
        contacts_to_add += stats["supergroups"]["gain"]["contacts"] * stats["supergroups"]["quantity"]

    user.messages += TIME_INTERVAL * messages_to_add
    user.messages_total += TIME_INTERVAL * messages_to_add
    user.contacts += TIME_INTERVAL * contacts_to_add
    user.contacts_total += TIME_INTERVAL * contacts_to_add
    user.save()

    pinned_and_achievements(id, context)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def update_job(id: int, context: CallbackContext) -> None:
    try:
        remove_job_if_exists(str(id), context)
        context.job_queue.run_repeating(update_from_job, TIME_INTERVAL, context=id, name=str(id))
    except (IndexError, ValueError):
        pass


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler(["interface", "buy", "sell", "join", "leave"], interface))
    updater.dispatcher.add_handler(CallbackQueryHandler(interface))
    dispatcher.add_handler(CommandHandler("stop", stop))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, answer))

    # Jobs go here

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    # Job
    updater.job_queue.run_once(alarm, 15, context="59804991", name=str(3))


if __name__ == '__main__':
    main()
