import shutil
import discord
from datetime import datetime
import re
import asyncio
import copy

from paraCH import paraCH

cmds = paraCH()

#TODO: Factor out into a util file everything except commands.

header = "\\documentclass[preview, 12pt]{standalone}\
          \n\\nonstopmode\
          \n\\everymath{\\displaystyle}\
          \n\\usepackage[mathletters]{ucs}\
          \n\\usepackage[utf8x]{inputenc}"

default_preamble = "\\usepackage{amsmath}\
                    \n\\usepackage{fancycom}\
                    \n\\usepackage{color}\
                    \n\\usepackage{tikz-cd}"

@cmds.cmd("texlisten",
          category="Maths",
          short_help="Listens for latex to reply to",
          aliases=["tl"])
async def cmd_texlisten(ctx):
    """
    Usage:
        {prefix}texlisten
    Description:
        Toggles listening to messages you post looking for tex.
        When tex is found, compiles it and replies to you.
    """
    listening = await ctx.data.users.get(ctx.authid, "tex_listening")
    if listening and not ctx.arg_str:
        if ctx.authid in ctx.bot.objects["tex_listen_tasks"]:
            ctx.bot.objects["tex_listen_tasks"][ctx.authid].cancel()
        await ctx.data.users.set(ctx.authid, "tex_listening", False)
        await ctx.reply("I have stopped listening to your tex.")
        return
    await ctx.data.users.set(ctx.authid, "tex_listening", True)
    ctx.objs["latex_listening"] = True
    listen_task = asyncio.ensure_future(texlistener(ctx), loop=ctx.bot.loop)
    ctx.bot.objects["tex_listen_tasks"][ctx.authid] = listen_task
    await ctx.reply("I am now listening to your tex.")

def _is_tex(msg):
    return (("$" in msg.content) and 1 - (msg.content.count("$") % 2)) or ("\\begin{" in msg.content)


async def texlistener(ctx):
    while True:
        msg = await ctx.bot.wait_for_message(author=ctx.author, check=_is_tex)
        if not await ctx.data.users.get(ctx.author.id, "tex_listening"):
            break
        await ctx.bot.log("Got a listening latex message\n{}\nfrom `{}` in `{}`".format(msg.content, msg.author.name, msg.server.name if msg.server else "DM"))

        newctx = type(ctx)(bot=ctx.bot, message=msg)
        newctx.msg = msg
        newctx.ch = msg.channel
        first = msg.content.split()[0]
        if not any(first.startswith(okprefix) for okprefix in ["$", "```tex", "`$", "\\begin"]) and any(prefix in first for prefix in ["latex", "tex", "align", "$", "$$"]):
            continue
        newctx.objs["latex_listening"] = True
        newctx.objs["latex_source_deleted"] = False
        newctx.objs["latex_out_deleted"] = False
        newctx.objs["latex_source"] = parse_tex(newctx, msg.content)
        out_msg = await make_latex(newctx)

        asyncio.ensure_future(reaction_edit_handler(newctx, out_msg), loop = ctx.bot.loop)
        if not newctx.objs["latex_source_deleted"]:
            asyncio.ensure_future(source_edit_handler(newctx, out_msg), loop = ctx.bot.loop)



@cmds.cmd("tex",
          category="Maths",
          short_help="Renders LaTeX code",
          aliases=["LaTeX", "$", "$$", "align"])
async def cmd_tex(ctx):
    """
    Usage:
        {prefix}tex <code>
        {prefix}$ <equation>
        {prefix}$$ <displayeqn>
        {prefix}align <align block>
    Description:
        Renders and displays LaTeX code.
        Using $ instead of tex compiles $<code>$.
        Using $$ instead of tex compiles $$<code>$$.
        Using align instead of tex compiles \\begin{{align*}}<code>\\end{{align*}}.
        Use the reactions to delete the message and show your code, respectively.
    """
    ctx.objs["latex_listening"] = False
    ctx.objs["latex_source_deleted"] = False
    ctx.objs["latex_out_deleted"] = False
    ctx.objs["latex_source"] = parse_tex(ctx, ctx.arg_str)

    out_msg = await make_latex(ctx)

    asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop = ctx.bot.loop)
    if not ctx.objs["latex_source_deleted"]:
        asyncio.ensure_future(source_edit_handler(ctx, out_msg), loop = ctx.bot.loop)

def parse_tex(ctx, source):
    if source.strip().startswith("```tex"):
        source = source[6:]
    source = source.strip("`").strip()
    if ctx.objs["latex_listening"]:
        return source
    if ctx.used_cmd_name == "$":
        return "${}$".format(source)
    elif ctx.used_cmd_name == "$$":
        return "$${}$$".format(source)
    elif ctx.used_cmd_name == "align":
        return "\\begin{{align*}}\n{}\n\\end{{align*}}".format(source)
    else:
        return source

