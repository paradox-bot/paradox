import shutil
import discord
from datetime import datetime
import asyncio
import os

from io import StringIO
import aiohttp

from paraCH import paraCH

cmds = paraCH()

# TODO: Factor out into a util file everything except commands.

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
          short_help="Turns on listening to your LaTeX",
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
    if listening:
        if ctx.authid in ctx.bot.objects["user_tex_listeners"]:
            ctx.bot.objects["user_tex_listeners"].remove(ctx.authid)
        await ctx.data.users.set(ctx.authid, "tex_listening", False)
        await ctx.reply("I have stopped listening to your tex.")
        return
    else:
        await ctx.data.users.set(ctx.authid, "tex_listening", True)
        ctx.bot.objects["user_tex_listeners"].append(ctx.authid)
        await ctx.reply("I am now listening to your tex.")


def _is_tex(msg):
    return (("$" in msg.clean_content) and 1 - (msg.clean_content.count("$") % 2) and msg.clean_content.strip("$")) or ("\\begin{" in msg.clean_content)


@cmds.cmd("tex",
          category="Maths",
          short_help="Renders LaTeX code",
          aliases=["$", "$$", "align", "latex"])
@cmds.execute("flags", flags=["config", "keepmsg", "colour==", "alwaysmath"])
async def cmd_tex(ctx):
    """
    Usage:
        {prefix}tex <code>
        {prefix}$ <equation>
        {prefix}$$ <displayeqn>
        {prefix}align <align block>
        {prefix}tex --colour white | black | transparent | grey | dark
        {prefix}tex --keepmsg
        {prefix}tex --config
        {prefix}tex --alwaysmath
    Description:
        Renders and displays LaTeX code.

        Using $ instead of tex compiles
        \\begin{{gather*}}<code>\\end{{gather*}}.

        Using $$ instead of tex compiles
        $$<code>$$.

        Using align instead of tex compiles
        \\begin{{align*}}<code>\\end{{align*}}.

        Use the reactions to delete the message and show your code, respectively.
    Flags:2
        --config:: Shows you your current config.
        --colour:: Changes your colourscheme. One of default, white, black, transparent, or grey.
        --keepmsg:: Toggles whether I delete your source message or not.
        --alwaysmath:: Toggles whether {prefix}tex always renders in math mode.
    Examples:
        {prefix}tex This is a fraction: $\\frac{{1}}{{2}}$
        {prefix}$ \\int^\\infty_0 f(x)~dx
        {prefix}$$ \\bmqty{{1 & 0 & 0\\\\ 0 & 1 & 0\\\\ 0 & 0 & 1}}
        {prefix}align a &= b\\\\ c &= d
        {prefix}tex --colour grey
    """
    if ctx.flags["config"]:
        await show_config(ctx)
        return
    elif ctx.flags["keepmsg"]:
        keepmsg = await ctx.data.users.get(ctx.authid, "latex_keep_message")
        if keepmsg is None:
            keepmsg = True
        keepmsg = 1 - keepmsg
        await ctx.data.users.set(ctx.authid, "latex_keep_message", keepmsg)
        if keepmsg:
            await ctx.reply("I will now keep your message after compilation.")
        else:
            await ctx.reply("I will not keep your message after compilation.")
        return
    elif ctx.flags["colour"]:
        colour = ctx.flags["colour"]
        if colour not in ["default", "white", "transparent", "black", "grey", "gray", "dark"]:
            await ctx.reply("Unknown colour scheme. Known colours are `default`, `white`, `transparent`, `black`, `dark` and `grey`.")
            return
        await ctx.data.users.set(ctx.authid, "latex_colour", colour)
        await ctx.reply("Your colour scheme has been changed to {}".format(colour))
        return
    elif ctx.flags["alwaysmath"]:
        always = await ctx.data.users.get(ctx.authid, "latex_alwaysmath")
        if always is None:
            always = False
        always = 1 - always
        await ctx.data.users.set(ctx.authid, "latex_alwaysmath", always)
        if always:
            await ctx.reply("`{0}tex` will now render in math mode. You can use `{0}latex` to render normally.".format(ctx.used_prefix))
        else:
            await ctx.reply("`{0}tex` now render latex as usual.".format(ctx.used_prefix))
        return
    if ctx.arg_str == "":
        await ctx.reply("Please give me something to compile! See `{0}help` or `{0}help tex` for usage!".format(ctx.used_prefix))
        return
    ctx.objs["latex_listening"] = False
    ctx.objs["latex_source_deleted"] = False
    ctx.objs["latex_out_deleted"] = False
    ctx.objs["latex_handled"] = True
    ctx.bot.objects["latex_messages"][ctx.msg.id] = ctx

    out_msg = await make_latex(ctx)

    asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop=ctx.bot.loop)
    if not ctx.objs["latex_source_deleted"]:
        ctx.objs["latex_edit_renew"] = False
        while True:
            await asyncio.sleep(600)
            if not ctx.objs["latex_edit_renew"]:
                break
            ctx.objs["latex_edit_renew"] = False
        ctx.bot.objects["latex_messages"].pop(ctx.msg.id, None)


