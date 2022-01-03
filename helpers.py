from telegram import ChatAction

from functools import wraps
from time import sleep


def get_si(number, type="'", size=3):
    if number < 1:
        return "0"
    if type == "s":
        suf = {
            0: "",
            1: " k",
            2: " M",
            3: " G",
            4: " T",
            5: " P",
            6: " E",
            7: " Z",
            8: " Y",
            9: " A",
            10: " AA",
            11: " AAA",
            12: " stop",
        }
        exp = 0
        while number // 10 ** (exp * size):
            exp += 1
        exp -= 1
        return "{:.2f}".format(int(number / 10 ** (exp * size))).rstrip('0').rstrip('.') + "{}".format(suf[exp])
    elif type == "'":
        return "{:,}".format(int(number)).replace(",", "'")
    else:
        return number


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        sleep(len(update.effective_message.text) // 20)  # This is based on my max WPM hehe.
        return func(update, context, *args, **kwargs)

    return command_func