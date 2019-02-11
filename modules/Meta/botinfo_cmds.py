import platform
import sys
from datetime import datetime

import discord
import psutil
from paraCH import paraCH

cmds = paraCH()

# Provides about, ping, invite, support, donators


@cmds.cmd("about", category="Meta", short_help="Provides information about the bot.")
async def cmd_about(ctx):
    """
    Usage:
        {prefix}about
    Description:
        Sends a message containing information about the bot.
    """
    current_devs = ctx.bot.objects["dev_list"]
    current_devnames = ', '.join(
        [str(discord.utils.get(ctx.bot.get_all_members(), id=str(devs))) for devs in current_devs])
    pform = platform.platform()
    py_vers = sys.version.split("\n")[0]
    mem = psutil.virtual_memory()
    mem_str = "{0:.2f}GB used out of {1:.2f}GB ({mem.percent}\%)".format(
        mem.used / (1024**3), mem.total / (1024**3), mem=mem)
    cpu_usage_str = "{}\%".format(psutil.cpu_percent())
    info = ctx.bot.objects["info_str"].format(prefix=ctx.used_prefix)
    links = "[Support Server]({sprt}), [Invite Me]({invite}), [Help keep me running!]({donate})".format(
        sprt=ctx.bot.objects["support_guild"],
        invite=ctx.bot.objects["invite_link"],
        donate=ctx.bot.objects["donate_link"])
    api_vers = "{} ({})".format(discord.__version__, discord.version_info[3])
    commands = len(set(cmd.name for cmd in ctx.bot.handlers[0].cmds.values()))
    servers = len(ctx.bot.servers)
    members = len(list(ctx.bot.get_all_members()))

    fields = [
        "Developers", "Servers", "Members", "Commands", "Memory", "CPU Usage", "API version", "Python version",
        "Platform"
    ]
    values = [current_devnames, servers, members, commands, mem_str, cpu_usage_str, api_vers, py_vers, pform]
    desc = "{}\n{}\n{}".format(info, ctx.prop_tabulate(fields, values), links)
    embed = discord.Embed(title="About Me", color=discord.Colour.red(), description=desc)
    await ctx.reply(embed=embed)
    # Uptime as well, of system and bot
    # Commands used? Or that goes in stats


@cmds.cmd("ping", category="Meta", short_help="Checks the bot's latency", aliases=["pong"])
async def cmd_ping(ctx):
    """
    Usage:
        {prefix}ping
    Description:
        Check how long it takes me to edit a message.
    """
    msg = await ctx.reply("Beep")
    msg_tstamp = msg.timestamp
    emsg = await ctx.bot.edit_message(msg, "Boop")
    emsg_tstamp = emsg.edited_timestamp
    latency = ((emsg_tstamp - msg_tstamp).microseconds) // 1000
    await ctx.bot.edit_message(msg, "Ping: {}ms".format(str(latency)))


@cmds.cmd("invite", category="Meta", short_help="Sends the bot's invite link", aliases=["inv"])
async def cmd_invite(ctx):
    """
    Usage:
        {prefix}invite
    Description:
        Replies with a link to invite me to your server.
    """
    await ctx.reply("Visit <{}> to invite me!".format(ctx.bot.objects["invite_link"]))


@cmds.cmd("support", category="Meta", short_help="Sends the link to the bot guild")
async def cmd_support(ctx):
    """
    Usage:
        {prefix}support
    Description:
        Sends the invite link to the my support guild.
    """
    await ctx.reply("Join my server at <{}>".format(ctx.bot.objects["support_guild"]))
