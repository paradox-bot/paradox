from paraCH import paraCH
import discord
cmds = paraCH()

@cmds.cmd("shutdown",
          category="Bot admin")
@cmds.require("Master")
async def cmd_shutdown(ctx):
    await ctx.reply("Shutting down, cya another day~")
    await ctx.client.logout()


@cmds.cmd("setgame",
          category="Bot admin",
          short_help="Sets my playing status!")
          # "Usage: setgame <status>\
          # \n\nSets my playing status to <status>. The following keys may be used:\
          # \n\t$users$: Number of users I can see.\
          # \n\t$servers$: Number of servers I am in.\
          # \n\t$channels$: Number of channels I am in.")
@cmds.require("Master")
async def cmd_setgame(ctx):
    status = await ctx.para_format(ctx.arg_str)
    await ctx.client.change_presence(game=discord.Game(name=status))
    await ctx.reply("Game changed to: \'{}\'".format(status))