async def parse_tex(ctx, source):
    if source.strip().startswith("```tex"):
        source = source[6:]
    source = source.strip("`").strip()
    if ctx.objs["latex_listening"]:
        return source
    always = await ctx.bot.data.users.get(ctx.authid, "latex_alwaysmath")
    if ctx.used_cmd_name == "latex" or (ctx.used_cmd_name == "tex" and not always):
        return source
    if ctx.used_cmd_name == "$" or (ctx.used_cmd_name == "tex" and always):
        return "\\begin{{gather*}}\n{}\n\\end{{gather*}}".format(source)
    elif ctx.used_cmd_name == "$$":
        return "$${}$$".format(source)
    elif ctx.used_cmd_name == "align":
        return "\\begin{{align*}}\n{}\n\\end{{align*}}".format(source)
    else:
        return source


async def make_latex(ctx):
    source = ctx.msg.clean_content if ctx.objs["latex_listening"] else ctx.msg.clean_content.partition(ctx.used_cmd_name)[2].strip()
    ctx.objs["latex_source"] = await parse_tex(ctx, source)

    error = await texcomp(ctx)
    err_msg = ""

    keep = await ctx.data.users.get(ctx.authid, "latex_keep_message")
    keep = keep or (keep is None)

    if error != "":
        err_msg = "Compile error! Output:\n```\n{}\n```".format(error)
    elif not keep:
        ctx.objs["latex_source_deleted"] = True
        await ctx.del_src()

    ctx.objs["latex_source_msg"] = "```tex\n{}\n```{}".format(ctx.objs["latex_source"], err_msg)
    ctx.objs["latex_del_emoji"] = ctx.bot.objects["emoji_tex_del"]
    ctx.objs["latex_show_emoji"] = ctx.bot.objects["emoji_tex_errors" if error else "emoji_tex_show"]
    file_name = "tex/{}.png".format(ctx.authid)
    exists = True if os.path.isfile(file_name) else False
    out_msg = await ctx.reply(file_name=file_name if exists else "tex/failed.png",
                              message="**{}**:\n{}".format(ctx.author.name.replace("*", "\\*"),
                                                           ("Compile Error! Click the {} reaction for details. (You may edit your message)".format(ctx.objs["latex_show_emoji"])) if error else ""))
    if exists:
        os.remove(file_name)
    ctx.objs["latex_show"] = 0
    ctx.objs["latex_out_msg"] = out_msg
    return out_msg


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
            await ctx.bot.edit_message(out_msg,
                                       "**{}**:\n{}".format(ctx.author.name.replace("*", "\\*"), (ctx.objs["latex_source_msg"] if ctx.objs["latex_show"] else "")))
    try:
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_del_emoji"], ctx.me)
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_show_emoji"], ctx.me)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass
    pass


