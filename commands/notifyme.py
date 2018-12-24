from paraCH import paraCH
import discord
import asyncio
from datetime import datetime

cmds = paraCH()

skeleton = {"server": {"id": 0},
            "from": {"id": 0},
            "mentions": {"id": 0},
            "rolementions": {"id": 0},
            "contains": {"text": ""},
            "in": {"id": ""}}


def check_listen(user, checks, msg_ctx):
    result = True
    result = result and ("server" not in checks or msg_ctx.server.id == checks["server"]["id"])
    result = result and ("from" not in checks or msg_ctx.authid == checks["from"]["id"])
    result = result and ("mentions" not in checks or checks["mentions"]["id"] in msg_ctx.msg.raw_mentions)
    result = result and ("rolementions" not in checks or checks["mentions"]["id"] in msg_ctx.msg.raw_role_mentions)
    result = result and ("contains" not in checks or checks["contains"]["text"] in msg_ctx.msg.contents)
    result = result and ("in" not in checks or msg_ctx.ch.id == checks["in"]["id"])
    return result


@cmds.cmd("notifyme",
          category="Utility",
          short_help="Sends a DM when a message matching certain criteria are detected.",
          aliases=["tellme", "pounce", "listenfor"])
@cmds.execute("flags", flags=["remove", "interactive"])
async def cmd_notifyme(ctx):
    """
    Usage:
        {prefix}notifyme
        {prefix}notifyme [conditions]
        {prefix}notifyme --mentions me
        {prefix}notifyme --remove
    Description:
        Notifyme sends you a direct message whenever messages matching your criteria are detected.
        On its own, displays a list of current conditions.
        See Examples for examples of conditions.
        (WIP command, more soon)
    Flags:3
        --remove:: Displays a menu where you can select a check to remove.
        --delay:: Smart delay, i.e. on't notify you if you message soon afterwards.
        --mentions:: Requires the message to mention this user.
        --contains:: Requires message to contain this string.
        --here:: Requires message to be from this server.
        --from:: Requires message to be from this user.
        --rolementions:: Requires message to mention this role. (TBD)
        --in:: Requires message to be in this channel. (TBD)
    """

async def notify_user(user, ctx, check):
    pass

async def register_notifyme_listeners(bot):
    bot.objects["notifyme_listeners"] = {}
    active_listeners = await bot.data.users.find_not_empty("notifyme")
    notifyme_listeners = {}
    for listener in active_listeners:
        listener = str(listener)
        try:
            user = await bot.get_user_info(listener)
        except discord.NotFound
            continue
        if not user:
            continue
        check_list = await bot.data.users.get(listener, "notifyme")
        notifyme_listeners[listener] = {"user": user, "checks": check_list}
    bot.objects["notifyme_listeners"] = notifyme_listeners

async def fire_listeners(ctx):
    if not ctx.server:
        return
    listeners = ctx.bot.objects["notifyme_listeners"]
    active_in_server = [user.id for user in ctx.server.members if user.id in listeners]
    for userid in active_in_server:
        listener = listeners[userid]
        for check in listener["checks"]:
            if not check_listen(listener["checks"]["user"], check, ctx):
                continue
            asyncio.ensure_future(notify_user(listener["checks"]["user"], ctx, check))
