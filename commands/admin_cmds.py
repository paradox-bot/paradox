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
@cmds.require("master_perm")
async def cmd_setgame(ctx):
    """
    Usage:
        {prefix}setgame <status>
    Description:
        Sets my playing status to <status>, The following expansions are made:
            $users$: Number of users I can see.
            $servers$: Number of servers I am in.
            $channels$: Number of channels I am in.
    """
    ctx.bot.objects["GAME"] = ctx.arg_str
    status = await ctx.ctx_format(ctx.arg_str)
    await ctx.bot.change_presence(game=discord.Game(name=status))
    await ctx.reply("Game changed to: \'{}\'".format(status))

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
        Performs an bot wide interactive lookup on user_info.
    """
    if len(ctx.params < 2):
        await ctx.reply("Please see Usage.")
        return
    await ctx.run("dm", user_info = ctx.params[0], message = " ".join(ctx.params[1:]))
    await ctx.reply("Done.")

@cmds.cmd("restart",
          category="Bot admin",
          short_help="Restart the bot.")
@cmds.require("manager_perm")
async def cmd_restart(ctx):
    """
    Usage:
        {prefix}restart
    Description:
        Redeploys the bot from github.
    """
    await ctx.reply("Restarting! Hold your horses...")
    msg = await ctx.run_sh('./Nanny/scripts/redeploy.sh')
    await ctx.reply(msg)

'''
@cmds.cmd("masters",
          category="Bot admin",
          short_help="Modify or check the bot masters")
@cmds.require("master_perm")
async def cmd_masters(ctx):
    """
    Usage: {prefix}masters [list] | [+/add | -/remove] <userid/mention>

    Adds or removes a bot master by id or mention, or lists all current masters.
    """
    masters = await ctx.bot.bot_conf["masters"].read(conf, None, message, client)
    action = ctx.params[0]
    if action in ['', 'list']:
        await ctx.reply("My masters are:\n{}".format(masters))
    else:
        errmsg = await ctx.bot.bot_conf["masters"].write(conf, None, cargs, message, client, message.server, botdata)
        await ctx.reply(errmsg)


@cmds.cmd("blacklist",
          category="Bot admin",
          short_help="Modify or check the bot blacklist")
@cmds.require("master_perm")
async def cmd_blacklist(ctx):
    """
    Usage: {prefix}blacklist [list] | [+/add | -/remove] <userid/mention>

    Adds or removes a blacklisted user by id or mention, or lists all current blacklisted users.
    """
    blist = await ctx.bot.bot_conf["blacklist"].read(conf, None, message, client)
    action = ctx.params[0]
    if action in ['', 'list']:
        await ctx.reply("I have blacklisted:\n{}".format(blist))
    else:
        errmsg = await ctx.bot.bot_conf["blacklist"].write(conf, None, cargs, message, client, message.server, botdata)
        await ctx.reply(errmsg)
'''


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
