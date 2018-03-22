from contextBot.CommandHandler import CommandHandler
from contextBot.Command import Command

from snippets import snippets
from checks import checks


class paraCH(CommandHandler):
    name = "General commands"
    snippets = snippets
    checks = checks
    priority = 1
    CmdCls = Command

    async def before_exec(self, ctx):
        if ctx.author.bot:
            return
        if int(ctx.authid) in ctx.bot.bot_conf.getintlist("blacklisted_users"):
            ctx.cmd_err = (1, "")
