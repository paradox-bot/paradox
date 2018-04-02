from paraCH import paraCH
import discord
import aiohttp
import asyncio
from datetime import datetime, timedelta

cmds = paraCH()


@cmds.cmd("lenny",
          category="Fun stuff",
          short_help="( ͡° ͜ʖ ͡°)")
async def cmd_lenny(ctx):
    """
    Usage: {prefix}lenny

    Sends lenny ( ͡° ͜ʖ ͡°).
    """
    try:
        await ctx.bot.delete_message(ctx.msg)
    except discord.Forbidden:
        pass
    await ctx.reply("( ͡° ͜ʖ ͡°)")


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
async def cmd_cat(ctx, recursion=0):
    """
    Usage: {prefix}cat

    Replies with a random cat image!
    """
    async with aiohttp.get('http://aws.random.cat/meow') as r:
        if r.status == 200:
            js = await r.json()
            embed = discord.Embed(title="Meow!", color=discord.Colour.light_grey())
            embed.set_image(url=js['file'])
            try:
                await ctx.reply(embed=embed)
                return
            except Exception:
                pass
        else:
            if recursion < 10:
                asyncio.sleep(1)
                await cmd_cat(ctx, recursion=recursion+1)
                return
        await ctx.reply("Sorry! The cats are too poweful right now. Please try again later!")


@cmds.cmd("rep",
          category="Fun stuff",
          short_help="Give reputation to a user")
async def cmd_rep(ctx):
    """
    Usage: {prefix}rep [mention] | rep stats

    Gives a reputation point to the mentioned user or shows your current reputation cooldown timer.
    With stats, shows how many times you have repped and your last rep time.
    """
    cooldown = 24*60*60
    now = datetime.utcnow()
    now_timestamp = int(now.strftime('%s'))
    last_rep = await ctx.data.users.get(ctx.authid, "last_rep_time")

    if ctx.arg_str == "" or ctx.arg_str.strip() == "stats":
        if last_rep is None:
            await ctx.reply("You have not yet given any reputation!\nStart giving reputation using `rep <user>`!")
            return
        last_rep = int(last_rep)
        given_ago = now_timestamp - last_rep
        if ctx.arg_str == "":
            can_give_in = cooldown - given_ago
            if can_give_in > 0:
                can_give_str = ctx.strfdelta(timedelta(seconds=can_give_in), sec=True)
                msg = "You may give reputation in {}.".format(can_give_str)
            else:
                msg = "You may now give reputation!"
        else:
            given_rep = await ctx.data.users.get(ctx.authid, "given_rep")
            last_rep_str = ctx.strfdelta(timedelta(seconds=given_ago))
            msg = "You have given **{}** reputation point{}! You last gave a reputation point **{}** ago.".format(given_rep, "s" if int(given_rep) > 1 else "", last_rep_str)
        await ctx.reply(msg)
        return
    else:
        user = await ctx.find_user(ctx.arg_str, in_server=True, interactive=True)
        if ctx.cmd_err[0] == -1:
            return
        if not user:
            await ctx.reply("I couldn't find that user in this server sorry.")
            return
        if user == ctx.author:
            await ctx.reply("You can't give yourself reputation!")
            return
        if user == ctx.me:
            await ctx.reply("Aww thanks!")
        elif user.bot:
            await ctx.reply("Bots don't need reputation points!")
            return
        if last_rep is not None:
            given_ago = now_timestamp - int(last_rep)
            if given_ago < cooldown:
                msg = "Cool down! You may give reputation in {}.".format(ctx.strfdelta(timedelta(seconds=(cooldown - given_ago)), sec=True))
                await ctx.reply(msg)
                return
        rep = await ctx.data.users.get(user.id, "rep")
        rep = int(rep) + 1 if rep else 1
        await ctx.data.users.set(user.id, "rep", str(rep))
        given_rep = await ctx.data.users.get(ctx.authid, "given_rep")
        given_rep = int(given_rep) + 1 if given_rep else 1
        await ctx.data.users.set(ctx.authid, "given_rep", str(given_rep))
        await ctx.data.users.set(ctx.authid, "last_rep_time", str(now.strftime('%s')))
        await ctx.reply("You have given a reputation point to {}".format(user.mention))
