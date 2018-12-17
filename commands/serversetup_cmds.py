from paraCH import paraCH
import discord
import string
import asyncio

cmds = paraCH()


async def _config_pages(ctx, serv_conf, value=True):
    """
    Builds the server configuration pages.
    """
    cats = {}
    pages = []
    sorted_pages = ctx.bot.objects["sorted_conf_pages"]

    for option in sorted(serv_conf):
        cat = serv_conf[option].category
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(option)
    for page in sorted_pages:
        page_name = page[0]
        page_cats = page[1]
        page_embed = discord.Embed(title="{} options:".format(page_name), color=discord.Colour.teal())
        for cat in page_cats:
            cat_msg = ""
            if cat not in cats:
                continue
            for option in cats[cat]:
                if value:
                    option_line = await serv_conf[option].hr_get(ctx)
                else:
                    option_line = serv_conf[option].desc
                cat_msg += "`​{}{}`:\t {}\n".format(" " * (12 - len(option)),
                                                    option, option_line)
            cat_msg += "\n"
            page_embed.add_field(name=cat, value=cat_msg, inline=False)
        page_embed.set_footer(text="Use {}config <option> [value] to see or set an option.".format(ctx.used_prefix))
        pages.append(page_embed)
    return pages


@cmds.cmd("config",
          category="Server Admin",
          short_help="Server configuration")
@cmds.require("in_server")
async def cmd_config(ctx):
    """
    Usage:
        {prefix}config | config help | config <option> [value]
    Description:
        Lists your current server configuration, shows option help, or sets an option.
        For example, "config join_ch #general" could be used to set your join message channel.
    """
    server_conf = ctx.server_conf.settings
    serv_conf = {}
    for setting in server_conf:
        serv_conf[server_conf[setting].vis_name] = server_conf[setting]
    if (ctx.params[0] in ["", "help"]) and len(ctx.params) == 1:
        pages = await _config_pages(ctx, serv_conf, value=True if ctx.params[0] == "" else False)
        await ctx.pager(pages, embed=True)
        return
    elif (ctx.params[0] == "help") and len(ctx.params) > 1:
        """
        Prints the description and possible values for the given option.
        """
        if ctx.params[1] not in serv_conf:
            await ctx.reply("Unrecognised option! See `serverconfig help` for all options.")
            return
        op = ctx.params[1]
        op_conf = serv_conf[op]
        msg = "Option help: ```\n{}.\nAcceptable input: {}.\nDefault value: {}```"\
            .format(op_conf.desc, op_conf.accept, await op_conf.dyn_default(ctx))
        await ctx.reply(msg)
    else:
        if ctx.params[0] not in serv_conf:
            await ctx.reply("Unrecognised option! See `{0.used_prefix}config help` for all options.".format(ctx))
            return
        if len(ctx.params) == 1:
            op = ctx.params[0]
            op_conf = serv_conf[op]
            msg = "Option help: ```\n{}.\nAcceptable input: {}.\nDefault value: {}```"\
                .format(op_conf.desc, op_conf.accept, await op_conf.dyn_default(ctx))
            msg += "Currently set to: {}".format(await op_conf.hr_get(ctx))
            await ctx.reply(msg)
        else:
            await serv_conf[ctx.params[0]].hr_set(ctx, ' '.join(ctx.params[1:]))
            if not ctx.cmd_err[0]:
                await ctx.reply("The setting was set successfully")


@cmds.cmd("rmrole",
          category="Server Admin",
          short_help="Deletes a role",
          aliases=["removerole", "remrole", "deleterole", "delrole"])
