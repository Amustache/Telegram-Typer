#!/usr/bin/env python
# pylint: disable=C0116,W0613
import logging

from peewee import BigIntegerField, CharField, IntegerField, Model, SqliteDatabase

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from secret import BOT_TOKEN

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Database
main_db = SqliteDatabase("./main.db")


class Players(Model):
    # Self
    id = BigIntegerField(unique=True)
    first_name = CharField(null=True)

    # Stats
    messages = BigIntegerField(default=0)
    contacts = BigIntegerField(default=0)
    groups = BigIntegerField(default=0)
    channels = BigIntegerField(default=0)
    supergroups = BigIntegerField(default=0)

    # Game
    pinned_message = BigIntegerField(null=True)

    class Meta:
        database = main_db


main_db.connect()
main_db.create_tables([Players])


def get_or_create_user(id: int):
    return Players.get_or_create(id=id)


def update_pinned_message(id: int, context: CallbackContext):
    user, _ = get_or_create_user(id)

    if user.messages == 0:
        message = "Start talking to play!"
    else:
        message = "Messages: {}".format(user.messages)
        if user.contacts:
            message += ", Contacts: {}".format(user.contacts)
        if user.groups:
            message += "\n\nGroups: {}".format(user.groups)
        if user.channels:
            message += "\nChannels: {}".format(user.channels)
        if user.supergroups:
            message += "\nSupergroups: {}".format(user.supergroups)

    context.bot.edit_message_text(message, user.id, user.pinned_message)


def start(update: Update, context: CallbackContext) -> None:
    _user = update.effective_user
    user, created = get_or_create_user(_user.id)

    if created:
        user.first_name = _user.first_name
        user.save()
        update.message.reply_text("Welcome, {}!".format(user.first_name))
    else:
        update.message.reply_text("Welcome back, {}!".format(user.first_name))

    update.message.reply_text("== Placeholder for the tutorial ==")

    update.message.reply_text("You're ready to play!")

    update.message.reply_text("Now, I am going to pin your counter to this conversation, so that you can see your progress!")
    counter = update.message.reply_text("Start talking to play!")
    user.pinned_message = counter.message_id
    user.save()

    try:
        context.bot.unpin_chat_message(update.message.chat.id)
    except:
        pass

    context.bot.pin_chat_message(update.message.chat.id, counter.message_id)


def debug(update: Update, context: CallbackContext) -> None:
    _user = update.effective_user
    user, _ = get_or_create_user(_user.id)

    message = update.message.reply_text(
        "Fuck you already. You're {}, ID {}, and you have {} messages.".format(user.first_name, user.id, user.messages))
    user.pinned_message = message.message_id
    user.save()

    context.bot.unpin_chat_message(user.id)
    context.bot.pin_chat_message(user.id, message.message_id)


def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def interface(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Interface!')


def stop(update: Update, context: CallbackContext) -> None:
    Players.delete().where(Players.id == update.effective_user.id).execute()
    update.message.reply_text('Stop!')


def answer(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)

    _user = update.effective_user
    user, _ = get_or_create_user(_user.id)
    user.messages += 2
    user.save()

    update_pinned_message(user.id, context)


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("debug", debug))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("interface", interface))
    dispatcher.add_handler(CommandHandler("stop", stop))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, answer))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