async def make_latex(ctx):
    error = await texcomp(ctx)
    err_msg = ""
    if error != "":
        err_msg = "Compile error! Output:\n```\n{}\n```".format(error)
    elif not (await ctx.data.users.get(ctx.authid, "latex_keep_message")):
        ctx.objs["latex_source_deleted"] = True
        await ctx.del_src()
    ctx.objs["latex_source_msg"] = "```tex\n{}\n```{}".format(ctx.objs["latex_source"], err_msg)
    ctx.objs["latex_del_emoji"] = ctx.bot.objects["emoji_tex_del"]
    ctx.objs["latex_show_emoji"] = ctx.bot.objects["emoji_tex_errors" if error else "emoji_tex_show"]
    out_msg = await ctx.reply(file_name='tex/{}.png'.format(ctx.authid), message= "{}:\n{}".format(ctx.author.name, ("Compile Error! Click the {} reaction for details.".format(ctx.objs["latex_show_emoji"])) if error else ""))
    ctx.objs["latex_show"] = 0
    return out_msg


async def source_edit_handler(ctx, out_msg):
    while True:
        res = await ctx.bot.wait_for_message_edit(message=ctx.msg, timeout=300)
        if res is None:
            break
        if (not res.after) or (not res.after.content):
            break
        if res.before.content == res.after.content:
            continue
        source = res.after.content if ctx.objs["latex_listening"] else res.after.content[(len(res.after.content.split()[0])):].strip()
        ctx.objs["latex_source"] = parse_tex(ctx, source)
        try:
            await ctx.bot.delete_message(out_msg)
        except discord.NotFound:
            pass
        out_msg = await make_latex(ctx)
        asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop = ctx.bot.loop)

async def reaction_edit_handler(ctx, out_msg):
    try:
        await ctx.bot.add_reaction(out_msg, ctx.objs["latex_del_emoji"])
        await ctx.bot.add_reaction(out_msg, ctx.objs["latex_show_emoji"])
    except discord.Forbidden:
        return
    def check(reaction, user):
        return ((reaction.emoji == ctx.objs["latex_del_emoji"]) or (reaction.emoji == ctx.objs["latex_show_emoji"])) and (not (user == ctx.me))
    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                              timeout=300,
                                              check=check)
        if res is None:
            break
        if res.reaction.emoji == ctx.objs["latex_del_emoji"] and res.user == ctx.author:
            await ctx.bot.delete_message(out_msg)
            ctx.objs["latex_out_deleted"] = True
            return
        if res.reaction.emoji == ctx.objs["latex_show_emoji"] and (res.user != ctx.me):
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_show_emoji"], res.user)
            except discord.Forbidden:
                pass
            ctx.objs["latex_show"] = 1 - ctx.objs["latex_show"]
            await ctx.bot.edit_message(out_msg, ctx.author.name + ":\n" +
                                       (ctx.objs["latex_source_msg"] if ctx.objs["latex_show"] else ""))
    try:
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_del_emoji"], ctx.me)
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_show_emoji"], ctx.me)
        #await ctx.bot.clear_reactions(out_msg)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass
    pass


@cmds.cmd("preamble",
          category="Maths",
          short_help="Change how your LaTeX compiles",
          aliases=["texconfig"])
@cmds.execute("flags", flags=["color==", "colour==", "keepmsg==", "reset", "approve==", "deny=="])
async def cmd_preamble(ctx):
    """
    Usage:
        {prefix}preamble [code] [--reset] [--colour|color [default|transparent]] [--keepmsg [yes|no]]
    Description:
        Displays the preamble currently used for compiling your latex code.
        If [code] is provided, sets this to be preamble instead.
        Note that preambles must currently be approved by a bot manager, to prevent abuse.
        Can also change the colourscheme of the output.
    Flags:2
        reset::  Resets your preamble to the default.
        colour:: One of default or transparent. Change how the output looks.
        keepmsg:: Either yes or no. Whether to delete your source message after rendering.
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

    keep = ctx.flags["keepmsg"]
    if keep:
        if keep not in ["yes", "no"]:
            await ctx.reply("Unrecognised keep message setting. It must be `yes` or `no`.")
            return
        await ctx.data.users.set(ctx.authid, "latex_keep_message", True if keep == "yes" else False)

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
        embed.add_field(name="Output colourscheme (colour)", value=colour, inline=False)
        keep = await ctx.data.users.get(ctx.authid, "latex_keep_message")
        keep = "Yes" if keep else "No"
        embed.add_field(name="Whether to keep source message after rendering (keepmsg)", value=keep, inline=False)
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
        work.write(ctx.objs["latex_source"])
        work.write('\n' + '\\end{document}' + '\n')
        work.close()
    colour = await ctx.data.users.get(ctx.authid, "latex_colour")
    colour = colour if colour else "default"
    return await ctx.run_sh("tex/texcompile.sh {} {}".format(ctx.authid, colour))
