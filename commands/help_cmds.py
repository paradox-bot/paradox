from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("help",
          category="General",
          short_help="Provides some detailed help on a command")
async def cmd_help(ctx):
    """
    Usage: {prefix}help [command name]

    Shows detailed help on the requested command or sends you a listing of the commands.
    """
    msg = ""
    commands = await ctx.get_cmds()  # Should probably be cached from ctx init
    sorted_cats = ctx.bot.objects["sorted cats"]
    if ctx.arg_str == "":
        cat_msgs = {}
        for cmd in sorted(commands):
            command = commands[cmd]
            cat = command.category if command.category else "Misc"
            if cat not in cat_msgs or not cat_msgs[cat]:
                cat_msgs[cat] = "```ini\n [ {}: ]\n".format(cat)
            cat_msgs[cat] += "; {}{}:\t{}\n".format(" " * (12 - len(cmd)), cmd, command.short_help)
        for cat in sorted_cats:
            if cat not in cat_msgs:
                continue
            cat_msgs[cat] += "```"
            msg += cat_msgs[cat]
        await ctx.dmreply(msg)
        await ctx.reply("I have messaged you a detailed listing of my commands! Use `list` to obtain a more succinct listing.")
        return
    else:
        for cmd in ctx.params:
            if cmd in commands:
                msg += "```{}```\n".format(commands[cmd].long_help)
            else:
                msg += "I couldn't find a command named `{}`. Please make sure you have spelled the command correctly. \n".format(cmd)
            await ctx.reply(msg)
