from paraCH import paraCH
import discord

cmds = paraCH()
# Provides giveme


@cmds.cmd("giveme",
          category="Moderation",
          short_help="Request, list and modify the self assignable roles.",
          aliases=["selfrole", "srole", "iam", "iamnot"])
@cmds.require("in_server")
@cmds.execute("flags", flags=["add", "remove", "list"])
async def cmd_giveme(ctx):
    """
    Usage:
        {prefix}giveme role1, role2, role3 [--list] [--add] [--remove]
    Description:
        Toggle your self assignable roles, or manage the server's self assignable roles.
        Roles will be created if they do not exist.
        If no roles are given, does an interactive lookup.
    Flags:2
        list:: List the self-assignable roles in the server.
        add:: Add new self assignable roles.
        remove:: Remove self assignable roles.
    Example:
        {prefix}selfrole Homotopy Theory --add
        {prefix}giveme Homotopy
        {prefix}selfrole Homotopy --remove
    """
    roles = await ctx.data.servers.get(ctx.server.id, "self_roles")
    self_roles = []
    roles = roles if roles else []
    for role in roles:
        actualrole = discord.utils.get(ctx.server.roles, id=role)
        if actualrole:
            self_roles.append(actualrole)

    mod = False
    if ctx.flags["add"] or ctx.flags["remove"]:
        (code, msg) = await cmds.checks["in_server_has_mod"](ctx)
        if code != 0:
            ctx.cmd_err = (code, msg)
            return
        mod = True

    if ctx.flags["list"]:
        if self_roles:
            role_list = "```css\n{}\n```".format(", ".join([role.name for role in self_roles]))
            msg = "**Self assignable roles for this server**:\
                \n{roles}\
                \nUse `{prefix}giveme role1, role2,...` to add or remove your self assignable roles.\
                \nType the command again to remove the roles.".format(roles=role_list, prefix=ctx.used_prefix)
        else:
            msg = "No self assignable roles have been set for this server. Roles may be set using the `--add` flag on this command or the selfroles config option."
        await ctx.reply(msg)
        return

    if not ctx.arg_str:
        if not self_roles:
            msg = "No self assignable roles have been set for this server. Roles may be set using the `--add` flag on this command or the selfroles config option."
            await ctx.reply(msg)
            return
        else:
            lines = [role.name for role in self_roles]
            selection = await ctx.selector("Please select which self assignable role you wish to toggle.", lines)
            if selection is None:
                return
            roles = [lines[selection]]
    else:
        roles = ctx.arg_str.split(",")
    msg_roles = []
    for role in roles:
        msg_role = await ctx.find_role(role.strip(), create=True if mod else False, interactive=True, collection=None if ctx.flags["add"] else self_roles)
        if msg_role is None:
            if role.isdigit() and ctx.flags["remove"]:
                continue
            else:
                return
        msg_roles.append(msg_role)

    if mod:
        if ctx.flags["remove"]:
            for role in msg_roles:
                if role in self_roles:
                    self_roles.remove(role)
        else:
            self_roles.extend([role for role in msg_roles if role not in self_roles])
        await ctx.data.servers.set(ctx.server.id, "self_roles", [role.id for role in self_roles])
        await ctx.reply("Server self roles updated!")
        return

    bad_roles = [role for role in msg_roles if role not in self_roles]
    if bad_roles:
        await ctx.reply("`{}` is not a self-assignable role.".format(bad_roles[0].name))
        return

    for role in msg_roles:
        try:
            if role in ctx.author.roles:
                await ctx.bot.remove_roles(ctx.author, role)
            else:
                await ctx.bot.add_roles(ctx.author, role)
        except discord.Forbidden:
            await ctx.reply("I don't have permissions to update these roles for you!")
            return
    await ctx.reply("Updated your roles!")
    # TODO: Make interactive system with no arg_str, with comma separated list of numbers selecting roles
    # This probably needs a check func passed to the wait_for


def load_into(bot):
    bot.data.servers.ensure_exists("self_roles", shared=True)
