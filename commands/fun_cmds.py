from paraCH import paraCH
import discord
import aiohttp
cmds = paraCH()

@cmds.cmd("lenny",
          category="Fun stuff",
          short_help="( ͡° ͜ʖ ͡°)")
         # "Usage: lenny\n\nSends lenny ( ͡° ͜ʖ ͡°)")
async def cmd_lenny(ctx):
    await ctx.client.delete_message(ctx.message)
    await ctx.reply('( ͡° ͜ʖ ͡°)')

@cmds.cmd("dog",
          category="Fun stuff",
          short_help="Sends a random dog image")
         # "Usage dog\
         # \n\nReplies with a random dog image!")
async def cmd_dog(ctx):
    async with aiohttp.get('http://random.dog/woof') as r:
        if r.status == 200:
            dog = await r.text()
            embed = discord.Embed(title="Woof!", color=discord.Colour.light_grey())
            embed.set_image(url="https://random.dog/"+dog)
            await ctx.reply(embed=embed)

@cmds.cmdd("cat",
           category="Fun stuff",
          short_help="Sends a random cat image")
          #"Usage cat\
          #\n\nReplies with a random cat image!")
async def cmd_cat(ctx):
    async with aiohttp.get('http://random.cat/meow') as r:
        if r.status == 200:
            js = await r.json()
            embed = discord.Embed(title="Meow!", color=discord.Colour.light_grey())
            embed.set_image(url=js['file'])
            await ctx.reply(embed=embed)
