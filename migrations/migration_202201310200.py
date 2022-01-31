from peewee import BigIntegerField, CharField, IntegerField, Model, SqliteDatabase
from playhouse.migrate import migrate, SqliteMigrator


DB_PATH = "./db/database.db"
CAP = int(1e200) * 100 + 99

DB = SqliteDatabase(DB_PATH)
migrator = SqliteMigrator(DB)

# Add migration here

migrate(
    migrator.alter_column_type("Model", "messages", CharField(default="0")),
    migrator.alter_column_type("Model", "messages_total", CharField(default="0")),
    migrator.alter_column_type("Model", "contacts", CharField(default="0")),
    migrator.alter_column_type("Model", "contacts_total", CharField(default="0")),
    migrator.alter_column_type("Model", "groups", CharField(default="0")),
    migrator.alter_column_type("Model", "groups_total", CharField(default="0")),
    migrator.alter_column_type("Model", "channels", CharField(default="0")),
    migrator.alter_column_type("Model", "channels_total", CharField(default="0")),
    migrator.alter_column_type("Model", "supergroups", CharField(default="0")),
    migrator.alter_column_type("Model", "supergroups_total", CharField(default="0")),
)


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


DB.bind([Model])
# DB.connect()
DB.create_tables([Model])

for player in Model.select():
    for header in [
        "messages",
        "messages_total",
        "contacts",
        "contacts_total",
        "groups",
        "groups_total",
        "channels",
        "channels_total",
        "supergroups",
        "supergroups_total",
    ]:
        current = eval("player.{}".format(header))  # str
        try:
            current = int(float(current) * 100)  # int(float(str) * 100) -> int
            if current < 0 or current > CAP:
                exec("player.{} = str(CAP)".format(header))
            else:
                exec("player.{} = str(current)".format(header))
        except OverflowError as e:
            exec("player.{} = str(CAP)".format(header))
    player.save()
