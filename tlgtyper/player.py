from collections import defaultdict


from peewee import BigIntegerField, CharField, IntegerField, Model
from telegram.error import BadRequest, RetryAfter, TimedOut
from telegram.ext import CallbackContext


from parameters import CAP
from tlgtyper.achievements import ACHIEVEMENTS, ACHIEVEMENTS_ID
from tlgtyper.cooldown import set_cooldown, update_cooldown_and_notify
from tlgtyper.items import ITEMS
from tlgtyper.jobs import remove_job_if_exists
from tlgtyper.texts import get_quantities


class Players:
    def __init__(self, logger):
        self.logger = logger

    class Model(Model):
        # Self
        id = BigIntegerField(unique=True)
        first_name = CharField(null=True)
        pinned_message = BigIntegerField(null=True)

        # Stats
        messages = CharField(default="0")
        messages_state = IntegerField(default=1)  # bool; Unlocked by default
        messages_total = CharField(default="0")
        messages_upgrades = CharField(default="")  # "xx,yy"

        contacts = CharField(default="0")
        contacts_state = IntegerField(default=0)  # bool
        contacts_total = CharField(default="0")
        contacts_upgrades = CharField(default="")  # "xx,yy"

        groups = CharField(default="0")
        groups_state = IntegerField(default=0)  # bool
        groups_total = CharField(default="0")
        groups_upgrades = CharField(default="")  # "xx,yy"

        channels = CharField(default="0")
        channels_state = IntegerField(default=0)  # bool
        channels_total = CharField(default="0")
        channels_upgrades = CharField(default="")  # "xx,yy"

        supergroups = CharField(default="0")
        supergroups_state = IntegerField(default=0)  # bool
        supergroups_total = CharField(default="0")
        supergroups_upgrades = CharField(default="")  # "xx,yy"

        upgrades = IntegerField(default=0)  # bool
        tools = IntegerField(default=0)  # bool
        achievements = CharField(default="")  # "xx,yy"

    cache = defaultdict(
        lambda: {
            "from_chat": 0,
            "achievements": [],
            "cooldown": {"informed": False, "retry_after": 0, "counter": 0},
        }
    )

    def get_or_create(self, player_id):
        return self.Model.get_or_create(id=player_id)

    def add_to_item(self, player_id: int, quantity: float, item: str) -> bool:
        # Quantities are stored as STRING, and last two digits are floating.
        quantity = int(quantity * 100)

        player, _ = self.Model.get_or_create(id=player_id)
        actual = int(eval("player.{}".format(item)))
        actual_total = int(eval("player.{}_total".format(item)))

        # We cannot deduce negative quantities
        if quantity < 0:
            if actual < -quantity:
                return False

        # Caping
        if actual + quantity > CAP:
            self.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["cap"]["id"])
            exec("player.{} = str(CAP)".format(item))
            exec("player.{}_total = str(CAP)".format(item))
        else:
            exec("player.{} = str(actual + quantity)".format(item))
            exec("player.{}_total = str(actual_total + quantity)".format(item))

        player.save()
        return True

    def sub_to_item(self, player_id: int, quantity: float, item: str) -> bool:
        return self.add_to_item(player_id, -quantity, item)

    def get_item(self, player_id: int, item: str) -> float:
        player, _ = self.Model.get_or_create(id=player_id)
        # Quantities are stored as STRING, and last two digits are floating.
        return int(eval("player.{}".format(item))) / 100

    def get_item_total(self, player_id: int, item: str) -> float:
        player, _ = self.Model.get_or_create(id=player_id)
        # Quantities are stored as STRING, and last two digits are floating.
        return int(eval("player.{}_total".format(item))) / 100

    def get_stats(self, player_id):
        player, _ = self.get_or_create(player_id)
        scope = locals()

        result = {
            item: {
                **attrs,
                **{
                    "unlocked": eval("player.{}_state".format(item), scope),
                    # Quantities are stored as STRING, and last two digits are floating.
                    "quantity": int(eval("player.{}".format(item), scope)) / 100,
                    "total": int(eval("player.{}_total".format(item), scope)) / 100,
                    "upgrades": eval("player.{}_upgrades".format(item), scope),
                },
            }
            for item, attrs in ITEMS.items()
        }

        del result["messages"]["unlock_at"]  # TODO: ugly

        return result

    def get_achievements(self, player_id: int):
        player, _ = self.get_or_create(player_id)
        return [int(num) for num in player.achievements.split(",") if num]

    def get_upgrades(self, player_id: int, item: str):
        player, _ = self.get_or_create(player_id)
        upgrades = eval("player.{}_upgrades".format(item))
        return [int(num) for num in upgrades.split(",") if num]

    def update_unlocks(self, player_id: int) -> None:
        player, _ = self.get_or_create(player_id)
        stats = self.get_stats(player_id)

        for item, attrs in stats.items():  # e.g., "contacts": {"unlock_at", ...}
            if "unlock_at" in attrs and not stats[item]["unlocked"]:
                unlock = True
                for unlock_item, unlock_quantity in attrs["unlock_at"].items():  # e.g., "messages": 10
                    if stats[unlock_item]["total"] < unlock_quantity:
                        unlock = False
                        break
                if unlock:
                    exec("player.{}_state = 1".format(item))
                    Players.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID[item]["unlocked"]["id"])

        # Upgrades
        if stats["messages"]["total"] >= 420:
            player.upgrades = 1
            Players.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["upgrades"]["id"])

        # Tools
        # if stats["messages"]["total"] >= 1_337:
        #     player.tools = 1
        #     Players.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["tools"]["id"])

        player.save()

    def update_pinned_message(
        self, player_id: int, context: CallbackContext
    ) -> None:  # TODO ugly and not in the correct place
        player, _ = self.get_or_create(player_id)
        if update_cooldown_and_notify(player_id, self, context):
            return

        message = get_quantities(player_id, self)

        try:
            context.bot.edit_message_text(message, player_id, player.pinned_message)
        # Spam protection
        except RetryAfter as e:
            self.logger.error(str(e))
            retry_after = int(str(e).split("in ")[1].split(".0")[0])
            self.cache[player_id]["cooldown"]["retry_after"] = retry_after
        # Time protection
        except TimedOut as e:
            self.logger.error(str(e))
            context.bot.send_message(
                player_id,
                "Oops\! I am currently experimenting network issues\. I'll try my best to get back to you as soon as possible\!",
                parse_mode="MarkdownV2",
            )
        # Edit problem
        except BadRequest as e:
            self.logger.error(str(e))
            if "Message to edit not found" in str(e):
                context.bot.send_message(
                    player_id,
                    "Oops\! It seems like I did not find the pinned message\. Could you use /reset, please\?",
                    parse_mode="MarkdownV2",
                )
                remove_job_if_exists(str(player_id), context)

    def update_achievements(
        self, player_id: int, context: CallbackContext
    ) -> None:  # TODO ugly and not in the correct place
        user, _ = self.get_or_create(player_id)
        user_achievements = self.get_achievements(player_id)
        data = list(set(self.cache[player_id]["achievements"]))
        self.cache[player_id]["achievements"] = []
        user.achievements = ",".join([str(num) for num in list(set(user_achievements + data))])
        user.save()

        for achievement in data:
            if achievement not in user_achievements:
                medal, title, text = ACHIEVEMENTS[achievement]
                message = "*{} {} {}*\n_{}_".format(medal, title, medal, text)
                context.bot.send_message(player_id, message, parse_mode="MarkdownV2")

    def update(self, player_id: int, context: CallbackContext):
        set_cooldown(player_id, self)
        self.update_unlocks(player_id)
        self.update_pinned_message(player_id, context)
        self.update_achievements(player_id, context)
