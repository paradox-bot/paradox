# from contextBot.CommandHandler import CommandHandler
from paraCH import paraCH
import asyncio

cmds = paraCH()


@cmds.cmd("test", aliases=["testy", "tst"])
async def cmd_test(ctx):
    """
    Flags:3:
        -a:: blah
        -b:: blaefd
    """
    async def for_edits():
        await ctx.reply("Listening for edits")
        (before, after) = await ctx.bot.wait_for_message_edit(message=ctx.msg, timeout=300, check=lambda before, after: True)
        await ctx.reply("Got edit!\nBefore: `{}`\nAfter: `{}`".format(before.content, after.content))

    async def for_reactions():
        out_msg = await ctx.reply("Listening for reactions on this message")
        res = await ctx.bot.wait_for_reaction(message=out_msg, timeout=300)
        await ctx.reply("Got reaction: {}".format(res.reaction.emoji))
    asyncio.ensure_future(for_edits(), loop = ctx.bot.loop)
    asyncio.ensure_future(for_reactions(), loop = ctx.bot.loop)
