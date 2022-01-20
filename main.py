#!/usr/bin/env python
# pylint: disable=C0116,W0613
import logging


from peewee import SqliteDatabase
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Updater


from parameters import DB_PATH, RESALE_PERCENTAGE
from secret import BOT_TOKEN
from tlgtyper.achievements import ACHIEVEMENTS_ID
from tlgtyper.cooldown import update_cooldown_and_notify
from tlgtyper.handlers import AdminHandlers, PlayerHandlers
from tlgtyper.helpers import get_si, power_10
from tlgtyper.jobs import start_all_jobs
from tlgtyper.player import Players
from tlgtyper.texts import get_quantities


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

Players = Players()

DB = SqliteDatabase(DB_PATH)
DB.bind([Players.Model])
DB.connect()
DB.create_tables([Players.Model])


def handler_interface(update: Update, context: CallbackContext) -> None:
    player_id = update.effective_user.id
    user, _ = Players.get_or_create(player_id)
    if update_cooldown_and_notify(player_id, Players, context):
        return

    if update.callback_query and update.callback_query.data != "stop":  # Choices
        stats = Players.get_stats(player_id)
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
                        stats = Players.get_stats(player_id)

                        if 10 <= stats[item]["quantity"]:
                            ach = power_10(stats[item]["quantity"])
                            while ach >= 10:
                                Players.cache[update.effective_user.id]["achievements"].append(
                                    ACHIEVEMENTS_ID[item]["quantity{}".format(ach)]["id"]
                                )
                                ach //= 10
                        if 10 <= stats[item]["total"]:
                            ach = power_10(stats[item]["total"])
                            while ach >= 10:
                                Players.cache[update.effective_user.id]["achievements"].append(
                                    ACHIEVEMENTS_ID[item]["total{}".format(ach)]["id"]
                                )
                                ach //= 10

                        update_player(player_id, context)
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
                        stats = Players.get_stats(player_id)

                        update_player(player_id, context)

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

        stats = Players.get_stats(player_id)
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
            message += get_quantities(player_id)
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


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Commands
    PlayerHandlers(Players, logger).add_commands(dispatcher)
    AdminHandlers(Players, logger).add_commands(dispatcher)

    dispatcher.add_handler(
        CommandHandler(["interface", "buy", "sell", "join", "leave"], handler_interface)
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(handler_interface))

    start_all_jobs(dispatcher, Players)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
