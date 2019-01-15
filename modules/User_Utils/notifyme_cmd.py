from paraCH import paraCH
import discord
import asyncio
from pytz import timezone

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
    result = result and ("rolementions" not in checks or checks["rolementions"]["id"] in msg_ctx.msg.raw_role_mentions)
    result = result and ("contains" not in checks or checks["contains"]["text"] in msg_ctx.msg.content)
    result = result and ("in" not in checks or msg_ctx.ch.id == checks["in"]["id"])
    result = result and ("notbot" not in checks or not msg_ctx.author.bot)
    return result


async def check_can_view(user, ctx):
    return ctx.ch.permissions_for(ctx.server.get_member(user.id)).read_messages


async def check_to_str(ctx, check, markdown=True):
    items = []
    if "server" in check:
        server = ctx.bot.get_server(check["server"]["id"])
        if not server:
            return "Invalid check"
        items.append("(Server {})".format(server.name))
    if "from" in check:
        items.append("(From {})".format(await ctx.bot.get_user_info(check["from"]["id"])))
    if "mentions" in check:
        items.append("(Mentions user {})".format(await ctx.bot.get_user_info(check["mentions"]["id"])))
    if "rolementions" in check:
        items.append("(Mentions role {})".format(discord.utils.get(server.roles, id=check["rolementions"]["id"])))
    if "contains" in check:
        items.append("(Contains \"{}\")".format(check["contains"]["text"]))
    if "in" in check:
        items.append("(Channel {})".format(discord.utils.get(ctx.bot.get_all_channels, id=check["in"]["id"])))
    if "notbot" in check:
        items.append("(Not a bot)")

    return (" **and** " if markdown else " and ").join(items)


@cmds.cmd("notifyme",
          category="Utility",
          short_help="DMs you messages matching given criteria.",
          aliases=["tellme", "pounce", "listenfor"])
@cmds.execute("flags", flags=["remove", "interactive", "delay", "mentions==", "contains==", "here", "from==", "rolementions==", "in==", "notbot"])
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
        --delay:: Smart delay, i.e. won't notify you if you message soon afterwards (TBD).
        --mentions:: Requires the message to mention this user.
        --contains:: Requires message to contain this string.
        --here:: Requires message to be from this server.
        --from:: Requires message to be from the specified user.
        --rolementions:: Requires message to mention the specified role.
        --notbot:: Requires the message not have been sent by a bot.
        --in:: Requires message to be in the specified channel. (TBD)
    """
    checks = await ctx.data.users.get(ctx.authid, "notifyme")
    checks = checks if checks else []

    if ctx.flags["remove"]:
        # Do interactive menu stuff
        if not checks:
            await ctx.reply("You haven't set any checks yet!")
        else:
            check_strs = []
            for check in checks:
                check_strs.append(await check_to_str(ctx, check, markdown=False))
            selected = await ctx.selector("Select a pounce to remove!", check_strs)
            if selected is None:
                return
            checks.remove(checks[selected])
            await update_checks(ctx, checks)
            await ctx.reply("The selected pounce has been removed!")
        return
    if ctx.flags["here"] or ctx.flags["in"] or ctx.flags["from"] or ctx.flags["rolementions"] or ctx.flags["mentions"]:
        if not ctx.server:
            await ctx.reply("You can only use these flags in a server!")
            return
    if not any([ctx.flags[flag] for flag in ctx.flags]):
        # Do print list stuff
        if not checks:
            await ctx.reply("You haven't set any checks yet!")
        else:
            check_strs = []
            for check in checks:
                check_strs.append(await check_to_str(ctx, check, markdown=False))
            await ctx.pager(ctx.paginate_list(check_strs, title="Current active pounces"))
        return

    # Do Construct new notify predicate stuff

    check = {}

    if ctx.flags["here"]:
        check["server"] = {"id": ctx.server.id}
    if ctx.flags["delay"]:
        check["delay"] = True
    if ctx.flags["mentions"]:
        if ctx.flags["mentions"] == "me":
            user = ctx.author
        else:
            user = await ctx.find_user(ctx.flags["mentions"], interactive=True, in_server=True)
            if not user:
                return
        check["mentions"] = {"id": user.id}
    if ctx.flags["from"]:
        if ctx.flags["from"] == "me":
            user = ctx.author
        else:
            user = await ctx.find_user(ctx.flags["from"], interactive=True)
            if not user:
                return
        check["from"] = {"id": user.id}
    if ctx.flags["rolementions"]:
        role = await ctx.find_role(ctx.flags["rolementions"], interactive=True)
        if not role:
            return
        check["rolementions"] = {"id": role.id}
        check["server"] = {"id": ctx.server.id}
    if ctx.flags["contains"]:
        check["contains"] = {"text": ctx.flags["contains"].strip("\"")}
    if ctx.flags["notbot"]:
        check["notbot"] = True

    # Add to check list, register, and save
    if check in checks:
        await ctx.reply("This check already exists!")
        return
    checks.append(check)
    await update_checks(ctx, checks)
    await ctx.reply("Added pounce!")


async def update_checks(ctx, checks):
    await ctx.data.users.set(ctx.authid, "notifyme", checks)
    listeners = ctx.bot.objects["notifyme_listeners"]
    listener = listeners[ctx.authid] if ctx.authid in listeners else {"user": ctx.author}
    listener["checks"] = checks
    listeners[ctx.authid] = listener


async def notify_user(user, ctx, check):
    await ctx.log("Notifying user {} with check {}".format(user, check))
    prior_msgs = [ctx.msg]
    async for msg in ctx.bot.logs_from(ctx.ch, limit=5, before=ctx.msg):
        prior_msgs.append(msg)
    tz = await ctx.data.users.get(user.id, "tz")
    TZ = timezone(tz) if tz else None

    msg_lines = "\n".join([ctx.msg_string(msg, mask_link=False, line_break=False, tz=TZ) for msg in reversed(prior_msgs)])
    jump_link = ctx.msg_jumpto(ctx.msg)
    message = "**__Pounce fired__** by **{}** in channel **{}** of **{}**\nJump link: {}\n\n{}".format(ctx.msg.author, ctx.ch.name, ctx.server.name, jump_link, msg_lines)
    await ctx.send(user, message=message)


async def register_notifyme_listeners(bot):
    bot.objects["notifyme_listeners"] = {}
    active_listeners = await bot.data.users.find_not_empty("notifyme")
    notifyme_listeners = {}
    for listener in active_listeners:
        listener = str(listener)
        try:
            user = await bot.get_user_info(listener)
        except discord.NotFound:
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
            if not check_listen(listener["user"], check, ctx):
                continue
            if not await check_can_view(listener["user"], ctx):
                continue
            if ctx.author.id in [listener["user"].id, ctx.me.id]:
                continue
            asyncio.ensure_future(notify_user(listener["user"], ctx, check))
            break


def load_into(bot):
    bot.data.users.ensure_exists("notifyme", shared=False)

    bot.add_after_event("ready", register_notifyme_listeners)
    bot.after_ctx_message(fire_listeners)
