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
               "mute": "User Muted!",
               "softban": "User Softbanned!"}

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


async def ban(ctx, user, ban_reason="None", days=1):
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


async def purge(ctx, user, hours):
    pass


async def multi_mod_action(ctx, user_strs, action_func, strings, reason, *kwargs):
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
        result = await action_func(ctx, user, *kwargs)
        if result == 0:
            msg = old_msg + "\t{}".format(strings["success"].format(user=user))
            users.append(user)
        elif result == 1:
            msg = old_msg + "\t{}".format(strings["fail_perm"].format(user=user))
        else:
            msg = old_msg + "\t{}".format(strings["fail_unknown"].format(user=user))
            break
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


@cmds.cmd("ban",
          category="Moderation",
          short_help="Bans users")
@cmds.execute("flags", flags=["r==", "p="])
async def cmd_ban(ctx):
    """
    Usage: {prefix}ban <user1> [user2] [user3]... [-r <reason>] [-p <days>]

    Bans the users listed with an optional reason.
    If -p is provided, purges <days> days of message history for each user.
    """
    """
    TODO: Emojis for ban messages
    TODO: Useful switch on permission errors etc
    TODO: When switching to rewrite, include reason in ban
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to ban!")
        return
    reason = ctx.flags["r"]
    purge_days = ctx.flags["p"]
    if not reason:
        reason = await ctx.input("📋 Please provide a reason! (`no` for no reason or `c` to abort ban)")
        if reason.lower() == "no":
            reason = "None"
        elif reason.lower() == "c":
            await ctx.reply("📋 Aborting!")
            return
        elif reason is None:
            await ctx.reply("📋 Request timed out, aborting.")
            return
    if not purge_days:
        purge_days = "1"
    if not purge_days.isdigit():
        await ctx.reply("⚠ Number of days to purge must be a number!")
        return
    if int(purge_days) > 7:
        await ctx.reply("⚠ Number of days to purge must be less than 7")
        return
    strings = {"action_name": "ban",
               "action_multi_name": "multi-ban",
               "start": "Banning... \n",
               "success": "🔨 Successfully banned `{user.name}`!",
               "fail_perm": "🚨 Failed to ban `{user.name}`! (Insufficient Permissions)",
               "fail_unknown": "🚨 Encountered an unexpected fatal error banning `{user.name}`!Aborting ban sequence..."}
    await multi_mod_action(ctx, ctx.params, ban, strings, reason, days=int(purge_days), ban_reason="{}: {}".format(ctx.author, reason))


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


@cmds.cmd("softban",
          category="Moderation",
          short_help="Softbans a user to delete messages")
@cmds.execute("flags", flags=["r==", "p="])
async def cmd_softban(ctx):
    """
    Usage: {prefix}ban <user1> [user2] [user3]... [-r <reason>] [-p <days>]

    Bans the users listed with an optional reason.
    """
    pass
