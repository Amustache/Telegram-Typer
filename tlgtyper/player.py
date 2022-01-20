from collections import defaultdict

from peewee import BigIntegerField, CharField, FloatField, IntegerField, Model

from tlgtyper.items import ITEMS


class PlayerInstance:
    class Model(Model):
        # Self
        id = BigIntegerField(unique=True)
        first_name = CharField(null=True)
        pinned_message = BigIntegerField(null=True)

        # Stats
        messages = FloatField(default=0)
        messages_state = IntegerField(default=1)  # Unlocked by default
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

        achievements = CharField(default="")

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

        result = {
            item: {**attrs, **{
                "unlocked": 1,  # eval("player.{}_state".format(item)),
                "quantity": 0,  # eval("player.{}".format(item)),
                "total": 0,  # eval("player.{}_total".format(item)),
            }}
            for item, attrs in ITEMS.items()
        }

        del result["messages"]["unlock_at"]  # TODO: ugly

        return result

    def get_achievements(self, player_id):
        user, _ = self.get_or_create(player_id)
        return [int(num) for num in user.achievements.split(",") if num]
