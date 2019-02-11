from checks import checks
from contextBot.CommandHandler import CommandHandler
from paraCMD import paraCMD
from snippets import snippets


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
        if "ready" not in ctx.bot.objects:
            ctx.cmd_err = (1,
                           "Bot is restarting, please try again in a moment.")
            return
        if not ctx.bot.objects["ready"]:
            await ctx.reply(
                "I have just restarted and am loading myself, please wait!")
            await ctx.bot.wait_until_ready()
        if int(ctx.authid) in ctx.bot.bot_conf.getintlist(
                "blacklisted_users") and ctx.used_cmd_name != "texlisten":
            ctx.cmd_err = (1, "")
        try:
            await ctx.bot.send_typing(ctx.ch)
        except Exception:
            pass
        if ctx.server:
            ban_cmds = await ctx.data.servers.get(ctx.server.id, "banned_cmds")
            if ban_cmds and ctx.cmd.name in ban_cmds:
                ctx.cmd_err = (1, "")

    def build_cmd(self, name, func, aliases=[], **kwargs):
        cmd = super().build_cmd(name, func, aliases=aliases, **kwargs)
        self.raw_cmds[name] = cmd
        for alias in aliases:
            self.cmds[alias] = cmd
        return cmd

    def append(self, CH):
        super().append(CH)
        self.raw_cmds.update(CH.raw_cmds)
