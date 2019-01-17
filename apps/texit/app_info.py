HELP_FILE = "apps/texit/help.txt"

with open(HELP_FILE, "r") as help_file:
    help_str = help_file.read()


def load_into(bot):
    info = {"dev_list": ["299175087389802496", "408905098312548362"],
            "info_str": "I am a high quality LaTeX rendering bot coded in discord.py.\nUse `{prefix}help` for information on how to use me, and `{prefix}list` to see all my commands!",
            "invite_link": "http://texit.paradoxical.pw",
            "donate_link": "https://www.patreon.com/texit",
            "support_guild": "https://discord.gg/YNQzcvH",
            "brief": True,
            "app": "texit",
            "help_str": help_str,
            "help_file": "resources/apps/texit/texit_thanks.png"}
    bot.objects.update(info)
