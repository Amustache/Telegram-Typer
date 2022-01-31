#!/usr/bin/env python
# pylint: disable=C0116,W0613
import datetime
import logging


from peewee import SqliteDatabase
from telegram.ext import Updater


from parameters import DB_PATH
from secret import BOT_TOKEN
from tlgtyper.handlers import AdminHandlers, PlayerAchievementsHandlers, PlayerHandlers, PlayerInterfaceHandlers
from tlgtyper.jobs import start_all_jobs
from tlgtyper.player import Players


# logging
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

fh = logging.FileHandler("./logs/log_{}.log".format(str(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))))
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        ch,
    ],
)

logger = logging.getLogger(__name__)
logger.addHandler(fh)

# Database
Players = Players(logger)

DB = SqliteDatabase(DB_PATH)
DB.bind([Players.Model])
DB.connect()
DB.create_tables([Players.Model])


def main() -> None:
    updater = Updater(BOT_TOKEN, request_kwargs={"read_timeout": 15, "connect_timeout": 15})
    dispatcher = updater.dispatcher

    # Commands
    PlayerHandlers(Players, logger, media_folder="./img").add_commands(dispatcher)
    PlayerInterfaceHandlers(Players, logger).add_commands(dispatcher)
    PlayerAchievementsHandlers(Players, logger).add_commands(dispatcher)
    AdminHandlers(Players, logger).add_commands(dispatcher)

    commands = ""
    for handler in dispatcher.handlers[0]:
        try:
            commands += "{}\n".format(
                "\n".join("{} - {}".format(command, handler.callback.__name__) for command in handler.command)
            )
        except AttributeError:
            continue
    print("{}\nList of commands\n{}\n{}".format("*" * 13, commands, "*" * 13))

    # Jobs
    start_all_jobs(dispatcher, Players)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
