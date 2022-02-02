"""
Handlers for the bot.
"""
from collections import Counter, defaultdict
from datetime import datetime
import os
import random


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, MessageHandler


from parameters import CAP, RESALE_PERCENTAGE
from secret import ADMIN_CHAT, BOT_LINK
from tlgtyper.achievements import ACHIEVEMENTS, ACHIEVEMENTS_ID, MAX_ACHIEVEMENTS
from tlgtyper.cooldown import update_cooldown_and_notify
from tlgtyper.helpers import get_si, power_10
from tlgtyper.items import accumulate_upgrades, get_max_to_buy, get_price_for_n, id_to_item_name, ITEMS, UPGRADES
from tlgtyper.jobs import remove_job_if_exists, update_job
from tlgtyper.texts import BLABLA_TEXT, get_quantities, HELP_COMMANDS, SUFFIXES_MEANING


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
                commands += "- {} => {};\n".format(", ".join(handler.command), handler.callback.__name__)
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
                commands += ["{} - {}\n".format(command, handler.callback.__name__) for command in handler.command]
            except:
                continue
        return commands


class AdminHandlers(BaseHandlers):
    def __init__(self, players_instance, logger=None, media_folder=None):
        command_handlers = [
            CommandHandler(["debug", "cheat", "rich"], self.be_rich),
            CommandHandler(["cap"], self.be_extra_rich),
            CommandHandler(["notify"], self.notify_all),
            CommandHandler(["total", "total_players"], self.total_players),
            CommandHandler(["alpha_ended"], self.give_everyone_alpha),
            CommandHandler(["beta_ended"], self.give_everyone_beta),
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
            self.players_instance.add_to_item(player_id, 10_000_000_000, "messages")
        update.message.reply_text("Sent 10'000'000'000 messages.")
        self.logger.info("[{}] {} cheated.".format(player_id, update.effective_user.first_name))

    def be_extra_rich(self, update: Update, context: CallbackContext) -> None:
        player_id = update.effective_user.id
        if player_id == ADMIN_CHAT:
            self.players_instance.add_to_item(player_id, CAP / 100, "messages")
        update.message.reply_text("Sent CAP messages.")
        self.logger.info("[{}] {} extra cheated.".format(player_id, update.effective_user.first_name))

    def notify_all(self, update: Update, context: CallbackContext) -> None:
        if update.effective_user.id == ADMIN_CHAT:
            total = len(list(self.players_instance.Model.select()))
            blocked = 0
            if update.message.reply_to_message:
                for player in self.players_instance.Model.select():
                    try:
                        context.bot.send_message(player.id, update.message.reply_to_message.text)
                    except:
                        blocked += 1
                self.logger.info(
                    "[{}] {} sent a global message to {} people ({} blocked).".format(
                        update.effective_user.id, update.effective_user.first_name, total - blocked, blocked
                    )
                )
                update.message.reply_text(
                    "Sent to {} people out of {} ({} failed).".format(total - blocked, total, blocked)
                )
            else:
                text_to_send = "🗣 Message from admin 🗣\n{}".format(update.effective_message.text.split(" ", 1)[1])
                update.message.reply_text("This is a preview:").reply_text(text_to_send).reply_text(
                    "Reply /notify to the previous message to send it."
                )

    def total_players(self, update: Update, context: CallbackContext) -> None:
        if update.effective_user.id == ADMIN_CHAT:
            update.message.reply_text(
                "There are currently {} players.".format(len(list(self.players_instance.Model.select())))
            )

    # Laziness is a hell of a drug
    def give_everyone_alpha(self, update: Update, context: CallbackContext) -> None:
        if update.effective_user.id == ADMIN_CHAT:
            for player in self.players_instance.Model.select():
                self.players_instance.cache[player.id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["alpha"]["id"])

    def give_everyone_beta(self, update: Update, context: CallbackContext) -> None:
        if update.effective_user.id == ADMIN_CHAT:
            for player in self.players_instance.Model.select():
                self.players_instance.cache[player.id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["beta"]["id"])


class PlayerHandlers(BaseHandlers):
    def __init__(self, players_instance, logger=None, media_folder=None):
        command_handlers = [
            CommandHandler(["start"], self.start_bot),
            CommandHandler(["new_game", "new", "reset_game", "reset"], self.new_game),
            MessageHandler(Filters.text & ~Filters.command, self.answer),
            CommandHandler(["help", "commands"], self.help_commands),
            CommandHandler(["quickmode", "quick", "quickmessage"], self.quickmode),
            CommandHandler(["stop", "stop_game", "end", "end_game"], self.stop_bot),
            CommandHandler(["stats", "stat"], self.show_stats),
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
            update.message.reply_document(gif, caption="👋 Welcome, {}!".format(user.first_name)).reply_text(
                "Press /new_game to play!"
            )

        self.logger.info("[{}] {} started the bot".format(user.id, user.first_name))

    def new_game(self, update: Update, context: CallbackContext):
        user = update.effective_user
        player_id = user.id
        player, created = self.players_instance.get_or_create(player_id)

        if created:
            player.first_name = user.first_name

            self.players_instance.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["start"]["id"])

            update.message.reply_text("❕ You're ready to play!")

            update.message.reply_text(
                "Simply send a plain message to the bot, and it will answer you – making your score go 📈."
            )
            update.message.reply_text(
                "Important: if you send too many messages at once, Telegram will kick you for at most 30 minutes, so, if you see that the bot is not answering anymore, take a break and go touch grass!"
            )

            update.message.reply_text(HELP_COMMANDS)

            update.message.reply_text(
                "Now, I am going to pin your counter to this conversation, so that you can see your progress!"
            )
            self.logger.info("[{}] {} started a new game".format(player_id, user.first_name))
        else:
            self.logger.info("[{}] {} did a reset".format(player_id, user.first_name))

        counter = update.message.reply_text(
            "Send a text (not a command!) to the bot to see this message update.\n"
            "(If the pinned message does not update, please do /new_game again.)"
        )

        self.players_instance.cache[player_id]["current_message"] = counter.text

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

        retry_after = update_cooldown_and_notify(player_id, self.players_instance, context)
        if retry_after:
            self.logger.error("[{}] {} is cooldown'd ({}s)".format(player_id, user.first_name, retry_after))
            return

        try:
            update.message.reply_text(update.message.text)  # TODO
            if update.message.text == "J'aime les loutres":
                self.players_instance.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["loutres"]["id"])
            self.players_instance.cache[player_id]["from_chat"] += 2
            self.players_instance.cache[player_id]["cooldown"]["counter"] += 1

            # Quickmode
            if "Get Max" in update.message.text:
                item = update.message.text.split("Get Max ")[1].lower()
                stats = self.players_instance.get_stats(player_id)
                if item not in stats.keys():
                    return

                player, _ = self.players_instance.get_or_create(player_id)
                base_prices = stats[item]["base_price"]

                qt = CAP
                for currency, price in base_prices.items():
                    loss = get_max_to_buy(price, stats[item]["quantity"], stats[currency]["quantity"])
                    qt = min(qt, loss)

                for currency, price in base_prices.items():
                    loss = get_price_for_n(price, stats[item]["quantity"], qt)
                    self.players_instance.sub_to_item(player_id, loss, currency)
                self.players_instance.add_to_item(player_id, qt, item)

                update.message.reply_text("[Quickmode] Got {} {}!".format(qt, item.capitalize()))
        except RetryAfter as e:
            self.logger.error("[{}] {}".format(player_id, str(e)))
            retry_after = int(str(e).split("in ")[1].split(".0")[0])
            self.players_instance.cache[player_id]["cooldown"]["retry_after"] = retry_after

    def help_commands(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        update.message.reply_text(HELP_COMMANDS).reply_text(SUFFIXES_MEANING)
        self.logger.info("[{}] {} requested help".format(user.id, user.first_name))

    def quickmode(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        player_id = user.id
        stats = self.players_instance.get_stats(player_id)

        buttons = []
        for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
            if "unlock_at" in attrs and stats[item]["unlocked"]:
                buttons.append(KeyboardButton("Get Max {}".format(item.capitalize())))

        buttons = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        kb_markup = ReplyKeyboardMarkup([[KeyboardButton(random.choice(BLABLA_TEXT))], *buttons])
        update.message.reply_text("Simply press the big keyboard button to use quickmode!", reply_markup=kb_markup)
        self.logger.info("[{}] {} requested quickmode".format(player_id, user.first_name))

    def stop_bot(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        player_id = user.id

        obj = self.players_instance.Model.get(self.players_instance.Model.id == player_id)
        obj.delete_instance()
        self.players_instance.Model.delete().where(self.players_instance.Model.id == player_id).execute()
        remove_job_if_exists(str(player_id), context)

        try:
            context.bot.unpin_chat_message(update.message.chat.id)
        except:
            pass

        update.message.reply_text("Game stopped, account deleted.")  # TODO
        self.logger.info("[{}] {} stopped the bot".format(player_id, user.first_name))

    def show_stats(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        player_id = user.id

        stats = self.players_instance.get_stats(player_id)
        message = "*📊 Stats 📊*\n_Stats of {} as of {}\._\n\n".format(
            update.effective_user.first_name, datetime.now().strftime("%B %d, %Y at %H:%M GMT")
        )

        user_achievements = self.players_instance.get_achievements(player_id)
        medals = Counter(
            [
                medal
                for achievement_id, (medal, _, _) in sorted(ACHIEVEMENTS.items())
                if achievement_id in user_achievements
            ]
        )
        if sum(medals.values()) > 0:
            message += "*Achievements*\n"
            message += "– Unlocked {} achievements out of {}\.\n".format(sum(medals.values()), MAX_ACHIEVEMENTS)
            message += "– {}\n".format(", ".join(["{} {}".format(qt, medal) for medal, qt in medals.items()]))
            message += "\n"

        if int(stats["messages"]["quantity"]) > 0:
            message += "*{}*\n".format("Messages")
            message += "– {} current {}\.\n".format(get_si(stats["messages"]["quantity"]), "messages")
            message += "– {} {} in total\.\n".format(get_si(stats["messages"]["total"]), "messages")
            message += "– {} upgrades unlocked out of {}\.\n".format(
                len(self.players_instance.get_upgrades(player_id, "messages")), len(UPGRADES["messages"])
            )
            message += "\n"

        per_second = defaultdict(int)
        for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
            if "unlock_at" in attrs and stats[item]["unlocked"]:
                if int(attrs["quantity"]) > 0:
                    message += "*{}*\n".format(item.capitalize())
                    message += "– {} current {}\.\n".format(get_si(attrs["quantity"]), item)
                    message += "– {} {} in total\.\n".format(get_si(attrs["total"]), item)
                    message += "– {} upgrades unlocked out of {}\.\n".format(
                        len(self.players_instance.get_upgrades(player_id, item)), len(UPGRADES[item])
                    )
                    for currency, quantity in attrs["gain"].items():
                        currency_per_second = (
                            accumulate_upgrades(item, stats[item]["upgrades"], stats[item]["gain"][currency])
                            * stats[item]["quantity"]
                        )
                        per_second[currency] += currency_per_second
                        message += "– Add {} {} per second\.\n".format(get_si(currency_per_second, type="f"), currency)
                    message += "\n"

        if sum(per_second.values()) > 0:
            message += "*Total*\n"
            for currency, quantity in per_second.items():
                message += "– Getting {} {} per second\.\n".format(get_si(quantity, type="f"), currency)

        message += "\n"
        message += BOT_LINK

        update.message.reply_text(message, parse_mode="MarkdownV2")
        self.logger.info("[{}] {} requested stats".format(player_id, update.effective_user.first_name))


(
    STATE_ACHIEVEMENTS_MAIN,
    STATE_ACHIEVEMENTS_CATALOG,
    STATE_ACHIEVEMENTS_SPECIFIC,
    STATE_INTERFACE_MAIN,
    STATE_INTERFACE_BUY_SELL,
    STATE_INTERFACE_UPGRADES,
    STATE_INTERFACE_TOOLS,
) = range(7)


class PlayerAchievementsHandlers(BaseHandlers):
    def __init__(self, players_instance, logger=None, media_folder=None):
        commands = ["achievements", "achievement"]
        command_handlers = [
            ConversationHandler(
                entry_points=[CommandHandler(commands, self.achievements)],
                states={
                    STATE_ACHIEVEMENTS_MAIN: [
                        CallbackQueryHandler(
                            self.achievements_catalog, pattern="^{}$".format(STATE_ACHIEVEMENTS_CATALOG)
                        ),
                    ],
                    STATE_ACHIEVEMENTS_CATALOG: [
                        CallbackQueryHandler(
                            self.achievements_catalog, pattern="^{}_?[0-9]*$".format(STATE_ACHIEVEMENTS_CATALOG)
                        ),
                        # CallbackQueryHandler(self.achievements_specific, pattern="^{}_[0-9]*$".format(STATE_SPECIFIC)),
                        CallbackQueryHandler(self.achievements_again, pattern="^{}$".format(STATE_ACHIEVEMENTS_MAIN)),
                    ],
                    STATE_ACHIEVEMENTS_SPECIFIC: [
                        CallbackQueryHandler(
                            self.achievements_catalog, pattern="^{}$".format(STATE_ACHIEVEMENTS_CATALOG)
                        ),
                    ],
                },
                fallbacks=[CommandHandler(commands, self.achievements)],
            )
        ]
        super().__init__(
            command_handlers=command_handlers,
            players_instance=players_instance,
            logger=logger,
            media_folder=media_folder,
        )

    def achievements(self, update: Update, context: CallbackContext) -> int:
        player_id = update.effective_user.id

        user_achievements = self.players_instance.get_achievements(player_id)
        question = "❔"

        things = [
            "{:02X}: {}".format(id, medal if id in user_achievements else question)
            for id, (medal, _, _) in sorted(ACHIEVEMENTS.items())
        ]
        things = [things[i : i + 5] for i in range(0, len(things), 5)]
        message = "*🌟 Achievements 🌟*\n_Unlocked {} achievements out of {}_\n\n".format(
            len(user_achievements), len(ACHIEVEMENTS.items())
        )
        message += "\n".join(["`{}`".format(", ".join(text)) for text in things])

        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Catalog View", callback_data=str(STATE_ACHIEVEMENTS_CATALOG)),
                ]
            ]
        )

        update.message.reply_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")

        self.logger.info("[{}] {} requested achievements".format(player_id, update.effective_user.first_name))

        return STATE_ACHIEVEMENTS_MAIN

    def achievements_again(self, update: Update, context: CallbackContext) -> int:
        player_id = update.effective_user.id

        user_achievements = self.players_instance.get_achievements(player_id)
        question = "❔"

        things = [
            "{:02X}: {}".format(id, medal if id in user_achievements else question)
            for id, (medal, _, _) in sorted(ACHIEVEMENTS.items())
        ]
        things = [things[i : i + 5] for i in range(0, len(things), 5)]
        message = "*🌟 Achievements 🌟*\n_Unlocked {} achievements out of {}_\n\n".format(
            len(user_achievements), len(ACHIEVEMENTS.items())
        )
        message += "\n".join([", ".join(text) for text in things])

        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Catalog View", callback_data=str(STATE_ACHIEVEMENTS_CATALOG)),
                ]
            ]
        )

        query = update.callback_query
        query.answer()
        update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")

        return STATE_ACHIEVEMENTS_MAIN

    def achievements_catalog(self, update: Update, context: CallbackContext) -> int:
        player_id = update.effective_user.id
        query = update.callback_query
        query.answer()
        data = query.data

        user_achievements = self.players_instance.get_achievements(player_id)
        question = "❔"
        not_yet = "\[You don't have this achievement just yet\.\.\.\]"

        if data[2:]:
            page = int(data[2:])
        else:
            page = 0

        total_pages = len(ACHIEVEMENTS.items()) // 5

        message = "*🌟 Achievements 🌟*\n_Page {} out of {}_\n\n".format(page + 1, total_pages + 1)
        for achievement_id, (medal, title, text) in sorted(ACHIEVEMENTS.items())[5 * page : 5 * (page + 1)]:
            message += "*{} {} {}*\n_{}_\n\n".format(
                medal if achievement_id in user_achievements else question,
                title,
                medal if achievement_id in user_achievements else question,
                text if achievement_id in user_achievements else not_yet,
            )

        page_buttons = []
        if page > 0:
            page_buttons.append(
                InlineKeyboardButton(
                    "Previous Page", callback_data="{}_{}".format(STATE_ACHIEVEMENTS_CATALOG, page - 1)
                ),
            )
        if page < total_pages:
            page_buttons.append(
                InlineKeyboardButton("Next Page", callback_data="{}_{}".format(STATE_ACHIEVEMENTS_CATALOG, page + 1)),
            )

        reply_markup = InlineKeyboardMarkup(
            [
                page_buttons,
                [
                    InlineKeyboardButton("Global View", callback_data=str(STATE_ACHIEVEMENTS_MAIN)),
                ],
            ]
        )

        try:
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")
        except BadRequest as e:  # Not edit to be done
            self.logger.warning("[{}] {}".format(player_id, str(e)))
            pass

        return STATE_ACHIEVEMENTS_CATALOG