async def show_config(ctx):
    embed = discord.Embed(title="LaTeX config", color=discord.Colour.light_grey())

    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    preamble = preamble if preamble else default_preamble
    preamble_message = "```tex\n{}\n```".format(preamble)

    if len(preamble) > 1000:
        temp_file = StringIO()
        temp_file.write(preamble)

        preamble_message = "Sent via direct message"

        temp_file.seek(0)
        try:
            await ctx.bot.send_file(ctx.author, fp=temp_file, filename="current_preamble.tex", content="Your current preamble")
        except discord.Forbidden:
            preamble_message = "Attempted to send your preamble file by direct message, but couldn't reach you."

    embed.add_field(name="Current preamble", value=preamble_message)

    new_preamble = await ctx.data.users.get(ctx.authid, "limbo_preamble")
    new_preamble_message = "```tex\n{}\n```".format(new_preamble)
    if new_preamble and len(new_preamble) > 1000:
        temp_file = StringIO()
        temp_file.write(new_preamble)

        new_preamble_message = "Sent via direct message"

        temp_file.seek(0)
        try:
            await ctx.bot.send_file(ctx.author, fp=temp_file, filename="new_preamble.tex", content="Preamble awaiting approval.")
        except discord.Forbidden:
            new_preamble_message = "Attempted to send your preamble file by direct message, but couldn't reach you."

    if new_preamble:
        embed.add_field(name="Awaiting approval", value=new_preamble_message, inline=False)

    colour = await ctx.data.users.get(ctx.authid, "latex_colour")
    colour = colour if colour else "default"
    embed.add_field(name="Output colourscheme (colour)", value=colour, inline=False)

    keep = await ctx.data.users.get(ctx.authid, "latex_keep_message")
    keep = "Yes" if keep or (keep is None) else "No"
    embed.add_field(name="Whether to keep source message after rendering (keepmsg)", value=keep, inline=False)

    await ctx.reply(embed=embed)


@cmds.cmd("preamble",
          category="Maths",
          short_help="Change how your LaTeX compiles",
          aliases=["texconfig"])
@cmds.execute("flags", flags=["reset", "approve==", "deny=="])
async def cmd_preamble(ctx):
    """
    Usage:
        {prefix}preamble [code] [--reset]
    Description:
        Displays the preamble currently used for compiling your latex code.
        If [code] is provided, sets this to be preamble instead.
        Note that preambles must currently be approved by a bot manager, to prevent abuse.
    Flags:2
        reset::  Resets your preamble to the default.
    """
    user_id = ctx.flags["approve"] or ctx.flags["deny"]
    if user_id:
        (code, msg) = await cmds.checks["manager_perm"](ctx)
        if code != 0:
            return
        if ctx.flags["approve"]:
            new_preamble = await ctx.data.users.get(user_id, "limbo_preamble")
            if not new_preamble:
                await ctx.reply("Nothing to approve. Perhaps this preamble was already approved?")
                return
            new_preamble = new_preamble if new_preamble.strip() else default_preamble
            await ctx.data.users.set(user_id, "latex_preamble", new_preamble)
            await ctx.reply("The preamble change has been approved")
        await ctx.data.users.set(user_id, "limbo_preamble", "")
        if ctx.flags["deny"]:
            await ctx.reply("The preamble change has been denied")
        return

    if not ctx.arg_str and not ctx.msg.attachments:
        await show_config(ctx)
        return

    if ctx.flags["reset"]:
        await ctx.data.users.set(ctx.authid, "latex_preamble", default_preamble)
        await ctx.data.users.set(ctx.authid, "limbo_preamble", "")
        await ctx.reply("Your LaTeX preamble has been reset to the default!")
        return
    ctx.objs["latex_handled"] = True

    file_name = "preamble.tex"
    if ctx.msg.attachments:
        file_info = ctx.msg.attachments[0]
        async with aiohttp.get(file_info['url']) as r:
            new_preamble = await r.text()
        file_name = file_info['filename']
    else:
        new_preamble = ctx.arg_str

    await ctx.data.users.set(ctx.authid, "limbo_preamble", new_preamble)

    in_file = (len(new_preamble) > 1000)
    if in_file:
        temp_file = StringIO()
        temp_file.write(new_preamble)

    preamble_message = "See file below!" if in_file else "```tex\n{}\n```".format(new_preamble)

    embed = discord.Embed(title="LaTeX Preamble Request", color=discord.Colour.blue()) \
        .set_author(name="{} ({})".format(ctx.author, ctx.authid),
                    icon_url=ctx.author.avatar_url) \
        .add_field(name="Requested preamble", value=preamble_message, inline=False) \
        .add_field(name="To Approve", value="`preamble --approve {}`".format(ctx.authid), inline=False) \
        .set_footer(text=datetime.utcnow().strftime("Sent from {} at %-I:%M %p, %d/%m/%Y".format(ctx.server.name if ctx.server else "private message")))
    await ctx.bot.send_message(ctx.bot.objects["preamble_channel"], embed=embed)
    if in_file:
        temp_file.seek(0)
        await ctx.bot.send_file(ctx.bot.objects["preamble_channel"], fp=temp_file, filename=file_name)
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


