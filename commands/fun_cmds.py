from paraCH import paraCH
import discord
import aiohttp
import asyncio
from datetime import datetime, timedelta
from NumericStringParser import NumericStringParser
import urllib
import random

cmds = paraCH()


@cmds.cmd("bin2ascii",
          category="Fun stuff",
          short_help="Converts binary to ascii",
          aliases=["bin2a", "binarytoascii"])
async def cmd_bin2ascii(ctx):
    """
    Usage:
        {prefix}bin2ascii <binary string>
    Description:
        Converts the provided binary string into ascii, then sends the output.
    Examples:
        {prefix}bin2ascii 01001000 01101001 00100001
    """
    # Would be cool if example could use username
    bitstr = ctx.arg_str.replace(' ', '')
    if (not bitstr.isdigit()) or (len(bitstr) % 8 != 0):
        await ctx.reply("Not a valid binary string!")
        return
    bytelist = map(''.join, zip(*[iter(bitstr)] * 8))
    asciilist = [chr(sum([int(b) << 7 - n for (n, b) in enumerate(byte)])) for byte in bytelist]
    await ctx.reply("Output: `{}`".format(''.join(asciilist)))

@cmds.cmd("calc",
          category="Fun stuff",
          short_help="Calculator!")
async def cmd_calc(ctx):
    """
    Usage:
        {prefix}calc <what you want to calculate>
    Description:
        Calculates the given expression and returns the answer
    Examples:
        {prefix}calc 1+1
    """
    if not ctx.params[0]:
        await ctx.reply("Please give me something to calculate!")
        return
    to_calc = ctx.arg_str.replace("`", "")
    nsp = NumericStringParser()
    response = nsp.eval(to_calc)
    if response:
        await ctx.reply("Answer: `{}`".format(response))
    else:
        await ctx.reply("Something went wrong calculating your expression! Please check your input and try again.")

@cmds.cmd("image",
          category="Fun Stuff",
          short_help="Searches images for the specified text",
          aliases=["imagesearch", "images"])
async def cmd_image(ctx):
    """
    Usage:
        {prefix}image <image text>
    Description:
        Replies with a random image matching the search description.
    """
    API_KEY = "10259038-12ef42751915ae10017141c86"
    if not ctx.arg_str:
        await ctx.reply("Please enter something to search for")
        return
    search_for = urllib.parse.quote_plus(ctx.arg_str)
    async with aiohttp.get('https://pixabay.com/api/?key={}&q={}&image_type=photo'.format(API_KEY, search_for)) as r:
        if r.status == 200:
            js = await r.json()
            hits = js['hits'] if 'hits' in js else None
            if not hits:
                await ctx.reply("Didn't get any results for this query!")
                return
            hit_pages = []
            for hit in [random.choice(hits) for i in range(20)]:
                embed = discord.Embed(title="Here you go!", color=discord.Colour.light_grey())
                if "webformatURL" in hit:
                    embed.set_image(url=hit["webformatURL"])
                else:
                    continue
                embed.set_footer(text="Images thanks to the free https://pixabay.com API!")
                hit_pages.append(embed)
            await ctx.pager(hit_pages, embed=True)
        else:
            await ctx.reply("Something went wrong with your search, sorry!")
            return

@cmds.cmd("lenny",
          category="Fun stuff",
          short_help="( ͡° ͜ʖ ͡°)")
async def cmd_lenny(ctx):
    """
    Usage:
        {prefix}lenny
    Description:
        Sends lenny ( ͡° ͜ʖ ͡°).
    """
    try:
        await ctx.bot.delete_message(ctx.msg)
    except discord.Forbidden:
        pass
    await ctx.reply("( ͡° ͜ʖ ͡°)")


@cmds.cmd("dog",
          category="Fun Stuff",
          short_help="Sends a random dog image",
          aliases=["doge", "pupper", "doggo", "woof"])
async def cmd_dog(ctx):
    """
    Usage:
        {prefix}dog
    Description:
        Replies with a random dog image!
    """
    async with aiohttp.get('http://random.dog/woof') as r:
        if r.status == 200:
            dog = await r.text()
            if not (dog.endswith("png") or dog.endswith("jpg") or dog.endswith("gif")):
                await cmd_dog(ctx)
                return
            embed = discord.Embed(title="Woof!", description="[Click to view image]({})".format("https://random.dog/"+dog), color=discord.Colour.light_grey())
            embed.set_image(url="https://random.dog/"+dog)
            await ctx.reply(embed=embed)


@cmds.cmd("duck",
          category="Fun Stuff",
          short_help="Sends a random duck image",
          aliases=["quack"])
@cmds.execute("flags", flags=["g"])
async def cmd_duck(ctx):
    """
    Usage:
        {prefix}duck
    Description:
        Replies with a random duck image!
    Flags:2
        -g:: Forces a gif
    """
    img_type = "gif" if ctx.flags["g"] else random.choice(["gif", "jpg"])
    async with aiohttp.get('http://random-d.uk/api/v1/quack?type={}'.format(img_type)) as r:
        if r.status == 200:
            js = await r.json()
            embed = discord.Embed(title="Quack!", description="[Click to view image]({})".format(js['url']), color=discord.Colour.light_grey())
            embed.set_image(url=js['url'])
            try:
                await ctx.reply(embed=embed)
                return
            except Exception:
                pass
        else:
            await ctx.reply("The ducks are too powerful right now! Please try again later.")


@cmds.cmd("sorry",
          category="Fun Stuff",
          short_help="Sorry, love.")
async def cmd_sorry(ctx):

   embed = discord.Embed(color=discord.Colour.purple())
   embed.set_image(url="https://cdn.discordapp.com/attachments/309625872665542658/406040395462737921/image.png")
   await ctx.reply(embed=embed)

@cmds.cmd("cat",
          category="Fun Stuff",
          short_help="Sends a random cat image",
          aliases=["meow", "purr", "pussy"])
async def cmd_cat(ctx, recursion=0):
    """
    Usage:
        {prefix}cat
    Description:
        Replies with a random cat image!
    """
    async with aiohttp.get('http://aws.random.cat/meow') as r:
        if r.status == 200:
            js = await r.json()
            embed = discord.Embed(description="[Meow!]({})".format(js=['file']), color=discord.Colour.light_grey())
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
        await ctx.reply("Sorry! The cats are too powerful right now. Please try again later!")


@cmds.cmd("rep",
          category="Fun stuff",
          short_help="Give reputation to a user")
async def cmd_rep(ctx):
    """
    Usage:
        {prefix}rep [mention]
        {prefix}rep stats
    Description:
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
