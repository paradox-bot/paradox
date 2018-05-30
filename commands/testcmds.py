# from contextBot.CommandHandler import CommandHandler
from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("test", aliases=["testy", "tst"])
async def cmd_test(ctx):
    """
    Flags:3:
        -a:: blah
        -b:: blaefd
    """
    async def test(bot):
        await bot.log("test")
    await ctx.bot.schedule(await ctx.from_now(10), test, 0)