async def register_tex_listeners(bot):
    bot.objects["user_tex_listeners"] = [str(userid) for userid in await bot.data.users.find("tex_listening", True, read=True)]
    bot.objects["server_tex_listeners"] = [str(serverid) for serverid in await bot.data.servers.find("latex_listen_enabled", True, read=True)]
    bot.objects["latex_messages"] = {}
    await bot.log("Loaded {} user tex listeners and {} server tex listeners.".format(len(bot.objects["user_tex_listeners"]), len(bot.objects["server_tex_listeners"])))


async def tex_listener(ctx):
    if ctx.author.bot:
        return
    if "ready" not in ctx.bot.objects or not ctx.bot.objects["ready"]:
        return
    if "latex_handled" in ctx.objs and ctx.objs["latex_handled"]:
        return
    if not (ctx.authid in ctx.bot.objects["user_tex_listeners"] or (ctx.server and ctx.server.id in ctx.bot.objects["server_tex_listeners"])):
        return
    if not _is_tex(ctx.msg):
        return
    await ctx.bot.log("Recieved the following listening tex message from \"{ctx.author.name}\" in server \"{ctx.server.name}\":\n{ctx.cntnt}".format(ctx=ctx))
    ctx.objs["latex_handled"] = True
    ctx.objs["latex_listening"] = True
    ctx.objs["latex_source_deleted"] = False
    ctx.objs["latex_out_deleted"] = False
    ctx.bot.objects["latex_messages"][ctx.msg.id] = ctx

    out_msg = await make_latex(ctx)

    ctx.objs["latex_out_msg"] = out_msg

    asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop=ctx.bot.loop)
    if not ctx.objs["latex_source_deleted"]:
        ctx.objs["latex_edit_renew"] = False
        while True:
            await asyncio.sleep(600)
            if not ctx.objs["latex_edit_renew"]:
                break
            ctx.objs["latex_edit_renew"] = False
        ctx.bot.objects["latex_messages"].pop(ctx.msg.id, None)


async def tex_edit_listener(bot, before, after):
    if before.id not in bot.objects["latex_messages"]:
        return
    if before.content == after.content:
        return
    ctx = bot.objects["latex_messages"][before.id]
    ctx.objs["latex_edit_renew"] = True
    ctx.msg = after

    old_out_msg = ctx.objs["latex_out_msg"] if "latex_out_msg" in ctx.objs else None
    if old_out_msg:
        try:
            await ctx.bot.delete_message(old_out_msg)
        except discord.NotFound:
            pass
    out_msg = await make_latex(ctx)
    asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop=ctx.bot.loop)


def load_into(bot):
    bot.add_after_event("ready", register_tex_listeners)
    bot.add_after_event("message_edit", tex_edit_listener)
    bot.after_ctx_message(tex_listener)
