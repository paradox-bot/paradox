from paraCH import paraCH

cmds = paraCH()
# Provides bancmd
# TODO: Upgrade to limitcmd


@cmds.cmd(
    "bancmd",
    category="Server Admin",
    short_help="Blacklist commands in the server.",
    aliases=["bcmd", "nocmd", "unbancmd"])
@cmds.require("in_server")
@cmds.require("has_manage_server")
async def cmd_bancmd(ctx):
    """
    Usage:
        {prefix}bancmd [cmd1, cmd2, cmd3,...]
    Descriptions:
        Bans or unbans the commands listed, or with no input shows the currently banned commands.
    Example:
        {prefix}bancmd secho, echo
    """
    bans = await ctx.data.servers.get(ctx.server.id, "banned_cmds")
    bans = bans if bans else []
    if not ctx.arg_str:
        bans_str = "Current banned commands: `{}`".format(
            "`, `".join(bans)) if bans else "There are no banned commands in this server!"
        await ctx.reply(bans_str)
        return
    cmds = ctx.arg_str.split(",")
    newbans = []
    unbans = []
    for cmd in cmds:
        cmd = cmd.strip()
        if cmd in bans:
            bans.remove(cmd)
            unbans.append(cmd)
        else:
            if cmd == "bancmd":
                await ctx.reply("You can't ban bancmd!")
                continue
            bans.append(cmd)
            newbans.append(cmd)
    newbanstr = "Banned commands: `{}`\n".format("`, `".join(newbans))
    unbanstr = "Unbanned commands: `{}`".format("`, `".join(unbans))
    await ctx.reply("{}{}".format(newbanstr if newbans else "", unbanstr if unbans else ""))
    await ctx.data.servers.set(ctx.server.id, "banned_cmds", bans)
