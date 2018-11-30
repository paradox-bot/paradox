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
    commands = await ctx.get_raw_cmds()
    sorted_cats = ctx.bot.objects["sorted cats"]
    if ctx.arg_str == "":
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
        await ctx.reply("I have messaged you a detailed listing of my commands! \
                        \nUse `{0.used_prefix}help <cmd>` to get detailed help on a command, or `{0.used_prefix}list` to obtain a briefer listing.".format(ctx))
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
        Replies with an embed containing all my visible commands.
    """
    sorted_cats = ctx.bot.objects["sorted cats"]
    cats = {}
    commands = await ctx.get_raw_cmds()
    for cmd in sorted(commands):
        command = commands[cmd]
        cat = command.category if command.category else "Misc"
        lower_cat = cat.lower()
        if lower_cat not in cats:
            cats[lower_cat] = []
        cats[lower_cat].append(cmd)
    embed = discord.Embed(title="Paradøx's commands!", color=discord.Colour.green())
    for cat in sorted_cats:
        if cat.lower() not in cats:
            continue
        embed.add_field(name=cat, value="`{}`".format('`, `'.join(cats[cat.lower()])), inline=False)
    embed.set_footer(text="Use {0}help or {0}help <command> for detailed help or get support with {0}support.".format(ctx.used_prefix))
    await ctx.reply(embed=embed)
