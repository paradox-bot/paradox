from paraCH import paraCH
import discord
from datetime import datetime

cmds = paraCH()


class ModEvent:
    """
    TODO: Ticket numbers and stuff.
    """
    actions = {"ban": "User Banned!",
               "multi-ban": "Multiple-User Ban!",
               "kick": "User Kicked!",
               "multi-kick": "Users Kicked!",
               "unban": "User Unbanned",
               "multi-unban": "Users Unbanned",
               "mute": "User Muted!",
               "multi-mute": "Users Muted!",
               "unmute": "User unmuted!",
               "multi-unmute": "Users unmuted!",
               "softban": "User Softbanned!",
               "multi-softban": "Users Softbanned!"}

    def __init__(self, ctx, action, mod, users, reason="None", timeout=0):
        self.ctx = ctx
        self.action = action
        self.mod = mod
        self.users = users
        self.user_strs = [str(user) for user in users]
        self.timeout = timeout
        self.reason = reason
        self.init_time = datetime.utcnow()
        self.embed = None

    async def embedify(self):
        """
        TODO: timeout in sensible form
        """
        embed = discord.Embed(title=self.actions[self.action], color=discord.Colour.red())
        embed.add_field(name="User{}:".format("s" if len(self.users) > 1 else ""), value=", ".join(self.user_strs), inline=False)
        if self.timeout:
            embed.add_field(name="Expires:", value="{} hour{}".format(self.timeout, "s" if self.timeout > 1 else ""), inline=False)
        embed.add_field(name="Reason", value=self.reason, inline=False)
        embed.set_footer(icon_url=self.mod.avatar_url, text=self.init_time.strftime("Acting Moderator: {} at %-I:%M %p, %d/%m/%Y".format(self.mod)))
        self.embed = embed
        return embed

    async def modlog_post(self):
        """
        TODO: When channel is retrieved as a channel, some bits won't be required.
        """
        modlog = await self.ctx.server_conf.modlog_ch.get(self.ctx)
        if not modlog:
            return -1
        modlog = self.ctx.server.get_channel(modlog)
        if not modlog:
            return 2
        if not self.embed:
            await self.embedify()
        try:
            self.modlog_msg = await self.ctx.bot.send_message(modlog,  embed=self.embed)
        except discord.Forbidden:
            return 1
        except Exception:
            return 3
        return 0


async def ban(ctx, user, ban_reason="None", days=0):
    """
    Todo: on rewrite, make this post reason
    """
    try:
        await ctx.bot.ban(user, int(days))
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0


async def softban(ctx, user, ban_reason="None", days=1):
    """
    Todo: on rewrite, make this post reason
    """
    try:
        await ctx.bot.ban(user, int(days))
        await ctx.bot.unban(ctx.server, user)
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0


async def kick(ctx, user):
    try:
        await ctx.bot.kick(user)
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0


async def test_action(ctx, user, **kwargs):
    return 0


async def purge(ctx, user, hours):
    pass


async def multi_mod_action(ctx, user_strs, action_func, strings, reason, **kwargs):
    users = []
    msg = strings["start"]
    out_msg = await ctx.reply(msg)

    for user_str in user_strs:
        if user_str == "":
            continue
        old_msg = msg
        msg += "\t{}".format(user_str)
        await ctx.bot.edit_message(out_msg, msg)
        user = await ctx.find_user(user_str, in_server=True, interactive=True)
        if user is None:
            if ctx.cmd_err[0] != -1:
                msg = old_msg + "\t⚠ Couldn't find user `{}`, skipping\n".format(user_str)
            else:
                msg = old_msg + "\t🗑 User selection aborted for `{}`, skipping\n".format(user_str)
                ctx.cmd_err = (0, "")
            continue
        result = await action_func(ctx, user, **kwargs)
        if result in strings["results"]:
            msg = old_msg + "\t{}".format(strings["results"][result].format(user=user))
        else:
            msg = old_msg + "\t{}".format(strings["fail_unknown"].format(user=user))
            break
        if result == 0:
            users.append(user)
        msg += "\n"
    await ctx.bot.edit_message(out_msg, msg)
    if len(users) == 0:
        return
    action = strings["action_name"] if len(users) == 1 else strings["action_multi_name"]
    mod_event = ModEvent(ctx, action, ctx.author, users, reason)
    result = await mod_event.modlog_post()
    if result == 1:
        await ctx.reply("I tried to post to the modlog, but lack the permissions!")  # TODO: Offer to repost after modlog works.
    elif result == 2:
        await ctx.reply("I can't see the set modlog channel!")
    elif result == 3:
        await ctx.reply("An unexpected error occurred while trying to post to the modlog.")


