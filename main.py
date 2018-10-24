import discord
import shutil
import os
from datetime import datetime

from botdata import BotData
from botconf import Conf

from contextBot.Context import Context
from contextBot.Bot import Bot

# Global constants/ environment variables

CONF_FILE = "paradox.conf"
BOT_DATA_FILE = "botdata.db"


# Initialise

conf = Conf(CONF_FILE)
botdata = BotData(BOT_DATA_FILE)

PREFIX = conf.get("PREFIX")

CHEAT_CH = "429507856908419074"
FEEDBACK_CH = "429514404418289684"
PREAMBLE_CH = "504225174799908864"
BOT_LOG_CH = "426655650706096129"

LOG_CHANNEL = "428159039831146506"

EMOJI_SERVER = "398694383089745920"


LOGFILE = "logs/paralog.log"
LOGFILE_LAST = "logs/paralog.last.log"


# Log file

if os.path.isfile(LOGFILE):
    if os.path.isfile(LOGFILE_LAST):
        shutil.move(LOGFILE_LAST, "logs/{}paralog.log".format(datetime.utcnow().strftime("%s")))
    shutil.move(LOGFILE, LOGFILE_LAST)


async def get_prefixes(ctx):
        """
        Returns a list of valid prefixes in this context.
        Currently just bot and server prefixes
        """
        prefix = 0
        prefix_conf = ctx.server_conf.guild_prefix
        if ctx.server:
            prefix = await prefix_conf.get(ctx)
        prefix = prefix if prefix else ctx.bot.prefix
        return [prefix]

bot = Bot(data=botdata,
          bot_conf=conf,
          prefix=PREFIX,
          prefix_func=get_prefixes,
          log_file="logs/paralog.log")

bot.DEBUG = 1


async def log(bot, logMessage):
    print(logMessage)
    with open(bot.LOGFILE, 'a+') as logfile:
        logfile.write(logMessage + "\n")
    ctx = Context(bot=bot)
    log_splits = await ctx.msg_split(logMessage, True)
    for log in log_splits:
        await bot.send_message(discord.utils.get(bot.get_all_channels(), id=LOG_CHANNEL), log)
Bot.log = log

# Loading and initial objects

bot.load("commands", "config", "events", "utils", ignore=["RCS", "__pycache__"])

bot.objects["invite_link"] = "http://invite.paradoxical.pw"
bot.objects["support guild"] = "https://discord.gg/ECbUu8u"
bot.objects["sorted cats"] = ["General",
                              "Fun Stuff",
                              "Social",
                              "Utility",
                              "User info",
                              "Moderation",
                              "Server Admin",
                              "Bot Admin",
                              "Maths",
                              "Misc"]

bot.objects["sorted_conf_pages"] = [("General", ["Guild settings"]),
                                    ("Manual Moderation", ["Moderation"]),
                                    ("Join/Leave Messages", ["Join message", "Leave message"])]

bot.objects["regions"] = {
        "brazil": "Brazil",
        "eu-central": "Central Europe",
        "hongkong": "Hong Kong",
        "japan": "Japan",
        "russia": "Russia",
        "singapore": "Singapore",
        "sydney": "Sydney",
        "us-central": "Central United States",
        "us-east": "Eastern United States",
        "us-south": "Southern United States",
        "us-west": "Western United States",
        "eu-west": "Western Europe",
        "vip-amsterdam": "Amsterdam (VIP)",
        "vip-us-east": "Eastern United States (VIP)"
    }

emojis = {"emoji_tex_del": "delete",
          "emoji_tex_show": "showtex",
          "emoji_tex_errors": "errors",
          "emoji_bot": "parabot",
          "emoji_botowner": "botowner",
          "emoji_botmanager": "botmanager",
          "emoji_online": "ParaOn",
          "emoji_idle": "ParaIdle",
          "emoji_dnd": "ParaDND",
          "emoji_offline": "ParaInvis",
          "emoji_next": "Next",
          "emoji_prev": "Previous"}

# ----Discord event handling----


def get_emoji(name):
    emojis = bot.get_server(id=EMOJI_SERVER).emojis
    return discord.utils.get(emojis, name=name)


@bot.event
async def on_ready():
    GAME = conf.getStr("GAME")
    if GAME == "":
        GAME = "in $servers$ servers!"
    bot.objects["GAME"] = GAME
    GAME = await Context(bot=bot).ctx_format(GAME)
    await bot.change_presence(status=discord.Status.online, game=discord.Game(name=GAME))
    bot.sync_log("Logged in as")
    bot.sync_log(bot.user.name)
    bot.sync_log(bot.user.id)
    bot.sync_log("Logged into {} servers".format(len(bot.servers)))

    ctx = Context(bot=bot)
    with open(LOGFILE, "r") as f:
        log_splits = await ctx.msg_split(f.read(), True)
        for log in log_splits:
            await bot.send_message(discord.utils.get(bot.get_all_channels(), id=LOG_CHANNEL), log)

    for emoji in emojis:
        bot.objects[emoji] = get_emoji(emojis[emoji])

    bot.objects["cheat_report_channel"] = discord.utils.get(bot.get_all_channels(), id=CHEAT_CH)
    bot.objects["feedback_channel"] = discord.utils.get(bot.get_all_channels(), id=FEEDBACK_CH)
    bot.objects["preamble_channel"] = discord.utils.get(bot.get_all_channels(), id=PREAMBLE_CH)
    bot.objects["server_change_log_channel"] = discord.utils.get(bot.get_all_channels(), id=BOT_LOG_CH)

# ----Event loops----
# ----End event loops----

# ----Everything is defined, start the bot!----
bot.run(conf.get("TOKEN"))
