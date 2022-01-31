#!/usr/bin/env python
from peewee import BigIntegerField, CharField, FloatField, IntegerField, Model, SqliteDatabase
from tabulate import tabulate


DB_PATH = "./db/database.db"


class Model(Model):
    # Self
    id = BigIntegerField(unique=True)
    first_name = CharField(null=True)
    pinned_message = BigIntegerField(null=True)

    # Stats
    messages = BigIntegerField(default=0)
    messages_state = IntegerField(default=1)  # bool; Unlocked by default
    messages_total = BigIntegerField(default=0)
    messages_upgrades = CharField(default="")  # "xx,yy"

    contacts = BigIntegerField(default=0)
    contacts_state = IntegerField(default=0)  # bool
    contacts_total = BigIntegerField(default=0)
    contacts_upgrades = CharField(default="")  # "xx,yy"

    groups = BigIntegerField(default=0)
    groups_state = IntegerField(default=0)  # bool
    groups_total = BigIntegerField(default=0)
    groups_upgrades = CharField(default="")  # "xx,yy"

    channels = BigIntegerField(default=0)
    channels_state = IntegerField(default=0)  # bool
    channels_total = BigIntegerField(default=0)
    channels_upgrades = CharField(default="")  # "xx,yy"

    supergroups = BigIntegerField(default=0)
    supergroups_state = IntegerField(default=0)  # bool
    supergroups_total = BigIntegerField(default=0)
    supergroups_upgrades = CharField(default="")  # "xx,yy"

    upgrades = IntegerField(default=0)  # bool
    tools = IntegerField(default=0)  # bool
    achievements = CharField(default="")  # "xx,yy"


DB = SqliteDatabase(DB_PATH)
DB.bind([Model])
DB.connect()
DB.create_tables([Model])

headers = (
    str(Model.select())
    .split("SELECT ")[1]
    .split(' FROM "model" AS "t1"')[0]
    .replace('"t1".', "")
    .replace('"', "")
    .split(", ")
)

values = []

for player in Model.select():
    inner = [eval("player.{}".format(header)) for header in headers]
    values.append(inner)

print(tabulate(values, headers=headers))

with open("db.html", "w") as f:
    f.write(tabulate(values, headers=headers, tablefmt="html"))
