#!/usr/bin/env python
from peewee import BigIntegerField, CharField, FloatField, IntegerField, Model, SqliteDatabase
from tabulate import tabulate


main_db = SqliteDatabase("./database.db")


class Players(Model):
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

    class Meta:
        database = main_db


main_db.connect()
main_db.create_tables([Players])

headers = (
    str(Players.select())
    .split("SELECT ")[1]
    .split(' FROM "players" AS "t1"')[0]
    .replace('"t1".', "")
    .replace('"', "")
    .split(", ")
)

values = []
for player in Players.select():
    inner = [eval("player.{}".format(header)) for header in headers]
    values.append(inner)

print(tabulate(values, headers=headers))

with open("db.html", "w") as f:
    f.write(tabulate(values, headers=headers, tablefmt="html"))
