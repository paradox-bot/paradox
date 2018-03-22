from paraCH import paraCH
import discord
from datetime import datetime
from pytz import timezone
import iso8601
import traceback


cmds = paraCH()


@cmds.cmd("echo",
          category="Utility",
          short_help="Sends what you tell me to!")
async def cmd_echo(ctx):
    """
    Usage: {prefix}echo <text>

    Replies to the message with <text>.
    """
    await ctx.reply(ctx.arg_str if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("secho",
          category="Utility",
          short_help="Like echo but deletes.")
async def cmd_secho(ctx):
    """
    Usage: {prefix}secho <text>

    Replies to the message with <text> and deletes your message.
    """
    try:
        await ctx.bot.delete_message(ctx.msg)
    except Exception:
        pass
    await ctx.reply(ctx.arg_str if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("userinfo",
          category="Utility",
          short_help="Shows the user's information")
@cmds.require("in_server")
@cmds.execute("user_lookup", in_server=True)
async def cmd_userinfo(ctx):
    """
    Usage: {prefix}userinfo (mention)

    Sends information on the mentioned user, or yourself if no one is provided.
    """
    if ctx.arg_str == "":
        user = ctx.author
    else:
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return

    bot_emoji = ctx.bot.objects["emoji_bot"]
    statusdict = {"offline": "Offline/Invisible",
                  "dnd": "Do Not Disturb",
                  "online": "Online",
                  "idle": "Idle/Away"}

    embed = discord.Embed(type="rich", color=(user.colour if user.colour.value else discord.Colour.light_grey()))
    embed.set_author(name="{user.name} ({user.id})".format(user=user), icon_url=user.avatar_url, url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name="Full name", value=("{} ".format(bot_emoji) if user.bot else "")+str(user), inline=False)

    game = "Playing {}".format(user.game if user.game else "nothing")
    embed.add_field(name="Status", value="{}, {}".format(statusdict[str(user.status)], game), inline=False)

    embed.add_field(name="Nickname", value=str(user.display_name), inline=False)

    shared = len(list(filter(lambda m: m.id == user.id, ctx.bot.get_all_members())))
    embed.add_field(name="Shared servers", value=str(shared), inline=False)

    joined_ago = ctx.strfdelta(datetime.utcnow()-user.joined_at)
    joined = user.joined_at.strftime("%-I:%M %p, %d/%m/%Y")
    created_ago = ctx.strfdelta(datetime.utcnow()-user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    embed.add_field(name="Joined at", value="{} ({} ago)".format(joined, joined_ago), inline=False)
    embed.add_field(name="Created at", value="{} ({} ago)".format(created, created_ago), inline=False)

    roles = [r.name for r in user.roles if r.name != "@everyone"]
    embed.add_field(name="Roles", value=('`' + '`, `'.join(roles) + '`'), inline=False)
    await ctx.reply(embed=embed)


@cmds.cmd("discrim",
          category="Utility",
          short_help="Searches for users with a given discrim")
async def prim_cmd_discrim(ctx):
    """
    Usage: {prefix}discrim [discriminator]

    Searches all guilds the bot is in for users matching the given discriminator.
    """
    p = ctx.bot.get_all_members()
    found_members = set(filter(lambda m: m.discriminator.endswith(ctx.args), p))
    if len(found_members) == 0:
        await ctx.reply("No users with this discrim found!")
        return
    user_info = [(str(m), "({})".format(m.id)) for m in found_members]
    max_len = len(max(list(zip(*user_info))[0], key=len))
    user_strs = ["{0[0]:^{max_len}} {0[1]:^25}".format(user, max_len=max_len) for user in user_info]
    await ctx.reply("```asciidoc\n= Users found =\n{}\n```".format('\n'.join(user_strs)))


@cmds.cmd("piggybank",
          category="Utility",
          short_help="Keep track of money added towards a goal.")
async def cmd_piggybank(ctx):
    """
    Usage: {prefix}piggybank [+|- <amount>] | [list [clear]] | [goal <amount>|none]

    [+|- <amount>]: Adds or removes an amount to your piggybank.
    [list [clear]]: Sends you a DM with your previous transactions or clears your history.
    [goal <amount>|none]: Sets your goal!
    Or with no arguments, lists your current amount and progress to the goal.
    """
    bank_amount = await ctx.data.users.get(ctx.authid, "piggybank_amount")
    transactions = await ctx.data.users.get(ctx.authid, "piggybank_history")
    goal = await ctx.data.users.get(ctx.authid, "piggybank_goal")
    bank_amount = bank_amount if bank_amount else 0
    transactions = transactions if transactions else {}
    goal = goal if goal else 0
    if ctx.arg_str == "":
        msg = "You have ${:.2f} in your piggybank!".format(bank_amount)
        if goal:
            msg += "\nYou have achieved {:.1%} of your goal (${:.2f})".format(bank_amount/goal, goal)
        await ctx.reply(msg)
        return
    elif (ctx.params[0] in ["+", "-"]) and len(ctx.params) == 2:
        action = ctx.params[0]
        now = datetime.utcnow().strftime('%s')
        try:
            amount = float(ctx.params[1].strip("$#"))
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        transactions[now] = {}
        transactions[now]["amount"] = "{}${:.2f}".format(action, amount)
        bank_amount += amount if action == "+" else -amount
        await ctx.data.users.set(ctx.authid, "piggybank_amount", bank_amount)
        await ctx.data.users.set(ctx.authid, "piggybank_history", transactions)
        msg = "${:.2f} has been {} your piggybank. You now have ${:.2f}!".format(amount,
                                                                                 "added to" if action == "+" else "removed from",
                                                                                 bank_amount)
        if goal:
            if bank_amount >= goal:
                msg += "\nYou have achieved your goal!"
            else:
                msg += "\nYou have now achieved {:.1%} of your goal (${:.2f}).".format(bank_amount/goal, goal)
        await ctx.reply(msg)
    elif (ctx.params[0] == "goal") and len(ctx.params) == 2:
        if ctx.params[1].lower() in ["none", "remove", "clear"]:
            await ctx.data.users.set(ctx.authid, "piggybank_goal", amount)
            await ctx.reply("Your goal has been cleared")
            return
        try:
            amount = float(ctx.params[1].strip("$#"))
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        await ctx.data.users.set(ctx.authid, "piggybank_goal", amount)
        await ctx.reply("Your goal has been set to ${}. ".format(amount))
    elif (ctx.params[0] == "list"):
        if len(transactions) == 0:
            await ctx.reply("No transactions to show! Start adding money to your piggy bank with `{}piggybank + <amount>`".format(ctx.used_prefix))
            return
        if (len(ctx.params) == 2) and (ctx.params[1] == "clear"):
            await ctx.data.users.set(ctx.authid, "piggybank_history", {})
            await ctx.reply("Your transaction history has been cleared!")
            return

        msg = "```\n"
        for trans in sorted(transactions):
            trans_time = datetime.utcfromtimestamp(int(trans))
            tz = await ctx.data.users.get(ctx.authid, "tz")
            if tz:
                try:
                    TZ = timezone(tz)
                except Exception:
                    pass
            else:
                TZ = timezone("UTC")
            timestr = '%-I:%M %p, %d/%m/%Y (%Z)'
            timestr = TZ.localize(trans_time).strftime(timestr)
            msg += "{}\t {:^10}\n".format(timestr, str(transactions[trans]["amount"]))
        await ctx.reply(msg + "```", dm=True)
    else:
        await ctx.reply("Usage: {}piggybank [+|- <amount>] | [list] | [goal <amount>|none]".format(ctx.used_prefix))


@cmds.cmd("set",
          category="User info",
          short_help="Shows or sets a user setting")
async def cmd_set(ctx):
    """
    "Usage: {prefix}set [settingname [value]]

    Sets <settingname> to <value>, shows the value of <settingname>, or lists your available settings.
    Temporary implementation, more is coming soon!
    """
    if ctx.arg_str == '':
        await ctx.reply("```timezone: Country/City, some short-hands are accepted, use ETC/+10 etc to set to GMT-10.```")
        return
    action = ctx.params[0]
    if action == "timezone":
        if len(ctx.params) == 1:
            tz = await ctx.data.users.get(ctx.authid, "tz")
            if tz:
                msg = "Your current timezone is `{}`".format(tz)
            else:
                msg = "You haven't set your timezone! Use `{prefix}set timezone <timezone>` to set it!".format(ctx.used_prefix)
            await ctx.reply(msg)
            return
        tz = ' '.join(ctx.params[1:])
        try:
            timezone(tz)
        except Exception:
            await ctx.reply("Unfortunately, I don't understand this timezone. More options will be available soon.")
            return
        await ctx.data.users.set(ctx.authid, "tz", tz)
        await ctx.reply("Your timezone has been set to `{}`".format(tz))

# User info commands


@cmds.cmd("time",
          category="User info",
          short_help="Shows the current time for a user")
@cmds.execute("user_lookup", in_server=True)
async def cmd_time(ctx):
    """
    Usage: {prefix}time [mention | id | partial name]

    Gives the time for the mentioned user or yourself.
    Requires the user to have set the usersetting "timezone".
    """
    if ctx.arg_str == "":
        user = ctx.author
    else:
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return
    user = user.id
    tz = await ctx.data.users.get(user, "tz")
    if not tz:
        if user == ctx.authid:
            await ctx.reply("You haven't set your timezone! Set it using \"{}set timezone <timezone>\"!".format(ctx.used_prefix))
        else:
            await ctx.reply("This user hasn't set their timezone. Ask them to set it using \"{}set timezone <timezone>\"!".format(ctx.used_prefix))
        return
    try:
        TZ = timezone(tz)
    except Exception:
        await ctx.reply("An invalid timezone was provided in the database. Aborting... \n **Error Code:** `ERR_OBSTRUCTED_DB`")
        trace = traceback.format_exc()
        await ctx.log(trace)
        return
    timestr = 'The current time for **{}** is **%-I:%M %p (%Z(%z))** on **%a, %d/%m/%Y**'\
        .format(ctx.server.get_member(user).display_name)
    timestr = TZ.localize(datetime.utcnow()).strftime(timestr)
#    timestr = iso8601.parse_date(datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
    await ctx.reply(timestr)


@cmds.cmd("profile",
          category="User info",
          short_help="Displays a user profile")
@cmds.execute("user_lookup", in_server=True)
async def cmd_profile(ctx):
    """
    Usage: {prefix}profile [mention]

    Displays the mentioned user's profile, or your own.
    """
    if ctx.arg_str == "":
        user = ctx.author
    else:
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return

    badge_dict = {"master_perm": "botowner",
                  "manager_perm": "botmanager"}
    badges = ""
    for badge in badge_dict:
        (code, msg) = await cmds.checks[badge](ctx)
        if code == 0:
            badge_emoj = ctx.bot.objects["emoji_"+badge_dict[badge]]
            if badge_emoj is not None:
                badges += str(badge_emoj) + " "

    created_ago = ctx.strfdelta(datetime.utcnow()-user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    rep = await ctx.data.users.get(user.id, "rep")
    embed = discord.Embed(type="rich", color=user.colour) \
        .set_author(name="{user} ({user.id})".format(user=user),
                    icon_url=user.avatar_url)
    if badges:
        embed.add_field(name="Badges", value=badges, inline=False)

    embed.add_field(name="Level",
                    value="(Coming Soon!)", inline=True) \
        .add_field(name="XP",
                   value="(Coming Soon!)", inline=True) \
        .add_field(name="Reputation",
                   value=rep, inline=True) \
        .add_field(name="Premium",
                   value="No", inline=True)
    tz = await ctx.data.users.get(user.id, "tz")
    if tz:
        try:
            TZ = timezone(tz)
        except Exception:
            await ctx.reply("An invalid timezone was provided in the database. Aborting... \n **Error Code:** `ERR_CORRUPTED_DB`")
            return
        timestr = '%-I:%M %p on %a, %d/%m/%Y'
        timestr = iso8601.parse_date(datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
        embed.add_field(name="Current Time", value="{}".format(timestr), inline=False)
    embed.add_field(name="Created at",
                    value="{} ({} ago)".format(created, created_ago), inline=False)
    await ctx.reply(embed=embed)