class PlayerInterfaceHandlers(BaseHandlers):
    def __init__(self, players_instance, logger=None, media_folder=None):
        commands = ["shop", "interface", "upgrades", "menu", "buy", "sell", "join", "leave"]
        command_handlers = [
            ConversationHandler(
                entry_points=[CommandHandler(commands, self.interface)],
                states={
                    STATE_INTERFACE_MAIN: [
                        CallbackQueryHandler(self.buy_sell, pattern="^{}$".format(STATE_INTERFACE_BUY_SELL)),
                        CallbackQueryHandler(self.upgrades, pattern="^{}$".format(STATE_INTERFACE_UPGRADES)),
                        # CallbackQueryHandler(self.tools, pattern="^{}$".format(STATE_TOOLS)),
                    ],
                    STATE_INTERFACE_BUY_SELL: [
                        CallbackQueryHandler(
                            self.buy_sell, pattern="^{}[a-z]?[x|b|s]?(1|10|max)?$".format(STATE_INTERFACE_BUY_SELL)
                        ),
                        CallbackQueryHandler(self.interface_again, pattern="^{}$".format(STATE_INTERFACE_MAIN)),
                    ],
                    STATE_INTERFACE_UPGRADES: [
                        CallbackQueryHandler(
                            self.upgrades, pattern="^{}[a-z]?[0-9]*$".format(STATE_INTERFACE_UPGRADES)
                        ),
                        CallbackQueryHandler(self.interface_again, pattern="^{}$".format(STATE_INTERFACE_MAIN)),
                    ],
                    # STATE_TOOLS: [],
                },
                fallbacks=[CommandHandler(commands, self.interface)],
            ),
        ]
        super().__init__(
            command_handlers=command_handlers,
            players_instance=players_instance,
            logger=logger,
            media_folder=media_folder,
        )

    def interface(self, update: Update, context: CallbackContext):
        player_id = update.effective_user.id
        player, _ = self.players_instance.get_or_create(player_id)
        retry_after = update_cooldown_and_notify(player_id, self.players_instance, context)
        if retry_after:
            self.logger.error(
                "[{}] {} is cooldown'd ({}s)".format(player_id, update.effective_user.first_name, retry_after)
            )
            return

        choices = [
            [
                InlineKeyboardButton("📈 Get/Forfeit 📉", callback_data=str(STATE_INTERFACE_BUY_SELL)),
            ]
        ]
        if player.upgrades:
            choices.append(
                [
                    InlineKeyboardButton("🆙 Upgrades 🆙", callback_data=str(STATE_INTERFACE_UPGRADES)),
                ]
            )
        if player.tools:
            choices.append(
                [
                    InlineKeyboardButton("🛠 Tools 🛠", callback_data=str(STATE_INTERFACE_TOOLS)),
                ]
            )
        reply_markup = InlineKeyboardMarkup(choices)

        message = (
            "*⌨️Main menu ⌨️*\n\n"
            "Here you can get or forfeit items, upgrade them, and more\.\.\.\n\n"
            "\.\.\. Given you have what it takes\."
        )

        update.message.reply_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")

        self.logger.info("[{}] {} requested the shop".format(player_id, update.effective_user.first_name))

        return STATE_INTERFACE_MAIN

    def interface_again(self, update: Update, context: CallbackContext):
        player_id = update.effective_user.id
        player, _ = self.players_instance.get_or_create(player_id)
        retry_after = update_cooldown_and_notify(player_id, self.players_instance, context)
        if retry_after:
            self.logger.error(
                "[{}] {} is cooldown'd ({}s)".format(player_id, update.effective_user.first_name, retry_after)
            )
            return

        choices = [
            [
                InlineKeyboardButton("📈 Get/Forfeit 📉", callback_data=str(STATE_INTERFACE_BUY_SELL)),
            ]
        ]
        if player.upgrades:
            choices.append(
                [
                    InlineKeyboardButton("🆙 Upgrades 🆙", callback_data=str(STATE_INTERFACE_UPGRADES)),
                ]
            )
        if player.tools:
            choices.append(
                [
                    InlineKeyboardButton("🛠 Tools 🛠", callback_data=str(STATE_INTERFACE_TOOLS)),
                ]
            )
        reply_markup = InlineKeyboardMarkup(choices)

        message = (
            "*⌨️Main menu ⌨️*\n\n"
            "Here you can get or forfeit items, upgrade them, and more\.\.\.\n\n"
            "\.\.\. Given you have what it takes\."
        )

        query = update.callback_query
        query.answer()
        update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")

        return STATE_INTERFACE_MAIN

    def buy_sell(self, update: Update, context: CallbackContext):
        player_id = update.effective_user.id
        query = update.callback_query
        query.answer()
        data = query.data

        # Main
        if data == str(STATE_INTERFACE_BUY_SELL):
            stats = self.players_instance.get_stats(player_id)
            choices = []
            for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
                if "unlock_at" in attrs and stats[item]["unlocked"]:
                    choices.append(
                        InlineKeyboardButton(
                            "{} {}".format(stats[item]["symbol"], item.capitalize()),
                            callback_data="{}{}x".format(STATE_INTERFACE_BUY_SELL, stats[item]["id"]),
                        )
                    )

            message = "*📈 Get/Forfeit 📉*\n\n"
            if choices:
                message += get_quantities(player_id, self.players_instance)
                message += "\n\nSelect what you would like to bargain:"
                choices = [choices[i : i + 2] for i in range(0, len(choices), 2)]
            else:
                message = "You don't have enough messages for now\.\.\."

            choices.append([InlineKeyboardButton("↩️ Back", callback_data=str(STATE_INTERFACE_MAIN))])
            reply_markup = InlineKeyboardMarkup(choices)

            update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")

        # Choice has been made
        else:
            stats = self.players_instance.get_stats(player_id)

            buy = []
            sell = []
            message = "*📈 Get/Forfeit 📉*\n\n"

            # Seeking for the correct one
            for item, attrs in stats.items():
                if "id" in attrs:
                    if data[1] == attrs["id"]:
                        base_prices = stats[item]["base_price"]
                        sell_price = {
                            currency: int(price * RESALE_PERCENTAGE) for currency, price in base_prices.items()
                        }

                        # Buy
                        if data[2] == "b":
                            if data[3:] == "1":
                                qt = 1
                            elif data[3:] == "10":
                                qt = 10
                            else:
                                qt = CAP
                                for currency, price in base_prices.items():
                                    loss = get_max_to_buy(price, stats[item]["quantity"], stats[currency]["quantity"])
                                    qt = min(qt, loss)
                            for currency, price in base_prices.items():
                                loss = get_price_for_n(price, stats[item]["quantity"], qt)
                                self.players_instance.sub_to_item(player_id, loss, currency)
                            self.players_instance.add_to_item(player_id, qt, item)
                            stats = self.players_instance.get_stats(player_id)

                            if 10 <= stats[item]["quantity"] <= 10_000_000:
                                ach = power_10(stats[item]["quantity"])
                                while ach >= 10:
                                    try:
                                        self.players_instance.cache[update.effective_user.id]["achievements"].append(
                                            ACHIEVEMENTS_ID[item]["quantity{}".format(ach)]["id"]
                                        )
                                    except KeyError as e:
                                        self.logger.warning("[{}] {}".format(player_id, str(e)))
                                        pass
                                    ach //= 10
                            if 10 <= stats[item]["total"] <= 10_000_000:
                                ach = power_10(stats[item]["total"])
                                while ach >= 10:
                                    try:
                                        self.players_instance.cache[update.effective_user.id]["achievements"].append(
                                            ACHIEVEMENTS_ID[item]["total{}".format(ach)]["id"]
                                        )
                                    except KeyError as e:
                                        self.logger.warning("[{}] {}".format(player_id, str(e)))
                                        pass
                                    ach //= 10

                            self.players_instance.update(player_id, context)

                        # Sell
                        elif data[2] == "s":
                            if data[3:] == "1":
                                qt = 1
                            elif data[3:] == "10":
                                qt = 10
                            else:
                                qt = stats[item]["quantity"]
                            for currency, price in sell_price.items():
                                gain = get_price_for_n(price, stats[item]["quantity"], -qt)
                                self.players_instance.add_to_item(player_id, gain, currency)
                            self.players_instance.sub_to_item(player_id, qt, item)
                            stats = self.players_instance.get_stats(player_id)

                            self.players_instance.update(player_id, context)

                        message += "*{} {}*\n".format(stats[item]["symbol"], item.capitalize())
                        message += "You have {} {}\.\n\n".format(get_si(stats[item]["quantity"]), item)
                        message += "💸 Cost to Get:\n"
                        for currency, price in base_prices.items():
                            loss = get_price_for_n(price, stats[item]["quantity"], 1)
                            message += "– {} {}\n".format(get_si(loss), currency)
                        message += "\n"
                        message += "💰 Gain for Forfeit:\n"
                        for currency, price in sell_price.items():
                            gain = get_price_for_n(price, stats[item]["quantity"], -1)
                            message += "– {} {}\n".format(get_si(gain), currency)
                        message += "\n"
                        message += "📈 Gains per Second \(for one\):\n"
                        for currency, quantity in attrs["gain"].items():
                            currency_per_second = (
                                    accumulate_upgrades(item, stats[item]["upgrades"], stats[item]["gain"][currency])
                            )
                            if currency_per_second >= 0.01:
                                message += "– Add {} {} per second\.\n".format(get_si(currency_per_second, type="f"),
                                                                           currency)

                        # Select
                        ## Buy
                        # It's in there that we test for availability
                        buy = []
                        can_buy = CAP
                        for currency, price in base_prices.items():
                            loss = get_max_to_buy(price, stats[item]["quantity"], stats[currency]["quantity"])
                            can_buy = min(can_buy, loss)
                        if can_buy >= 1:
                            buy.append(
                                InlineKeyboardButton(
                                    "Get 1 {}".format(item[:-1]),
                                    callback_data="{}{}b1".format(STATE_INTERFACE_BUY_SELL, attrs["id"]),
                                )
                            )
                            if can_buy >= 10:
                                buy.append(
                                    InlineKeyboardButton(
                                        "Get 10 {}".format(item),
                                        callback_data="{}{}b10".format(STATE_INTERFACE_BUY_SELL, attrs["id"]),
                                    )
                                )
                            else:
                                buy.append(
                                    InlineKeyboardButton(
                                        " ", callback_data="{}{}x".format(STATE_INTERFACE_BUY_SELL, attrs["id"])
                                    )
                                )
                            buy.append(
                                InlineKeyboardButton(
                                    "Get max {}".format(item),
                                    callback_data="{}{}bmax".format(STATE_INTERFACE_BUY_SELL, attrs["id"]),
                                )
                            )
                        else:
                            buy = [
                                InlineKeyboardButton(
                                    "", callback_data="{}{}x".format(STATE_INTERFACE_BUY_SELL, attrs["id"])
                                )
                            ] * 3

                        ## Sell
                        sell = []
                        if stats[item]["quantity"] >= 1:
                            sell.append(
                                InlineKeyboardButton(
                                    "Forfeit 1 {}".format(item[:-1]),
                                    callback_data="{}{}s1".format(STATE_INTERFACE_BUY_SELL, attrs["id"]),
                                )
                            )
                            if stats[item]["quantity"] >= 10:
                                sell.append(
                                    InlineKeyboardButton(
                                        "Forfeit 10 {}".format(item),
                                        callback_data="{}{}s10".format(STATE_INTERFACE_BUY_SELL, attrs["id"]),
                                    )
                                )
                            else:
                                sell.append(
                                    InlineKeyboardButton(
                                        "", callback_data="{}{}x".format(STATE_INTERFACE_BUY_SELL, attrs["id"])
                                    )
                                )
                            sell.append(
                                InlineKeyboardButton(
                                    "Forfeit all {}".format(item),
                                    callback_data="{}{}smax".format(STATE_INTERFACE_BUY_SELL, attrs["id"]),
                                )
                            )
                        else:
                            sell = [
                                InlineKeyboardButton(
                                    "", callback_data="{}{}x".format(STATE_INTERFACE_BUY_SELL, attrs["id"])
                                )
                            ] * 3

                        ## We found the correct one
                        break

            buttons = list(map(list, zip(*[buy, sell])))
            buttons.append([InlineKeyboardButton("↩️ Back", callback_data="{}".format(STATE_INTERFACE_BUY_SELL))])

            reply_markup = InlineKeyboardMarkup(buttons)
            try:
                query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")
            except BadRequest as e:  # Not edit to be done
                self.logger.warning("[{}] {}".format(player_id, str(e)))
                pass

        return STATE_INTERFACE_BUY_SELL

    def upgrades(self, update: Update, context: CallbackContext):
        player_id = update.effective_user.id
        query = update.callback_query
        query.answer()
        data = query.data

        # Main
        if data == str(STATE_INTERFACE_UPGRADES):
            stats = self.players_instance.get_stats(player_id)
            choices = []
            for item, upgrades in UPGRADES.items():
                if stats[item]["unlocked"]:
                    choices.append(
                        InlineKeyboardButton(
                            "{} {}".format(stats[item]["symbol"], item.capitalize()),
                            callback_data="{}{}".format(STATE_INTERFACE_UPGRADES, stats[item]["id"]),
                        )
                    )

            message = "*🆙 Upgrades 🆙*\n\n"
            if choices:
                message += (
                    "Upgrades are way to enhance the production of messages\.\n\n"
                    "Select what you would like to upgrade:"
                )
                choices = [choices[i : i + 2] for i in range(0, len(choices), 2)]
            else:
                message = "You cannot upgrade anything for now\.\.\."

            choices.append([InlineKeyboardButton("↩️ Back", callback_data=str(STATE_INTERFACE_MAIN))])
            reply_markup = InlineKeyboardMarkup(choices)

            update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")

        # Choice has been made
        else:
            item = id_to_item_name(data[1])
            current_upgrades = set(self.players_instance.get_upgrades(player_id, item))

            if data[2:]:
                upgrade_id = int(data[2:])
                for currency, quantity in UPGRADES[item][upgrade_id]["cost"].items():
                    self.players_instance.sub_to_item(player_id, quantity, currency)
                current_upgrades.add(upgrade_id)
                player, _ = self.players_instance.get_or_create(player_id)
                exec('player.{}_upgrades = ", ".join([str(num) for num in current_upgrades if num])'.format(item))
                player.save()

                self.players_instance.update(player_id, context)

            stats = self.players_instance.get_stats(player_id)

            message = "*🆙 Upgrades 🆙*\n\n"
            message += "*{} {}*\n\n".format(stats[item]["symbol"], item.capitalize())
            message += "Available upgrades:\n"
            available_upgrades = []
            some_upgrades = False

            for upgrade_id, attrs in UPGRADES[item].items():
                if upgrade_id not in current_upgrades:
                    available = True
                    for currency, quantity in attrs["conditions"].items():
                        if stats[currency]["total"] < quantity:
                            available = False
                            break
                    if available:
                        some_upgrades = True
                        message += (
                            "*\[{}\] {}*\n"
                            "_{}_\n"
                            "Costs: {}\n".format(
                                upgrade_id,
                                attrs["title"],
                                attrs["text"],
                                ", ".join(
                                    [
                                        "{} {}".format(get_si(quantity), currency)
                                        for currency, quantity in attrs["cost"].items()
                                    ]
                                ),
                            )
                        )
                        can_buy = True
                        for currency, quantity in UPGRADES[item][upgrade_id]["cost"].items():
                            if stats[currency]["quantity"] < quantity:
                                can_buy = False
                                break
                        if can_buy:
                            available_upgrades.append(upgrade_id)

            if not some_upgrades:
                message += "None for the moment\.\n"

            message += "\nAcquired upgrades:\n"
            for upgrade_id in current_upgrades:
                attrs = UPGRADES[item][upgrade_id]
                message += "*\[{}\] {}*\n" "_{}_\n".format(
                    upgrade_id,
                    attrs["title"],
                    attrs["text"],
                )

            buttons = [
                InlineKeyboardButton(
                    upgrade_id, callback_data="{}{}{}".format(STATE_INTERFACE_UPGRADES, stats[item]["id"], upgrade_id)
                )
                for upgrade_id in available_upgrades
            ]
            buttons = [buttons[i : i + 4] for i in range(0, len(buttons), 4)]
            buttons.append([InlineKeyboardButton("↩️ Back", callback_data="{}".format(STATE_INTERFACE_UPGRADES))])

            reply_markup = InlineKeyboardMarkup(buttons)
            try:
                query.edit_message_text(message, reply_markup=reply_markup, parse_mode="MarkdownV2")
            except BadRequest as e:  # Not edit to be done
                self.logger.warning("[{}] {}".format(player_id, str(e)))
                pass

        return STATE_INTERFACE_UPGRADES
