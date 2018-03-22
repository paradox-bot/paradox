from paraCH import paraCH
import discord
import aiohttp
import datetime
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
    Usage: {prefix}piggybank [+|- <amount>]

    Adds or removes an amount to your piggybank, or lists your current value.
    """
    bank_amount = await ctx.data.users.get("piggybank_amount")
    transactions = await ctx.data.users.get("piggybank_history")
    bank_amount = bank_amount if bank_amount else 0
    transactions = transactions if transactions else {}
    if ctx.arg_str == "":
        await ctx.reply("You have {} in your piggybank!".format(bank_amount))
        return
    elif (ctx.params[0] in ["+", "-"]) and len(ctx.params) == 2:
        action = ctx.params[0]
        now = datetime.utcnow().strftime('%s')
        try:
            amount = float(ctx.params[1])
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        transactions[now] = {}
        transactions[now]["amount"] = action + str(amount)
        bank_amount += amount if action == "+" else -amount
        await ctx.data.users.set("piggybank_amount", bank_amount)
        await ctx.data.users.set("piggybank_history", transactions)
        await ctx.reply("{} has been {} your piggybank. You now have {}!".format(amount,
                                                                                 "added to" if action == "+" else "removed from",
                                                                                 bank_amount))
    else:
        await ctx.reply("Usage: {}piggybank [+|- <amount>]".format(ctx.used_prefix))
