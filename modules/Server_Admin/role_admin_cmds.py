from paraCH import paraCH
import discord
import string

cmds = paraCH()


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
    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return
    if role.managed:
        await ctx.reply("⚠ This role is managed by an integration. You will have to reinvite its respective bot to recover the role.")
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
        await ctx.reply("I can't delete the `@everyone` role.")
        return
    await ctx.reply("Successfully deleted the role.")


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

"""
@cmds.cmd("roledesc",
          category="Server Admin",
          short_help="Set a role description",
          flags=["clear", "set="])
@cmds.require("has_manage_server")
async def cmd_roledesc(ctx):
    "
    Usage:
        {prefix}roledesc <rolename> [--set description] [--clear]
    Description:
        Set or clear the description for the provided role.
        The role description is shown in {prefix}roleinfo.
    Examples:
        {prefix}roledesc {msg.server.owner.top_role.name} --set The all powerful.
    "
    role = await ctx.find_role(ctx.arg_str, create=True, interactive=True)
    if role is None:
        return

"""
