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

    def __init__(self, ctx, action, mod, users, reason, timeout=0):
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


async def ban(ctx, user, reason, days):
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


@cmds.cmd("ban",
          category="Moderation",
          short_help="Bans users")
@cmds.execute("flags", flags=["r==", "p="])
async def cmd_ban(ctx):
    """
    Usage: {prefix}ban <user1> [user2] [user3]... [-r <reason>] [-p <days>]

    Bans the users listed with an optional reason.
    If -p is provided, purges <days> days of message history for each user.
    TODO: Emojis for ban messages
    TODO: Useful switch on permission errors etc
    TODO: Too many edits?
    TODO: When switching to rewrite, include reason in ban
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to ban!")
        return
    reason = ctx.flags["r"]
    purge_days = ctx.flags["p"]
    if not reason:
        reason = await ctx.input("Please provide a reason! (`no` for no reason or `c` to abort ban)")
        if reason.lower() == "no":
            reason = "None"
        elif reason.lower() == "c":
            await ctx.reply("Aborting!")
            return
        elif reason is None:
            await ctx.reply("Request timed out, aborting.")
            return
    if not purge_days:
        purge_days = "1"
    if not purge_days.isdigit():
        await ctx.reply("Number of days to purge must be a number!")
        return
    if int(purge_days) > 7:
        await ctx.reply("Number of days to burge must be less than 7")
        return
    bans = []
    msg = "Banning...\n"
    out_msg = await ctx.reply(msg)
    for userstr in ctx.params:
        old_msg = msg
        msg += "\t{}".format(userstr)
        await ctx.bot.edit_message(out_msg, msg)
        user = await ctx.find_user(userstr, in_server=True, interactive=True)
        if user is None:
            if ctx.cmd_err[0] != -1:
                msg = old_msg + "\tCouldn't find user `{}`, skipping\n".format(userstr)
            else:
                msg = old_msg + "\tUser selection aborted for `{}`, skipping\n".format(userstr)
                ctx.cmd_err = (0, "")
            await ctx.bot.edit_message(out_msg, msg)
            continue
        result = await ban(ctx, user, days=int(purge_days), reason=reason)
        if result == 0:
            msg = old_msg + "\tSuccessfully banned `{}`! ".format(user)
            bans.append(user)
        elif result == 1:
            msg = old_msg + "\tFailed to ban `{}`! (Insufficient Permissions) ".format(user.name)
        else:
            msg = old_msg + "\tEncountered an unexpected fatal error banning `{}`!Aborting ban sequence...".format(user.name)
            await ctx.bot.edit_message(out_msg, msg)
            break
        await ctx.bot.edit_message(out_msg, msg)
        """
        if purge_days:
            old_msg = msg
            msg += "\t Purging messages"
            await ctx.bot.edit_message(out_msg, msg)
            result = await purge(ctx, user, purge_days)
            if result == 0:
                msg = old_msg + "\t Purged `{}` hour{} of messages".format(str(purge_days),
                                                                           "s" if purge_days > 1 else "")
            else:
                msg = old_msg + "\t Failed to purge messages!"
            await ctx.bot.edit_message(out_msg, msg)
        """
        msg += "\n"
    if len(bans) == 0:
        return
    action = "ban" if len(bans) == 1 else "multi-ban"
    mod_event = ModEvent(ctx, action, ctx.author, bans, reason)
    result = await mod_event.modlog_post()
    if result == 1:
        await ctx.reply("I tried to post to the modlog, but lack the permissions!")  # TODO: Offer to repost after modlog works.
    elif result == 2:
        await ctx.reply("I can't see the set modlog channel!")
    elif result == 3:
        await ctx.reply("An unexpected error occurred while trying to post to the modlog.")


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
