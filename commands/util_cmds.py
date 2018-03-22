from paraCH import paraCH
import discord
from datetime import datetime
from pytz import timezone

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
                 # "Usage: discrim [discriminator]\n\nSearches all guilds the bot is in for a user with the given discriminator.")
    async def prim_cmd_discrim(ctx):
         p = ctx.bot.get_all_members()
         found_members = set(filter(lambda m: m.discriminator.endswith(ctx.args), p))
         if len(found_members) == 0:
             await ctx.reply("No users with this discrim found!")
             return
         user_info = [ (str(m), "({})".format(m.id)) for m in found_members]
         max_len = len(max(list(zip(*user_info))[0],key=len))
         user_strs = [ "{0[0]:^{max_len}} {0[1]:^25}".format(user, max_len = max_len) for user in user_info]
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
        transactions[now]["amount"] = "{}{:.2f}".format(action, amount)
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
