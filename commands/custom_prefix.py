from paraCH import paraCH


cmds = paraCH()


@cmds.cmd("prefix",
          category="General",
          short_help="Set or view prefixes",
          aliases=["myprefix"])
@cmds.execute("flags", flags=["set=="])
async def cmd_tag(ctx):
    """
    Usage:
        {prefix}prefix [--set <custom prefix>]
    Description:
        Shows some information about the command prefixes where you are, or sets a personal custom prefix.
        Use {prefix}config prefix <prefix> to change the server prefix.
        A mention will always work as a prefix.
    Flags:2
        --set:: Set your personal bot prefix.
    """
    if ctx.flags["set"]:
        await ctx.bot.data.users.set(ctx.authid, "custom_prefix", ctx.flags["set"])
        await ctx.reply("Your personal custom prefix has been set to `{}`. Mentions and any server custom prefix will still function.".format(ctx.flags["set"]))
        return

    personal_prefix = await ctx.bot.data.users.get(ctx.authid, "custom_prefix")
    server_prefix = (await ctx.server_conf.guild_prefix.get(ctx)) if ctx.server else None
    personal = "Your personal prefix is `{}`.".format(personal_prefix) if personal_prefix else "You have not set a personal prefix."
    server = "The current server prefix is `{}`.".format(server_prefix) if server_prefix else "No custom server prefix here."
    default = "Default prefix is `{}`.".format(ctx.bot.prefix)
    await ctx.reply("{}\n{}\n{}".format(personal, server if ctx.server else "", default))
