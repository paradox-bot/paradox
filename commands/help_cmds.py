from paraCH import paraCH
import discord

cmds = paraCH()


@cmds.cmd("help",
          category="General",
          short_help="Provides some detailed help on a command.")
async def cmd_help(ctx):
    """
    Usage: {prefix}help [command name]

    Shows detailed help on the requested command or sends you a listing of the commands.
    """
    help_keys = {"prefix": ctx.used_prefix}
    msg = ""
    commands = await ctx.get_cmds()  # Should probably be cached from ctx init
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
            msg += cat_msgs[cat.lower()]
        await ctx.reply(msg, dm=True)
        await ctx.reply("I have messaged you a detailed listing of my commands! Use `{0.used_prefix}list` to obtain a more succinct listing.".format(ctx))
        return
    else:
        for cmd in ctx.params:
            if cmd in commands:
                msg += "```{}```\n".format((commands[cmd].long_help).format(**help_keys))
            else:
                msg += "I couldn't find a command named `{}`. Please make sure you have spelled the command correctly. \n".format(cmd)
        await ctx.reply(msg, split=True, code=False)


@cmds.cmd("list",
          category="General",
          short_help="Lists all my commands!")
async def cmd_list(ctx):
    """
    Usage: {prefix}list

    Replies with an embed containing all my visible commands.
    """
    sorted_cats = ctx.bot.objects["sorted cats"]
    if ctx.arg_str == "":
        cats = {}
        commands = await ctx.get_cmds()
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
        embed.set_footer(text="Use ~help or ~help <command> for detailed help or get support with ~support.")
        await ctx.reply(embed=embed)
