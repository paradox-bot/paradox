from paraCH import paraCH
import discord

cmds = paraCH()


@cmds.cmd("help",
          category="General",
          short_help="Provides some detailed help on a command.",
          aliases=["h"])
async def cmd_help(ctx):
    """
    Usage:
        {prefix}help [command name]
    Description:
        Shows detailed help on the requested command or sends you a listing of the commands.
    """
    help_keys = {"prefix": ctx.used_prefix,
                 "msg": ctx.msg}
    msg = ""
    all_commands = await ctx.get_cmds()  # Should probably be cached from ctx init
    if ctx.arg_str == "":
        with open("helpmsg.txt", "r") as helpmsg:
            msg = helpmsg.read()
            await ctx.reply(msg.format(prefix=ctx.used_prefix, support=ctx.bot.objects["support guild"]), dm=True)
            try:
                await ctx.bot.add_reaction(ctx.msg, "✅")
            except discord.Forbidden:
                await ctx.reply("Help sent!")
        return
    else:
        cmd = ctx.params[0]
        if cmd in all_commands:
            command = all_commands[cmd]
            cmd = command.name
            alias_str = "(alias{} `{}`)".format("es" if len(command.aliases) > 1 else "", "`, `".join(command.aliases)) if command.aliases else ""
            embed = discord.Embed(type="rich", color=discord.Colour.teal(), title="Help for `{}` {}".format(cmd, alias_str))
            emb_fields = []
            fields = command.help_fields
            if len(fields) == 0:
                msg += "Sorry, no help has been written for the command {} yet!".format(cmd)
            else:
                emb_fields = [(field[0], field[1].format(**help_keys), 0) for field in fields]
                await ctx.emb_add_fields(embed, emb_fields)
                await ctx.reply(embed=embed)
        else:
            msg += "I couldn't find a command named `{}`. Please make sure you have spelled the command correctly. \n".format(cmd)
    if msg:
        await ctx.reply(msg, split=True, code=False)


@cmds.cmd("list",
          category="General",
          short_help="Lists all my commands!")
async def cmd_list(ctx):
    """
    Usage:
        {prefix}list
    Description:
        DMs you with a complete listing of my commands.
    """
    msg = "Here are my commands!\n"
    commands = await ctx.get_raw_cmds()
    sorted_cats = ctx.bot.objects["sorted cats"]
    cat_msgs = {}
    for cmd in sorted(commands):
        command = commands[cmd]
        cat = command.category if command.category else "Misc"
        lower_cat = cat.lower()
        if lower_cat not in cat_msgs or not cat_msgs[lower_cat]:
            cat_msgs[lower_cat] = "```ini\n [ {}: ]\n".format(cat)
        cat_msgs[lower_cat] += "; {}{}:\t{}\n".format(" " * (12 - len(cmd)), cmd, command.short_help)
    for cat in sorted_cats:
        if cat.lower() not in cat_msgs:
            continue
        cat_msgs[cat.lower()] += "```"
        if len(msg) + len(cat_msgs[cat.lower()]) > 1990:
            await ctx.reply(msg, dm=True)
            msg = ""
        msg += cat_msgs[cat.lower()]
    await ctx.reply(msg, dm=True)
    try:
        await ctx.bot.add_reaction(ctx.msg, "✅")
    except discord.Forbidden:
        await ctx.reply("Command list set!")
    return
