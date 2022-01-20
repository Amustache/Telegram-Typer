"""
Handlers for the bot.
"""
import os

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler

from secret import ADMIN_CHAT


class BaseHandlers:
    """
    Base class to add new features in the bot.
    """

    def __init__(self, command_handlers, player_instance=None, logger=None, media_folder=None):
        """
        :param logger: logging.getLogger, when using a logger.
        :param command_handlers: [telegram.ext.CommandHandler], for command handling.
        :param table: peewee.ModelBase, when using a table in the bot's database.
        """
        self.command_handlers = command_handlers
        self.player_instance = player_instance
        self.logger = logger
        self.media_folder = media_folder

    def _media(self, filename=""):
        if self.media_folder:
            return os.path.join(self.media_folder, filename)

    def add_commands(self, dispatcher):
        """
        Add all self.commandhandlers to the provided dispatcher.
        :param dispatcher: telegram.ext.Dispatcher
        """
        for command_handler in self.command_handlers:
            dispatcher.add_handler(command_handler)

    def get_commands(self):
        """
        :return: Aliases and commands in text format.
        """
        commands = ""
        for handler in self.command_handlers:
            try:
                commands += "- {} => {};\n".format(
                    ", ".join(handler.command), handler.callback.__name__
                )
            except:
                continue

    def get_commands_botfather(self):
        """
        :return: Aliases and commands but formatted for botfather.
        """
        commands = ""
        for handler in self.command_handlers:
            try:
                commands += [
                    "{} - {}\n".format(command, handler.callback.__name__)
                    for command in handler.command
                ]
            except:
                continue


class PlayerHandlers(BaseHandlers):
    def __init__(self, player_instance=None, logger=None, media_folder=None):
        command_handlers = [
            CommandHandler([""], self.XXX),
        ]
        super().__init__(command_handlers=command_handlers, player_instance=player_instance, logger=logger,
                         media_folder=media_folder)


class AdminHandlers(BaseHandlers):
    def __init__(self, player_instance=None, logger=None, media_folder=None):
        command_handlers = [
            CommandHandler(["debug", "cheat", "rich"], self.be_rich),
            CommandHandler(["notify"], self.notify_all),
            CallbackQueryHandler(self.notify_all),
        ]
        super().__init__(command_handlers=command_handlers, player_instance=player_instance, logger=logger,
                         media_folder=media_folder)

    def be_rich(self, update: Update, context: CallbackContext) -> None:
        player_id = update.effective_user.id
        if player_id == 59804991:
            player, _ = self.player_instance.get_or_create(player_id)
            player.messages += 10_000_000_000
            player.messages_total += 10_000_000_000
            player.save()
        update.message.reply_text("Sent 10\_000\_000\_000 messages\.", parse_mode="MarkdownV2")

    def notify_all(self, update: Update, context: CallbackContext) -> None:
        if update.effective_user.id == 59804991:  # ADMIN_CHAT:
            if update.message.reply_to_message:
                self.logger.info("{} sent a global message.".format(update.effective_user.first_name))
                for player in self.player_instance.Model.select():
                    context.bot.send_message(player.id, update.message.reply_to_message.text)
            else:
                text_to_send = "🗣 Message from admin 🗣\n{}".format(
                    update.effective_message.text.split(" ", 1)[1]
                )
                update.message.reply_text("This is a preview:").reply_text(text_to_send).reply_text(
                    "Reply /notify to the previous message to send it."
                )
