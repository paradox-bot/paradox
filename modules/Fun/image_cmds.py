from paraCH import paraCH
import discord
import aiohttp
import asyncio
from datetime import datetime, timedelta
import urllib
import random

cmds = paraCH()

# Provides cat, duck, dog, image


@cmds.cmd("image",
          category="Fun",
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


@cmds.cmd("dog",
          category="Fun",
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
            embed = discord.Embed(description="[Woof!]({})".format("https://random.dog/"+dog), color=discord.Colour.light_grey())
            embed.set_image(url="https://random.dog/"+dog)
            await ctx.reply(embed=embed)


@cmds.cmd("duck",
          category="Fun",
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
            embed = discord.Embed(description="[Quack!]({})".format(js['url']), color=discord.Colour.light_grey())
            embed.set_image(url=js['url'])
            try:
                await ctx.reply(embed=embed)
                return
            except Exception:
                pass
        else:
            await ctx.reply("The ducks are too powerful right now! Please try again later.")


@cmds.cmd("cat",
          category="Fun",
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
            embed = discord.Embed(description="[Meow!]({})".format(js['file']), color=discord.Colour.light_grey())
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
