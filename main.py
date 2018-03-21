import discord

from botdata import BotData
from botconf import Conf
from serverconfig import serv_conf

from contextBot.Context import Context
from contextBot.Bot import Bot

# Global constants/ environment variables

CONF_FILE = "paradox.conf"
BOT_DATA_FILE = "botdata.db"


# Initialise

conf = Conf(CONF_FILE)
botdata = BotData(BOT_DATA_FILE)

PREFIX = conf.get("PREFIX")

bot = Bot(data=botdata,
          serv_conf=serv_conf,
          user_conf=None,
          bot_conf=conf,
          log_file="paralog.log")

"""
bot = Bot(data=botdata,
          prefixes=[conf.get("PREFIX")]
          log_file="paralog.log")
"""




bot.DEBUG = 1

bot.load("commands", "config", "events", "utils")

bot.objects["invite_link"] = "https://discordapp.com/api/oauth2/authorize?bot_id=401613224694251538&permissions=8&scope=bot"
bot.objects["support guild"] = "https://discord.gg/ECbUu8u"
bot.objects["sorted cats"] = ["General",
                              "Fun Stuff",
                              "User info",
                              "Server setup",
                              "Bot admin",
                              "Tex",
                              "Misc"]


# ----Discord event handling----


@bot.event
async def on_ready():
    GAME = conf.getStr("GAME")
    if GAME == "":
        GAME = "in $servers$ servers!"
    GAME = await Context(bot=bot).ctx_format(GAME)
    await bot.change_presence(status=discord.Status.online, game=discord.Game(name=GAME))
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("Logged into", len(bot.servers), "servers")

    bot.objects["emoji_tex_del"] = discord.utils.get(bot.get_all_emojis(), name='delete')
    bot.objects["emoji_tex_show"] = discord.utils.get(bot.get_all_emojis(), name='showtex')
    bot.objects["emoji_bot"] = discord.utils.get(bot.get_all_emojis(), name='parabot')


# ----End Discord event handling----

# ----Event loops----
# ----End event loops----


# ----Everything is defined, start the bot!----
bot.run(conf.get("TOKEN"))
