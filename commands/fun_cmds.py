from paraCH import paraCH
import discord
import aiohttp
from datetime import datetime
from pytz import timezone
cmds = paraCH()

@cmds.cmd("lenny",
          category="Fun stuff",
          short_help="( ͡° ͜ʖ ͡°)")
async def cmd_lenny(ctx):
    """
    Usage: {prefix}lenny

    Sends lenny ( ͡° ͜ʖ ͡°).
    """
    await ctx.bot.delete_message(ctx.message)
    await ctx.reply('( ͡° ͜ʖ ͡°)')

@cmds.cmd("dog",
          category="Fun Stuff",
          short_help="Sends a random dog image")
async def cmd_dog(ctx):
    """
    Usage: {prefix}dog

    Replies with a random dog image!
    """
    async with aiohttp.get('http://random.dog/woof') as r:
        if r.status == 200:
            dog = await r.text()
            if not (dog.endswith("png") or dog.endswith("jpg") or dog.endswith("gif")):
                await cmd_dog(ctx)
                return
            embed = discord.Embed(title="Woof!", color=discord.Colour.light_grey())
            embed.set_image(url="https://random.dog/"+dog)
            await ctx.reply(embed=embed)

@cmds.cmd("cat",
          category="Fun Stuff",
          short_help="Sends a random cat image")
async def cmd_cat(ctx):
    """
    Usage: {prefix}cat

    Replies with a random cat image!
    """
    async with aiohttp.get('http://aws.random.cat/meow') as r:
        if r.status == 200:
            js = await r.json()
            embed = discord.Embed(title="Meow!", color=discord.Colour.light_grey())
            embed.set_image(url=js['file'])
            await ctx.reply(embed=embed)


@cmds.cmd("piggybank",
          category="Fun Stuff",
          short_help="Keep track of money added towards a goal.")
async def cmd_piggybank(ctx):
    """
    Usage: {prefix}piggybank [+|- <amount>] | [list] | [goal <amount>]

    [+|- <amount>]: Adds or removes an amount to your piggybank.
    [list]: Sends you a DM with your previous transactions.
    [goal <amount>]: Sets your goal!
    Or with no arguments, lists your current amount and progress to the goal.
    """
    bank_amount = await ctx.data.users.get(ctx.authid, "piggybank_amount")
    transactions = await ctx.data.users.get(ctx.authid, "piggybank_history")
    goal = await ctx.data.users.get(ctx.authid, "piggybank_goal")
    bank_amount = bank_amount if bank_amount else 0
    transactions = transactions if transactions else {}
    goal = goal if goal else 0
    if ctx.arg_str == "":
        msg = "You have ${} in your piggybank!".format(bank_amount)
        if goal:
            msg += "\nYou have achieved {:.1%} of your goal (${:.2})".format(bank_amount/goal, goal)
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
        transactions[now]["amount"] = action + str(amount)
        bank_amount += amount if action == "+" else -amount
        await ctx.data.users.set(ctx.authid, "piggybank_amount", bank_amount)
        await ctx.data.users.set(ctx.authid, "piggybank_history", transactions)
            msg = "${:.2} has been {:.2} your piggybank. You now have ${:.2}!".format(amount,
                                                                         "added to" if action == "+" else "removed from",
                                                                         bank_amount)
        if goal:
            if bank_amount >= goal:
                msg += "\nYou have chieved your goal! Congratulations!"
            else:
                msg += "\nYou have now achieved {:.1%} of your goal (${:.2}).".format(bank_amount/goal, goal)
        await ctx.reply(msg)
    elif (ctx.params[0] == "goal") and len(ctx.params) == 2:
        try:
            amount = float(ctx.params[1].strip("$#"))
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        await ctx.data.users.set(ctx.authid, "piggybank_goal", amount)
        await ctx.reply("Your goal has been set! Good luck")
    elif (ctx.params[0] == "list"):
        await ctx.reply("In progress", dm=True)
        if len(transactions) == 0:
            await ctx.reply("No transactions to show! Start adding money to your piggy bank with `{}piggybank + <amount>`".format(ctx.used_prefix))
            return
        msg = "```\n"
        for trans in sorted(transactions):
            trans_time = datetime.utcfromtimestamp(int(trans))
            tz = botdata.users.get(user.id, "tz")
            if tz:
                try:
                    TZ = timezone(tz)
                except Exception:
                    pass
            else:
                TZ = timezone("UTC")
            timestr = '%-I:%M %p, %d/%m/%Y (%Z)'
            timestr = trans_time.astimezone(TZ).strftime(timestr)

            msg += "{}\t {:^10}\n".format(timestr, transactions[trans][amount])


    else:
        await ctx.reply("Usage: {}piggybank [+|- <amount>] | [list] | [goal <amount>]".format(ctx.used_prefix))