@cmds.require("has_manage_server")
async def cmd_rmrole(ctx):
    """
    Usage:
        {prefix}rmrole <rolename>
    Description:
        Deletes a role given by partial name or mention.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must provide a role to delete.")
        return
    # TODO: Letting find_role handle all input and output for finding.
    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return
    result = await ctx.ask("Are you sure you want to delete the role `{}`?".format(role.name))
    if result is None:
        await ctx.reply("Question timed out, aborting")
        return
    if result == 0:
        await ctx.reply("Aborting...")
        return
    try:
        await ctx.bot.delete_role(ctx.server, role)
    except discord.Forbidden:
        await ctx.reply("I am unable to delete that role, insufficient permissions.")
        return
    except Exception:
        await ctx.reply("I am unable to delete that role, integration managed.")
        return
    await ctx.reply("Successfully deleted the role.")


@cmds.cmd("bancmd",
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
        bans_str = "Current banned commands: `{}`".format("`, `".join(bans)) if bans else "There are no banned commands in this server!"
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


@cmds.cmd("editrole",
          category="Server Admin",
          short_help="Create or edit a server role.",
          aliases=["erole", "roleedit", "roledit", "editr"])
@cmds.require("in_server_has_mod")
@cmds.execute("flags", flags=["colour=", "color=", "name==", "perm==", "hoist=", "mention=", "pos=="])
async def cmd_editrole(ctx):
    """
    Usage:
        {prefix}editrole <rolename> [flags]
    Description:
        Modifies the specified role, either interactively (WIP), or using the provided flags (see below).
        This may also be used to create a role.
    Flags:
        --colour/--color <hex value>:  Change the colour
        --name <name>:  Change the name
        --perm <permission>: Add or remove a permission (WIP)
        --hoist <on/off>: Hoist or unhoist the role
        --mention <on/off>: Make the role mentionable, or not
        --pos < number | up | down | above <role> | below <role> >: Move the role in the heirachy (WIP)
    Examples:
        {prefix}erole Member --colour #0047AB --name Noob
        {prefix}erole Regular --pos above Member
    """
    role = await ctx.find_role(ctx.arg_str, create=True, interactive=True)
    if role is None:
        return
    edits = {}
    ctx.me = ctx.server.me  # Not actually required, just due to a bug in contextBot TODO
    if role >= ctx.me.top_role:
        await ctx.reply("The role specified is above or equal to my top role, aborting.")
        return
    if not (ctx.flags["colour"] or ctx.flags["color"] or ctx.flags["name"] or ctx.flags["perm"] or ctx.flags["hoist"] or ctx.flags["mention"] or ctx.flags["pos"]):
        await ctx.reply("Interactive role editing is a work in progress, please check back later!")
        return
    if ctx.flags["colour"] or ctx.flags["color"]:
        colour = ctx.flags["colour"] if ctx.flags["colour"] else ctx.flags["color"]
        hexstr = colour.strip("#")
        if not (len(hexstr) == 6 or all(c in string.hexdigits for c in hexstr)):
            await ctx.reply("Please provide a valid hex colour (e.g. #0047AB).")
            return
        edits["colour"] = discord.Colour(int(hexstr, 16))
    if ctx.flags["name"]:
        edits["name"] = ctx.flags["name"]
    if ctx.flags["perm"]:
        await ctx.reply("Sorry, perm modification is a work in progress. Please check back later!")
        return
    if ctx.flags["hoist"]:
        if ctx.flags["hoist"].lower() in ["enable", "yes", "on"]:
            hoist = True
        elif ctx.flags["hoist"].lower() in ["disable", "no", "off"]:
            hoist = False
        else:
            await ctx.reply("I don't understand your argument to --hoist! See the help for usage.")
            return
        edits["hoist"] = hoist
    if ctx.flags["mention"]:
        if ctx.flags["mention"].lower() in ["enable", "yes", "on"]:
            mention = True
        elif ctx.flags["mention"].lower() in ["disable", "no", "off"]:
            mention = False
        else:
            await ctx.reply("I don't understand your argument to --mention! See the help for usage.")
            return
        edits["mentionable"] = mention
    position = None
    if ctx.flags["pos"]:
        pos_flag = ctx.flags["pos"]
        if pos_flag.isdigit():
            position = int(pos_flag)
        elif pos_flag.lower() == "up":
            position = role.position + 1
        elif pos_flag.lower() == "down":
            position = role.position - 1
        elif pos_flag.startswith("above"):
            target_role = await ctx.find_role((' '.join(pos_flag.split(' ')[1:])).strip(), create=False, interactive=True)
            position = target_role.position + 1
        elif pos_flag.startswith("below"):
            target_role = await ctx.find_role((' '.join(pos_flag.split(' ')[1:])).strip(), create=False, interactive=True)
            position = target_role.position
        else:
            await ctx.reply("I didn't understand your argument to --pos. See the help for usage.")
#    msg = ""
    if position is not None:
        if position > ctx.me.top_role.position:
            await ctx.reply("The target position is above me, aborting.")
            return
        if position == 0:
            await ctx.reply("Can't move a role to position 0, aborting.")
            return
        try:
            await ctx.bot.move_role(ctx.server, role, position)
#            msg += "Moved role to position {}!".format(
        except discord.Forbidden:
            await ctx.reply("I am unable to move the role, insufficient permissions.")
            return
        except discord.HTTPException:
            await ctx.reply("Something went wrong while moving the role! Possibly I am of too low a rank.")
            return
    if edits:
        try:
            await ctx.bot.edit_role(ctx.server, role, **edits)
        except discord.Forbidden:
            await ctx.reply("I don't have enough permissions to make the specified edits.")
            return
    await ctx.reply("The role was modified successfully.")


@cmds.cmd("cleanch",
          category="Server Admin",
          short_help="Enable or disable automatic deletion on a channel.",
          aliases=["chclean"])
@cmds.require("has_manage_server")
async def cmd_cleanch(ctx):
    """
    Usage:
        {prefix}cleanch
    Description:
        Enables or disables automatic deletion of messages in a channel.
    """
    if ctx.server.id in ctx.bot.objects["cleaned_channels"]:
        ctx.bot.objects["cleaned_channels"][ctx.server.id] = []
    cleaned = ctx.bot.objects["cleaned_channels"][ctx.server.id]
    if ctx.ch.id in cleaned:
        cleaned.remove(ctx.ch.id)
        await ctx.reply("I have stopped auto-deleting messages in this channel")
    else:
        cleaned.append(ctx.ch.id)
        await ctx.reply("I will now auto-delete messages in this channel.")
    await ctx.bot.data.servers.set(ctx.server.id, "clean_channels", cleaned)
    return


async def channel_cleaner(ctx):
    if not ctx.server:
        return
    if not (ctx.server.id in ctx.bot.objects["cleaned_channels"] and ctx.ch.id in ctx.bot.objects["cleaned_channels"][ctx.server.id]):
        return
    await asyncio.sleep(30)
    try:
        await ctx.bot.delete_message(ctx.msg)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass


async def register_channel_cleaners(bot):
    cleaned_channels = {}
    for server in bot.servers:
        channels = await bot.data.servers.get(server.id, "clean_channels")
        if channels:
            cleaned_channels[server.id] = channels
    bot.objects["cleaned_channels"] = cleaned_channels
    await bot.log("Loaded {} servers with channels to clean.".format(len(cleaned_channels)))


def load_into(bot):
    bot.add_after_event("ready", register_channel_cleaners)
    bot.after_ctx_message(channel_cleaner)
