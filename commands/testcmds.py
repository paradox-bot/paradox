from contextBot.CommandHandler import CommandHandler

cmds = CommandHandler()


@cmds.cmd("test")
async def cmd_test(ctx):
    await ctx.reply("hello")
