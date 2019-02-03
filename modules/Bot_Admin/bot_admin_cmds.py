from paraCH import paraCH
import discord
import aiohttp

cmds = paraCH()

# Provides shutdown, setinfo, logs, dm

status_dict = {"online": discord.Status.online,
               "offline": discord.Status.offline,
               "idle": discord.Status.idle,
               "dnd": discord.Status.dnd,
               "invisible": discord.Status.invisible}

@cmds.cmd("shutdown",
          category="Bot admin")
@cmds.require("master_perm")
async def cmd_shutdown(ctx):
    await ctx.reply("Shutting down, cya another day~")
    await ctx.bot.logout()


@cmds.cmd("setinfo",
          category="Bot admin",
          short_help="Set my game, avatar, and status",
          aliases=["status", "setgame", "setstatus"])
@cmds.execute("flags", flags=["game==", "avatar==", "status="])
@cmds.require("master_perm")
async def cmd_setgame(ctx):
    """
    Usage:
        {prefix}setinfo --game game --status status --avatar avatar_url
    Description:
        The following expansions are made in game
            $users$: Number of users I can see.
            $servers$: Number of servers I am in.
            $channels$: Number of channels I am in.
        The status must be one of online, idle, dnd, invisible.
    """
    if ctx.flags["game"]:
        game = ctx.flags["game"]
        ctx.bot.objects["GAME"] = game
        status = await ctx.ctx_format(game)
        await ctx.bot.change_presence(game=discord.Game(name=status))
        await ctx.reply("Game changed to: \'{}\'".format(status))
    if ctx.flags["avatar"]:
        avatar_url = ctx.flags["avatar"]
        async with aiohttp.get(avatar_url) as r:
            response = await r.read()
        await ctx.bot.edit_profile(avatar=response)
    if ctx.flags["status"]:
        status = ctx.flags["status"]
        if status not in status_dict:
            await ctx.reply("Invalid status given!")
        else:
            await ctx.bot.change_presence(status=status_dict[status])

@cmds.cmd("dm",
          category="Bot admin",
          short_help="dms a user")
@cmds.require("master_perm")
async def cmd_dm(ctx):
    """
    Usage:
        {prefix}dm user_info message
    Description:
        Dms a user with the specified message.
        Performs a bot wide interactive lookup on user_info.
    """
    if len(ctx.params) < 2:
        await ctx.reply("Please see Usage.")
        return
    await ctx.run("dm", user_info=ctx.params[0], message=" ".join(ctx.params[1:]))
    await ctx.reply("Done.")

@cmds.cmd("logs",
          category="Bot admin",
          short_help="Reads and returns the logs")
@cmds.require("master_perm")
async def cmd_logs(ctx):
    """
    Usage:
        {prefix}logs [number]
    Description:
        Sends the logfile or the last <number> lines of the log.
    """
    if ctx.arg_str == '':
        try:
            await ctx.reply(file_name=ctx.bot.log_file)
        except Exception:
            await ctx.reply("I couldn't send you the logfile! Perhaps it is too big")
    elif ctx.params[0].isdigit():
        logs = await ctx.tail(ctx.bot.log_file, ctx.params[0])
        await ctx.reply("Here are your logs:\n```{}```".format(logs))
