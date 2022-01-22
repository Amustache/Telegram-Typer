from collections import defaultdict


from peewee import BigIntegerField, CharField, FloatField, IntegerField, Model
from telegram.error import BadRequest, RetryAfter
from telegram.ext import CallbackContext


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
        messages = FloatField(default=0)
        messages_state = IntegerField(default=1)  # bool; Unlocked by default
        messages_total = FloatField(default=0)
        messages_upgrades = CharField(default="")  # "xx,yy"

        contacts = FloatField(default=0)
        contacts_state = IntegerField(default=0)  # bool
        contacts_total = FloatField(default=0)
        contacts_upgrades = CharField(default="")  # "xx,yy"

        groups = FloatField(default=0)
        groups_state = IntegerField(default=0)  # bool
        groups_total = FloatField(default=0)
        groups_upgrades = CharField(default="")  # "xx,yy"

        channels = FloatField(default=0)
        channels_state = IntegerField(default=0)  # bool
        channels_total = FloatField(default=0)
        channels_upgrades = CharField(default="")  # "xx,yy"

        supergroups = FloatField(default=0)
        supergroups_state = IntegerField(default=0)  # bool
        supergroups_total = FloatField(default=0)
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

    def get_stats(self, player_id):
        player, _ = self.get_or_create(player_id)
        scope = locals()

        result = {
            item: {
                **attrs,
                **{
                    "unlocked": eval("player.{}_state".format(item), scope),
                    "quantity": eval("player.{}".format(item), scope),
                    "total": eval("player.{}_total".format(item), scope),
                    "upgrades": eval("player.{}_upgrades".format(item), scope),
                },
            }
            for item, attrs in ITEMS.items()
        }

        del result["messages"]["unlock_at"]  # TODO: ugly

        return result

    def get_achievements(self, player_id: int):
        user, _ = self.get_or_create(player_id)
        return [int(num) for num in user.achievements.split(",") if num]

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
        if stats["messages"]["total"] >= 1_337:
            player.tools = 1
            Players.cache[player_id]["achievements"].append(ACHIEVEMENTS_ID["misc"]["tools"]["id"])

        player.save()

    def update_pinned_message(
        self, player_id: int, context: CallbackContext
    ) -> None:  # TODO ugly and not in the correct place
        user, _ = self.get_or_create(player_id)
        if update_cooldown_and_notify(player_id, self, context):
            return

        message = get_quantities(player_id, self)

        try:
            context.bot.edit_message_text(message, player_id, user.pinned_message)
        except RetryAfter as e:
            self.logger.error(str(e))
            retry_after = int(str(e).split("in ")[1].split(".0")[0])
            self.cache[player_id]["cooldown"]["retry_after"] = retry_after
        # Edit problem
        except BadRequest as e:
            if "Message to edit not found" in str(e):
                context.bot.send_message(
                    player_id,
                    "Oops\! It seems like I did not find the pinned message\. Could you use /reset, please\?",
                    parse_mode="MarkdownV2",
                )
                remove_job_if_exists(str(player_id), context)
            self.logger.error(str(e))

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