async def request_reason(ctx):
    reason = await ctx.input("📋 Please provide a reason! (`no` for no reason or `c` to abort ban)")
    if reason.lower() == "no":
        reason = "None"
    elif reason.lower() == "c":
        await ctx.reply("📋 Aborting!")
        return None
    elif reason is None:
        await ctx.reply("📋 Request timed out, aborting.")
        return None
    return reason


@cmds.cmd("ban",
          category="Moderation",
          short_help="Bans users")
@cmds.execute("flags", flags=["r==", "p=", "f"])
@cmds.require("in_server")
@cmds.require("in_server_can_ban")
async def cmd_ban(ctx):
    """
    Usage: {prefix}ban <user1> [user2] [user3]... [-r <reason>] [-p <days>] [-f]

    Bans the users listed with an optional reason.
    If -p (purge) is provided, purges <days> days of message history for each user.
    If -f (fake) is provided, only pretends to ban.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to ban!")
        return
    reason = ctx.flags["r"]
    purge_days = ctx.flags["p"]
    action_func = test_action if ctx.flags["f"] else ban
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    if not purge_days:
        purge_days = "0"
    if not purge_days.isdigit():
        await ctx.reply("⚠ Number of days to purge must be a number!")
        return
    if int(purge_days) > 7:
        await ctx.reply("⚠ Number of days to purge must be less than 7")
        return
    strings = {"action_name": "ban",
               "action_multi_name": "multi-ban",
               "start": "Banning... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error banning `{user.name}`!Aborting ban sequence..."}
    strings["results"] = {0: "🔨 Successfully banned `{user.name}`" + (" and purged `{}` days of messages".format(purge_days) if int(purge_days) > 0 else "!"),
                          1: "🚨 Failed to ban `{user.name}`! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason, days=int(purge_days), ban_reason="{}: {}".format(ctx.author, reason))


@cmds.cmd("softban",
          category="Moderation",
          short_help="Softbans users")
@cmds.execute("flags", flags=["r==", "p=", "f"])
@cmds.require("in_server")
@cmds.require("in_server_can_softban")
async def cmd_softban(ctx):
    """
    Usage: {prefix}softban <user1> [user2] [user3]... [-r <reason>] [-p <days>] [-f]

    Softbans (bans and unbans) the users listed with an optional reason.
    If -p (purge) is provided, purges <days> days of message history for each user. Otherwise purges 1 day.
    If -f (fake) is provided, only pretends to softban.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to softban!")
        return
    reason = ctx.flags["r"]
    purge_days = ctx.flags["p"]
    action_func = test_action if ctx.flags["f"] else softban
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    if not purge_days:
        purge_days = "1"
    if not purge_days.isdigit():
        await ctx.reply("⚠ Number of days to purge must be a number!")
        return
    if int(purge_days) > 7:
        await ctx.reply("⚠ Number of days to purge must be less than 7")
        return
    strings = {"action_name": "softban",
               "action_multi_name": "multi-softban",
               "start": "Softbanning... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error softbanning `{user.name}`!Aborting ban sequence..."}
    strings["results"] = {0: "🔨 Softbanned `{user.name}`" + " and purged `{}` days of messages!".format(purge_days),
                          1: "🚨 Failed to softban `{user.name}`! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason, days=int(purge_days), ban_reason="{}: {}".format(ctx.author, reason))


@cmds.cmd("kick",
          category="Moderation",
          short_help="Kicks users")
@cmds.execute("flags", flags=["r==", "f"])
@cmds.require("in_server")
@cmds.require("in_server_can_kick")
async def cmd_kick(ctx):
    """
    Usage: {prefix}kick <user1> [user2] [user3]... [-r <reason>] [-f]

    Kicks the users listed with an optional reason.
    If -f (fake) is provided,  only pretends to kick.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to kick!")
        return
    reason = ctx.flags["r"]
    action_func = test_action if ctx.flags["f"] else kick
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    strings = {"action_name": "kick",
               "action_multi_name": "multi-kick",
               "start": "Kicking... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error kicking `{user.name}`! Aborting kick sequence..."}
    strings["results"] = {0: "🔨 Kicked `{user.name}`!",
                          1: "🚨 Failed to kick `{user.name}`! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason)


'''
@cmds.cmd("hackban",
          category="Moderation",
          short_help="Pre-bans users by id")
@cmds.execute("flags", flags=["r=="])
async def cmd_hackban(ctx):
    """
    Usage: {prefix}hackban <userid1> [userid2] [userid3]... [-r <reason>]

    Bans the user ids listed with an optional reason.
    """
    pass
'''
