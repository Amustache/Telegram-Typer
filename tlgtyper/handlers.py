"""
Handlers for the bot.
"""
from collections import Counter
from datetime import datetime
import os


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Filters, MessageHandler


from parameters import CAP, RESALE_PERCENTAGE
from secret import ADMIN_CHAT, BOT_LINK
from tlgtyper.achievements import ACHIEVEMENTS, ACHIEVEMENTS_ID, MAX_ACHIEVEMENTS
from tlgtyper.cooldown import update_cooldown_and_notify
from tlgtyper.helpers import get_si, power_10, send_typing_action
from tlgtyper.items import get_max_to_buy, get_price_for_n
from tlgtyper.jobs import remove_job_if_exists, update_job
from tlgtyper.texts import get_quantities, HELP_COMMANDS


class BaseHandlers:
    """
    Base class to add new features in the bot.
    """

    def __init__(self, command_handlers, players_instance, logger=None, media_folder=None):
        """
        :param logger: logging.getLogger, when using a logger.
        :param command_handlers: [telegram.ext.CommandHandler], for command handling.
        :param table: peewee.ModelBase, when using a table in the bot's database.
        """
        self.command_handlers = command_handlers
        self.players_instance = players_instance
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
        return commands

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
        return commands


class PlayerHandlers(BaseHandlers):
    def __init__(self, players_instance, logger=None, media_folder=None):
        command_handlers = [
            CommandHandler(["start"], self.start_bot),
            CommandHandler(["new_game", "new", "reset_game", "reset"], self.new_game),
            MessageHandler(Filters.text & ~Filters.command, self.answer),
            CommandHandler(["help", "commands"], self.help_commands),
            CommandHandler(["quickmode", "quick", "quickmessage"], self.quickmode),
            CommandHandler(["stop", "stop_game", "end", "end_game"], self.stop_bot),
            CommandHandler(["achievements", "achievement"], self.show_achievements),
            CommandHandler(["stats", "stat"], self.show_stats),
            CommandHandler(["interface", "buy", "sell", "join", "leave"], self.interface),
            CallbackQueryHandler(self.interface),
        ]
        super().__init__(
            command_handlers=command_handlers,
            players_instance=players_instance,
            logger=logger,
            media_folder=media_folder,
        )

    def start_bot(self, update: Update, context: CallbackContext):
        user = update.effective_user

        with open(self._media("typing.gif"), "rb") as gif:
            update.message.reply_document(
                gif, caption="👋 Welcome, {}!".format(user.first_name)
            ).reply_text("Press /new_game to play!")

        self.logger.info("{} started the bot".format(user.first_name))

    def new_game(self, update: Update, context: CallbackContext):
        user = update.effective_user
        player_id = user.id
        player, created = self.players_instance.get_or_create(player_id)

        if created:
            player.first_name = user.first_name

            self.players_instance.cache[player_id]["achievements"].append(
                ACHIEVEMENTS_ID["misc"]["start"]["id"]
            )

            update.message.reply_text("❕ You're ready to play!")

            update.message.reply_text(HELP_COMMANDS)

            update.message.reply_text(
                "Now, I am going to pin your counter to this conversation, so that you can see your progress!"
            )
            self.logger.info("{} started a new game".format(user.first_name))
        else:
            self.logger.info("{} did a reset".format(user.first_name))

        counter = update.message.reply_text(
            "Send a text (not a command!) to the bot to see this message update.\n"
            "(If the pinned message does not update, please do /new_game again.)"
        )
        player.pinned_message = counter.message_id
        player.save()

        try:
            context.bot.unpin_chat_message(update.message.chat.id)
        except:
            pass

        context.bot.pin_chat_message(update.message.chat.id, counter.message_id)
        update_job(player_id, context, self.players_instance)

    # @send_typing_action
    def answer(self, update: Update, context: CallbackContext):
        user = update.effective_user
        player_id = user.id

        if update_cooldown_and_notify(player_id, self.players_instance, context):
            return

        try:
            update.message.reply_text(update.message.text)  # TODO
            if update.message.text == "J'aime les loutres":
                self.players_instance.cache[player_id]["achievements"].append(
                    ACHIEVEMENTS_ID["misc"]["loutres"]["id"]
                )
            self.players_instance.cache[player_id]["from_chat"] += 2
            self.players_instance.cache[player_id]["cooldown"]["counter"] += 1
        except RetryAfter as e:
            self.logger.error(str(e))
            retry_after = int(str(e).split("in ")[1].split(".0")[0])
            self.players_instance.cache[player_id]["cooldown"]["retry_after"] = retry_after

    def help_commands(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        update.message.reply_text(HELP_COMMANDS)  # TODO
        self.logger.info("{} requested help".format(user.first_name))

    def quickmode(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        kb_markup = ReplyKeyboardMarkup([[KeyboardButton("Blablabla")]])
        update.message.reply_text(
            "Simply press the big keyboard button to use quickmode!", reply_markup=kb_markup
        )
        self.logger.info("{} requested quickmode".format(user.first_name))

    def stop_bot(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        player_id = user.id

        obj = self.players_instance.Model.get(self.players_instance.Model.id == player_id)
        obj.delete_instance()
        self.players_instance.Model.delete().where(
            self.players_instance.Model.id == player_id
        ).execute()
        remove_job_if_exists(str(player_id), context)

        try:
            context.bot.unpin_chat_message(update.message.chat.id)
        except:
            pass

        update.message.reply_text("Game stopped, account deleted.")  # TODO
        self.logger.info("{} stopped the bot".format(user.first_name))

    def show_stats(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        player_id = user.id

        stats = self.players_instance.get_stats(player_id)
        message = "*📊 Stats 📊*\n_Stats of {} as of {}\._\n\n".format(
            update.effective_user.first_name, datetime.now().strftime("%B %d, %Y at %H:%M GMT\+1")
        )

        user_achievements = self.players_instance.get_achievements(player_id)
        medals = Counter(
            [
                medal
                for achievement_id, (medal, _, _) in sorted(ACHIEVEMENTS.items())
                if achievement_id in user_achievements
            ]
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

        message += BOT_LINK

        update.message.reply_text(message, parse_mode="MarkdownV2")
        self.logger.info("{} requested stats".format(update.effective_user.first_name))

    def show_achievements(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        player_id = user.id

        user_achievements = self.players_instance.get_achievements(player_id)
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
            except (KeyError, ValueError):
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
            things = [things[i : i + 5] for i in range(0, len(things), 5)]
            message = "*🌟 Achievements 🌟*\n\n"
            message += "\n".join([", ".join(text) for text in things])
            message += "\n\nUse `/achievement number` to have more information\."

            update.message.reply_text(message, parse_mode="MarkdownV2")
        self.logger.info("{} requested achievements".format(update.effective_user.first_name))

    def interface(self, update: Update, context: CallbackContext):
        player_id = update.effective_user.id
        player, _ = self.players_instance.get_or_create(player_id)
        if update_cooldown_and_notify(player_id, self.players_instance, context):
            return

        # The choice has been made
        if update.callback_query and update.callback_query.data != "stop":  # Choices
            stats = self.players_instance.get_stats(player_id)
            query = update.callback_query
            query.answer()
            data = query.data

            for item, attrs in stats.items():
                if "id" in attrs:
                    if data[0] == attrs["id"]:
                        base_prices = stats[item]["base_price"]
                        sell_price = {
                            currency: int(price * RESALE_PERCENTAGE)
                            for currency, price in base_prices.items()
                        }

                        # Buy
                        if data[1] == "b":
                            if data[2:] == "1":
                                qt = 1
                            elif data[2:] == "10":
                                qt = 10
                            else:
                                qt = int(data[2:])
                            for currency, price in base_prices.items():
                                loss = get_price_for_n(price, stats[item]["quantity"], qt)
                                exec("player.{} -= loss".format(currency))
                            exec("player.{} += qt".format(item))
                            exec("player.{}_total += qt".format(item))
                            player.save()
                            stats = self.players_instance.get_stats(player_id)

                            if 10 <= stats[item]["quantity"]:
                                ach = power_10(stats[item]["quantity"])
                                while ach >= 10:
                                    self.players_instance.cache[update.effective_user.id][
                                        "achievements"
                                    ].append(ACHIEVEMENTS_ID[item]["quantity{}".format(ach)]["id"])
                                    ach //= 10
                            if 10 <= stats[item]["total"]:
                                ach = power_10(stats[item]["total"])
                                while ach >= 10:
                                    self.players_instance.cache[update.effective_user.id][
                                        "achievements"
                                    ].append(ACHIEVEMENTS_ID[item]["total{}".format(ach)]["id"])
                                    ach //= 10

                            self.players_instance.update(player_id, context)
                        # Sell
                        elif data[1] == "s":
                            if data[2:] == "1":
                                qt = 1
                            elif data[2:] == "10":
                                qt = 10
                            else:
                                qt = stats[item]["quantity"]
                            for currency, price in sell_price.items():
                                gain = -get_price_for_n(price, stats[item]["quantity"], -qt)
                                exec("player.{} += gain".format(currency))
                                exec("player.{}_total += gain".format(currency))
                            exec("player.{} -= qt".format(item))
                            player.save()
                            stats = self.players_instance.get_stats(player_id)

                            self.players_instance.update(player_id, context)

                        message = "*🧮 Interface 🧮*\n\n*{}*\n".format(item.capitalize())
                        message += "You have {} {}\.\n".format(
                            get_si(stats[item]["quantity"]), item
                        )
                        message += "📈 Join:"
                        for currency, price in base_prices.items():
                            loss = get_price_for_n(price, stats[item]["quantity"], 1)
                            message += " –{} {} ".format(loss, currency)
                        message += "\n"
                        message += "📉 Leave:"
                        for currency, price in sell_price.items():
                            gain = -get_price_for_n(price, stats[item]["quantity"], -1)
                            message += " \+{} {} ".format(gain, currency)

                        # Select
                        ## Buy
                        # It's in there that we test for availability
                        buy = []
                        can_buy = CAP
                        for currency, price in base_prices.items():
                            loss = get_max_to_buy(
                                price, stats[item]["quantity"], stats[currency]["quantity"]
                            )
                            can_buy = min(can_buy, loss)
                        if can_buy >= 1:
                            buy.append(
                                InlineKeyboardButton(
                                    "📈 Join 1 {}".format(item),
                                    callback_data="{}b1".format(attrs["id"]),
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
                                    callback_data="{}b{}".format(attrs["id"], can_buy),
                                )
                            )

                        ## Sell
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

                        ## We found the correct
                        break

            reply_markup = InlineKeyboardMarkup(
                [buy, sell, [InlineKeyboardButton("Back", callback_data="stop")]]
            )

            try:
                query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")
            except BadRequest:  # Not edit to be done
                pass

        else:  # Main
            self.logger.info("{} requested the interface".format(update.effective_user.first_name))

            stats = self.players_instance.get_stats(player_id)
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
                message += get_quantities(player_id, self.players_instance)
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
                update.message.reply_text(
                    message, reply_markup=reply_markup, parse_mode="MarkdownV2"
                )


class AdminHandlers(BaseHandlers):
    def __init__(self, players_instance, logger=None, media_folder=None):
        command_handlers = [
            CommandHandler(["debug", "cheat", "rich"], self.be_rich),
            CommandHandler(["notify"], self.notify_all),
            CallbackQueryHandler(self.notify_all),
        ]
        super().__init__(
            command_handlers=command_handlers,
            players_instance=players_instance,
            logger=logger,
            media_folder=media_folder,
        )

    def be_rich(self, update: Update, context: CallbackContext) -> None:
        player_id = update.effective_user.id
        if player_id == ADMIN_CHAT:
            player, _ = self.players_instance.get_or_create(player_id)
            player.messages += 10_000_000_000
            player.messages_total += 10_000_000_000
            player.save()
        update.message.reply_text("Sent 10'000'000'000 messages.")
        self.logger.info("{} cheated.".format(update.effective_user.first_name))

    def notify_all(self, update: Update, context: CallbackContext) -> None:
        if update.effective_user.id == ADMIN_CHAT:
            if update.message.reply_to_message:
                for player in self.players_instance.Model.select():
                    context.bot.send_message(player.id, update.message.reply_to_message.text)
                self.logger.info(
                    "{} sent a global message.".format(update.effective_user.first_name)
                )
            else:
                text_to_send = "🗣 Message from admin 🗣\n{}".format(
                    update.effective_message.text.split(" ", 1)[1]
                )
                update.message.reply_text("This is a preview:").reply_text(text_to_send).reply_text(
                    "Reply /notify to the previous message to send it."
                )
