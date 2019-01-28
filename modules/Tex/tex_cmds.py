import shutil
import discord
from datetime import datetime
import asyncio
import os

from io import StringIO
import aiohttp

from paraCH import paraCH

from contextBot.Context import MessageContext as MCtx

cmds = paraCH()

# TODO: Factor out into a util file everything except commands.

header = "\\documentclass[preview, border=5pt, 12pt]{standalone}\
          \n\\nonstopmode\
          \n\\everymath{\\displaystyle}\
          \n\\usepackage[mathletters]{ucs}\
          \n\\usepackage[utf8x]{inputenc}"

default_preamble = "\\usepackage{amsmath}\
                    \n\\usepackage{fancycom}\
                    \n\\usepackage{color}\
                    \n\\usepackage{tikz-cd}\
                    \n\\usepackage{physics}"


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
    return (("$" in msg.clean_content) and 1 - (msg.clean_content.count("$") % 2) and msg.clean_content.strip("$")) or ("\\begin{" in msg.clean_content) or ("\\[" in msg.clean_content and "\\]" in msg.clean_content)


@cmds.cmd("tex",
          category="Maths",
          short_help="Renders LaTeX code",
          aliases=[",", "$", "$$", "align", "latex", "texw"])
@cmds.execute("flags", flags=["config", "keepmsg", "color==", "colour==", "alwaysmath", "allowother", "name"])
async def cmd_tex(ctx):
    """
    Usage:
        {prefix}tex <code>
        {prefix}, <code>
        {prefix}$ <equation>
        {prefix}$$ <displayeqn>
        {prefix}align <align block>
        {prefix}tex --colour white | black | grey | dark
    Description:
        Renders and displays LaTeX code.

        Using $ or , instead of tex compiles
        \\begin{{gather*}}<code>\\end{{gather*}}
        (You can treat this as a display equation with centering where \\\\ works.)

        Using $$ instead of tex compiles
        $$<code>$$.

        Using align instead of tex compiles
        \\begin{{align*}}<code>\\end{{align*}}.

        Use the reactions to delete the message and show your code, respectively.
    Flags:2
        --config:: Shows you your current config.
        --colour:: Changes your colourscheme. One of default, white, black, or grey.
        --keepmsg:: Toggles whether I delete your source message or not.
        --alwaysmath:: Toggles whether {prefix}tex always renders in math mode.
        --allowother:: Toogles whether other users may use the reaction to show your message source.
        --name:: Toggles whether your name appears on the output message. Note the name of the image is your userid.
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
    elif ctx.flags["colour"] or ctx.flags["color"]:
        colour = ctx.flags["colour"] if ctx.flags["colour"] else ctx.flags["color"]
        if colour not in ["default", "white", "black", "grey", "gray", "dark"]:
            await ctx.reply("Unknown colour scheme. Known colours are `default`, `white`, `black`, `dark` and `grey`.")
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
    elif ctx.flags["allowother"]:
        allowed = await ctx.data.users.get(ctx.authid, "latex_allowother")
        if allowed is None:
            allowed = False
        allowed = 1 - allowed
        await ctx.data.users.set(ctx.authid, "latex_allowother", allowed)
        if allowed:
            await ctx.reply("Other people may now use the reaction to view your message source.")
        else:
            await ctx.reply("Other people may no longer use the reaction to view your message source.")
        return
    elif ctx.flags["name"]:
        showname = await ctx.data.users.get(ctx.authid, "latex_showname")
        if showname is None:
            showname = True
        showname = 1 - showname
        await ctx.data.users.set(ctx.authid, "latex_showname", showname)
        if showname:
            await ctx.reply("Your name is now shown on the output message.")
        else:
            await ctx.reply("Your name is no longer shown on the output message. Note that your user id appears in the name of the output image.")
        return

    if ctx.arg_str == "":
        await ctx.reply("Please give me something to compile! See `{0}help` and `{0}help tex` for usage!".format(ctx.used_prefix))
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
    if ctx.used_cmd_name in ["$", ","] or (ctx.used_cmd_name == "tex" and always):
        return "\\begin{{gather*}}\n{}\n\\end{{gather*}}".format(source.strip(","))
    elif ctx.used_cmd_name == "$$":
        return "$${}$$".format(source)
    elif ctx.used_cmd_name == "align":
        return "\\begin{{align*}}\n{}\n\\end{{align*}}".format(source)
    elif ctx.used_cmd_name == "texw":
        return "{{\\color{{white}}\\rule{{\\textwidth}}{{1pt}}}}\n{}".format(source)
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
    ctx.objs["latex_delsource_emoji"] = ctx.bot.objects["emoji_tex_delsource"]
    ctx.objs["latex_show_emoji"] = ctx.bot.objects["emoji_tex_errors" if error else "emoji_tex_show"]

    ctx.objs["latex_name"] = "**{}**:\n".format(ctx.author.name.replace("*", "\\*")) if (await ctx.data.users.get(ctx.authid, "latex_showname")) in [None, True] else ""

    file_name = "tex/{}.png".format(ctx.authid)
    exists = True if os.path.isfile(file_name) else False
    out_msg = await ctx.reply(file_name=file_name if exists else "tex/failed.png",
                              message="{}{}".format(ctx.objs["latex_name"],
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
        if not ctx.objs["latex_source_deleted"]:
            await ctx.bot.add_reaction(out_msg, ctx.objs["latex_delsource_emoji"])

    except discord.Forbidden:
        return
    allow_other = await ctx.bot.data.users.get(ctx.authid, "latex_allowother")

    def check(reaction, user):
        if user == ctx.me:
            return False
        result = reaction.emoji == ctx.objs["latex_del_emoji"] and user == ctx.author
        result = result or (reaction.emoji == ctx.objs["latex_show_emoji"] and (allow_other or user == ctx.author))
        result = result or (reaction.emoji == ctx.objs["latex_delsource_emoji"] and (user == ctx.author))
        return result

    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                              timeout=300,
                                              check=check)
        if res is None:
            break
        if res.reaction.emoji == ctx.objs["latex_delsource_emoji"]:
            try:
                await ctx.bot.delete_message(ctx.msg)
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_delsource_emoji"], ctx.me)
                await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_delsource_emoji"], ctx.author)
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass

        if res.reaction.emoji == ctx.objs["latex_del_emoji"] and res.user == ctx.author:
            await ctx.bot.delete_message(out_msg)
            ctx.objs["latex_out_deleted"] = True
            return
        if res.reaction.emoji == ctx.objs["latex_show_emoji"] and (res.user != ctx.me):
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_show_emoji"], res.user)
            except discord.Forbidden:
                pass
            except discord.NotFound:
                pass
            ctx.objs["latex_show"] = 1 - ctx.objs["latex_show"]
            await ctx.bot.edit_message(out_msg,
                                       "{}{} ".format(ctx.objs["latex_name"], (ctx.objs["latex_source_msg"] if ctx.objs["latex_show"] else "")))
    try:
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_del_emoji"], ctx.me)
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_show_emoji"], ctx.me)
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_delsource_emoji"], ctx.me)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass
    pass


async def show_config(ctx):
    # Grab the config values
    grab = ["latex_keep_msg", "latex_colour", "latex_alwaysmath", "latex_allowother", "latex_showname"]
    grab_names = ["keepmsg", "colour", "alwaysmath", "allowother", "showname"]

    values = []
    for to_grab in grab:
        values.append(await ctx.data.users.get(ctx.authid, to_grab))

    value_lines = []
    value_lines.append("Keeping your message after compilation" if values[0] or values[0] is None else "Deleting your message after compilation")
    value_lines.append("Using colourscheme `{}`".format(values[1] if values[1] is not None else "default"))
    value_lines.append(("`{}tex` renders in mathmode" if values[2] else "`{}tex` renders in textmode").format(ctx.used_prefix))
    value_lines.append("Other uses may view your source and errors" if values[3] else "Other users may not view your source and errors")
    value_lines.append("Your name shows on the compiled output" if values[4] or values[4] is None else "Your name is hidden on the compiled output")

    desc = "**Config Option Values:**\n{}".format(ctx.prop_tabulate(grab_names, value_lines))

    # Initialise the embed
    embed = discord.Embed(title="Personal LaTeX Configuration", color=discord.Colour.light_grey(), description=desc)

    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    header = ""
    if not preamble:
        header = "No custom user preamble set, using default preamble."
        preamble = default_preamble
        if ctx.server:
            server_preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
            if server_preamble:
                header = "No custom user preamble set, using server preamble."
                preamble = server_preamble

    preamble_message = "{}```tex\n{}\n```".format(header, preamble)

    if len(preamble) > 1000:
        temp_file = StringIO()
        temp_file.write(preamble)

        preamble_message = "{}\nSent via direct message".format(header)

        temp_file.seek(0)
        try:
            await ctx.bot.send_file(ctx.author, fp=temp_file, filename="current_preamble.tex", content="Current active preamble")
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

    await ctx.reply(embed=embed)


@cmds.cmd("serverpreamble",
          category="Maths",
          short_help="Change the server LaTeX preamble",
          flags=["reset", "replace", "remove"])
@cmds.require("in_server")
@cmds.require("in_server_has_mod")
async def cmd_serverpreamble(ctx):
    """
    Usage:
        {prefix}serverpreamble [code] [--reset] [--replace] [--remove]
    Description:
        Modifies or displays the current server preamble.
        The server preamble is used for compilation when a user in the server has no personal preamble.
        If [code] is provided, adds this to the server preamble, or replaces it with --replace
    Flags:2
        reset::  Resets your preamble to the default.
        replace:: replaces your preamble with this code
        remove:: Removes all lines from your preamble containing the given text.
    """
    if ctx.flags["reset"]:
        await ctx.data.servers.set(ctx.server.id, "server_latex_preamble", None)
        await ctx.reply("The server preamble has been reset to the default!")
        return

    current_preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
    current_preamble = current_preamble if current_preamble else default_preamble

    if not ctx.arg_str and not ctx.msg.attachments:
        if len(current_preamble) > 1000:
            temp_file = StringIO()
            temp_file.write(current_preamble)

            temp_file.seek(0)
            await ctx.reply(file_data=temp_file, file_name="server_preamble.tex", message="Current server preamble")
        else:
            await ctx.reply("Current server preamble:\n```tex\n{}```".format(current_preamble))
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

    if not ctx.flags["replace"]:
        new_preamble = "{}\n{}".format(current_preamble, new_preamble)

    if ctx.flags["remove"]:
        if ctx.arg_str not in current_preamble:
            await ctx.reply("Couldn't find this string in any line of the server preamble!")
            return
        new_preamble = "\n".join([line for line in current_preamble.split("\n") if ctx.arg_str not in line])

    await ctx.data.servers.set(ctx.server.id, "server_latex_preamble", new_preamble)

    in_file = (len(new_preamble) > 1000)
    if in_file:
        temp_file = StringIO()
        temp_file.write(new_preamble)

    preamble_message = "See file below!" if in_file else "```tex\n{}\n```".format(new_preamble)

    embed = discord.Embed(title="New Server Preamble", color=discord.Colour.blue()) \
        .set_author(name="{} ({})".format(ctx.author, ctx.authid),
                    icon_url=ctx.author.avatar_url) \
        .add_field(name="Preamble", value=preamble_message, inline=False) \
        .add_field(name="Server", value="{} ({})".format(ctx.server.name, ctx.server.id), inline=False) \
        .set_footer(text=datetime.utcnow().strftime("Sent from {} at %-I:%M %p, %d/%m/%Y".format(ctx.server.name if ctx.server else "private message")))

    await ctx.bot.send_message(ctx.bot.objects["preamble_channel"], embed=embed)
    if in_file:
        temp_file.seek(0)
        await ctx.bot.send_file(ctx.bot.objects["preamble_channel"], fp=temp_file, filename=file_name)
    await ctx.reply("Your server preamble has been updated!")


@cmds.cmd("preamble",
          category="Maths",
          short_help="Change how your LaTeX compiles",
          aliases=["texconfig"])
@cmds.execute("flags", flags=["reset", "replace", "add", "approve==", "remove", "retract", "deny=="])
async def cmd_preamble(ctx):
    """
    Usage:
        {prefix}preamble [code] [--reset] [--replace] [--remove]
    Description:
        Displays the preamble currently used for compiling your latex code.
        If [code] is provided, adds this to your preamble, or replaces it with --replace
        Note that preambles must currently be approved by a bot manager, to prevent abuse.
    Flags:2
        reset::  Resets your preamble to the default.
        replace:: replaces your preamble with this code
        remove:: Removes all lines from your preamble containing the given text.
        retract:: Retract a pending preamble.
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

    if ctx.flags["reset"]:
        await ctx.data.users.set(ctx.authid, "latex_preamble", None)
        await ctx.data.users.set(ctx.authid, "limbo_preamble", "")
        await ctx.reply("Your LaTeX preamble has been reset to the default!")
        return

    if ctx.flags["retract"]:
        await ctx.data.users.set(ctx.authid, "limbo_preamble", "")
        await ctx.reply("You have retracted your preamble request.")
        return

    if not ctx.arg_str and not ctx.msg.attachments:
        await show_config(ctx)
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

    current_preamble = await ctx.data.users.get(ctx.authid, "limbo_preamble")
    if not current_preamble:
        current_preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
        if not current_preamble and ctx.server:
            current_preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
        if not current_preamble:
            current_preamble = default_preamble

    if not ctx.flags["replace"]:
        new_preamble = "{}\n{}".format(current_preamble, new_preamble)

    if ctx.flags["remove"]:
        # TODO: Fix, Ugly
        if ctx.arg_str not in current_preamble:
            await ctx.reply("Couldn't find this in any line of your preamble!")
            return
        new_preamble = "\n".join([line for line in current_preamble.split("\n") if ctx.arg_str not in line])

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
    if not preamble and ctx.server:
        preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
    if not preamble:
        preamble = default_preamble

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
    bot.objects["server_tex_listeners"] = {}
    for serverid in await bot.data.servers.find("latex_listen_enabled", True, read=True):
        channels = await bot.data.servers.get(serverid, "maths_channels")
        bot.objects["server_tex_listeners"][str(serverid)] = channels if channels else []
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
    if ctx.server and (ctx.server.id in ctx.bot.objects["server_tex_listeners"]) and ctx.bot.objects["server_tex_listeners"][ctx.server.id] and not (ctx.ch.id in ctx.bot.objects["server_tex_listeners"][ctx.server.id]):
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
        ctx = MCtx(bot=bot, message=after)
        await tex_listener(ctx)
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
    bot.data.users.ensure_exists("tex_listening", "latex_keepmsg", "latex_colour", "latex_alwaysmath", "latex_allowother", "latex_showname", shared=False)
    bot.data.users.ensure_exists("latex_preamble", "limbo_preamble", shared=True)
    bot.data.servers.ensure_exists("maths_channels", "latex_listen_enabled", shared=False)

    bot.add_after_event("ready", register_tex_listeners)
    bot.add_after_event("message_edit", tex_edit_listener)
    bot.after_ctx_message(tex_listener)
