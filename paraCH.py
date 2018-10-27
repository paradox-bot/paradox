from contextBot.CommandHandler import CommandHandler
from paraCMD import paraCMD

from snippets import snippets
from checks import checks


class paraCH(CommandHandler):
    name = "General commands"
    snippets = snippets
    checks = checks
    priority = 1
    CmdCls = paraCMD

    def __init__(self):
        super().__init__()
        self.raw_cmds = {}  # The raw command listing, with no aliases

    async def before_exec(self, ctx):
        if ctx.author.bot:
            ctx.cmd_err = (1, "")
        if int(ctx.authid) in ctx.bot.bot_conf.getintlist("blacklisted_users"):
            ctx.cmd_err = (1, "")
        try:
            await ctx.bot.send_typing(ctx.ch)
        except Exception:
            pass

    def build_cmd(self, name, func, aliases=[], **kwargs):
        cmd = super().build_cmd(name, func, aliases=aliases, **kwargs)
        self.raw_cmds[name] = cmd
        for alias in aliases:
            self.cmds[alias] = cmd
        return cmd

    def append(self, CH):
        super().append(CH)
        self.raw_cmds.update(CH.raw_cmds)

