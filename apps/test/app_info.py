HELP_FILE = "apps/test/help.txt"

with open(HELP_FILE, "r") as help_file:
    help_str = help_file.read()

def load_into(bot):
    info = {"dev_list": ["299175087389802496", "408905098312548362"],
            "info_str": "Paradox test configuration.\nUse `{prefix}help` for information on how to use me, and `{prefix}list` to see all my commands!",
            "invite_link": "http://texit.paradoxical.pw",
            "donate_link": "https://www.patreon.com/texit",
            "support_guild": "https://discord.gg/YNQzcvH",
            "brief": False,
            "app": "test",
            "help_str": help_str}
    bot.objects.update(info)
