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
