import shutil
import discord
from datetime import datetime
import re

from paraCH import paraCH

cmds = paraCH()


header = "\\documentclass[preview, 12pt]{standalone}\
          \n\\nonstopmode"

default_preamble = "\\usepackage{amsmath}\
                    \n\\usepackage{fancycom}\
                    \n\\usepackage{color}\
                    \n\\usepackage{tikz-cd}"

@cmds.cmd("tex",
          category="Maths",
          short_help="Renders LaTeX code",
          aliases=["LaTeX"])
async def cmd_tex(ctx):
    """
    Usage:
        {prefix}tex <code>
    Description:
        Renders and displays LaTeX code.
        Use the reactions to delete the message and show your code, respectively.
    """
    # TODO: Make this an embed
    error = await texcomp(ctx)
    err_msg = ""
    if error != "":
        err_msg = "Compile error! Output:\n```\n{}\n```".format(error)
    else:
        await ctx.del_src()
    source_msg = "```tex\n{}\n```{}".format(ctx.arg_str, err_msg)

    out_msg = await ctx.reply(file_name='tex/{}.png'.format(ctx.authid), message= "{}:\n{}".format(ctx.author.name, source_msg if error else ""))

    del_emoji = ctx.bot.objects["emoji_tex_del"]
    show_emoji = ctx.bot.objects["emoji_tex_errors" if error else "emoji_tex_show"]
    show = 1 if error else 0

    def check(reaction, user):
        return ((reaction.emoji == del_emoji) or (reaction.emoji == show_emoji)) and (not (user == ctx.me))
    try:
        await ctx.bot.add_reaction(out_msg, del_emoji)
        await ctx.bot.add_reaction(out_msg, show_emoji)
    except discord.Forbidden:
        return
    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                              timeout=300,
                                              check=check)
        if res is None:
            break
        if res.reaction.emoji == del_emoji and res.user == ctx.author:
            await ctx.bot.delete_message(out_msg)
            return
        if res.reaction.emoji == show_emoji and (res.user != ctx.me):
            try:
                await ctx.bot.remove_reaction(out_msg, show_emoji, res.user)
            except discord.Forbidden:
                pass
            show = 1 - show
            await ctx.bot.edit_message(out_msg, ctx.author.name + ":\n" +
                                       (source_msg if show else ""))
    try:
        await ctx.bot.remove_reaction(out_msg, del_emoji, ctx.me)
        await ctx.bot.remove_reaction(out_msg, show_emoji, ctx.me)
        await ctx.bot.clear_reactions(out_msg)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass


@cmds.cmd("preamble",
          category="Maths",
          short_help="Change how your LaTeX compiles",
          aliases=["texconfig"])
@cmds.execute("flags", flags=["color==", "colour==", "reset", "approve==", "deny=="])
async def cmd_preamble(ctx):
    """
    Usage:
        {prefix}preamble [code] [--reset] [--colour|color [default|transparent]]
    Description:
        Displays the preamble currently used for compiling your latex code.
        If [code] is provided, sets this to be preamble instead.
        Note that preambles must currently be approved by a bot manager, to prevent abuse.
        Can also change the colourscheme of the output.
    Flags:2
        reset::  Resets your preamble to the default.
        colour:: One of default or transparent. Change how the output looks.
    """
    message = ""
    user_id = ctx.flags["approve"] or ctx.flags["deny"]
    if user_id:
        (code, msg) = await cmds.checks["manager_perm"](ctx)
        if code != 0:
            return
        if ctx.flags["approve"]:
            new_preamble = await ctx.data.users.get(user_id, "limbo_preamble")
            new_preamble = new_preamble if new_preamble.strip() else default_preamble
            await ctx.data.users.set(user_id, "latex_preamble", new_preamble)
            await ctx.reply("The preamble change has been approved")
        await ctx.data.users.set(user_id, "limbo_preamble", "")
        if ctx.flags["deny"]:
            await ctx.reply("The preamble change has been denied")
        return


    colour = ctx.flags["colour"] or ctx.flags["color"]
    if colour:
        if colour not in ["default", "transparent"]:
            await ctx.reply("Unrecognised colourscheme. It must be one of `default` or `transparent`.")
            return
        await ctx.data.users.set(ctx.authid, "latex_colour", colour)

    if ctx.flags["reset"]:
        await ctx.data.users.set(ctx.authid, "latex_preamble", default_preamble)
        await ctx.data.users.set(ctx.authid, "limbo_preamble", "")
        message = "Your LaTeX preamble has been reset to the default!\n"
    embed = discord.Embed(title="LaTeX config", color = discord.Colour.light_grey(), description = message)
    if ctx.arg_str.strip() == "":
        preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
        preamble = preamble if preamble else default_preamble
        embed.add_field(name="Current preamble", value="```tex\n{}\n```".format(preamble))
        new_preamble = await ctx.data.users.get(ctx.authid, "limbo_preamble")
        if new_preamble:
            embed.add_field(name="Awaiting approval", value="```tex\n{}\n```".format(new_preamble), inline=False)
        colour = await ctx.data.users.get(ctx.authid, "latex_colour")
        colour = colour if colour else "default"
        embed.add_field(name="Output colourscheme", value=colour, inline=False)
        await ctx.reply(embed=embed)
        return
    new_preamble = ctx.arg_str
    await ctx.data.users.set(ctx.authid, "limbo_preamble", new_preamble)
    embed = discord.Embed(title="LaTeX Preamble Request", color=discord.Colour.blue()) \
        .set_author(name="{} ({})".format(ctx.author, ctx.authid),
                    icon_url=ctx.author.avatar_url) \
        .add_field(name="Requested preamble", value="```tex\n{}\n```".format(new_preamble), inline=False) \
        .add_field(name="To Approve", value="`preamble --approve {}`".format(ctx.authid), inline=False) \
        .set_footer(text=datetime.utcnow().strftime("Sent from {} at %-I:%M %p, %d/%m/%Y".format(ctx.server.name if ctx.server else "private message")))
    await ctx.bot.send_message(ctx.bot.objects["preamble_channel"], embed=embed)
    await ctx.reply("Your new preamble has been sent to the bot managers for review!")



async def texcomp(ctx):
    fn = "tex/{}.tex".format(ctx.authid)
    shutil.copy('tex/preamble.tex', fn)
    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    preamble = preamble if preamble else default_preamble
    with open(fn, 'w') as work:
        work.write(header + preamble)
        work.write('\n' + '\\begin{document}' + '\n')
        work.write(ctx.arg_str)
        work.write('\n' + '\\end{document}' + '\n')
        work.close()
    colour = await ctx.data.users.get(ctx.authid, "latex_colour")
    colour = colour if colour else "default"
    return await ctx.run_sh("tex/texcompile.sh {} {}".format(ctx.authid, colour))
