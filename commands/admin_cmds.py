from paraCH import paraCH
import discord
cmds = paraCH()

@cmds.cmd("shutdown",
          category="Bot admin")
@cmds.require("Master")
async def cmd_shutdown(ctx):
    await ctx.reply("Shutting down, cya another day~")
    await ctx.bot.logout()


@cmds.cmd("setgame",
          category="Bot admin",
          short_help="Sets my playing status!")
@cmds.require("Master")
async def cmd_setgame(ctx):
    """
    Usage: {prefix}setgame <status>

    Sets my playing status to <status>, The following expansions are made:
        $users$: Number of users I can see.
        $servers$: Number of servers I am in.
        $channels$: Number of channels I am in.
    """
    status = await ctx.ctx_format(ctx.arg_str)
    await ctx.bot.change_presence(game=discord.Game(name=status))
    await ctx.reply("Game changed to: \'{}\'".format(status))
