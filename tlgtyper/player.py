from collections import defaultdict

from peewee import BigIntegerField, CharField, FloatField, IntegerField, Model


class PlayerInstance:
    class Model(Model):
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
