import discord

checks = {}


def check(name):
    def decorator(func):
        checks[name.lower()] = func
        return func
    return decorator


@check("master_perm")
async def check_master_perm(ctx):
    if int(ctx.authid) not in ctx.bot.bot_conf.getintlist("masters"):
        return (1, "This requires you to be one of my masters!")
    return (0, "")


@check("exec_perm")
async def check_exec_perm(ctx):
    (code, msg) = await checks["master_perm"](ctx)
    if code == 0:
        return (code, msg)
    if int(ctx.authid) not in ctx.bot.bot_conf.getintlist("execWhiteList"):
        return (1, "You don't have the required Exec perms to do this!")
    return (0, "")


@check("dev_perm")
async def check_dev_perm(ctx):
    (code, msg) = await checks["exec_perm"](ctx)
    if code == 0:
        return (code, msg)
    if int(ctx.authid) not in ctx.bot.bot_conf.getintlist("developers"):
        return (1, "You need to be one of my developers to do this!")
    return (0, "")


@check("contrib_perm")
async def check_contrib_perm(ctx):
    (code, msg) = await checks["manager_perm"](ctx)
    if code == 0:
        return (code, msg)
    if int(ctx.authid) not in ctx.bot.bot_conf.getintlist("contributors"):
        return (1, "You need to be a bot contributor to do this!")
    return (0, "")


@check("manager_perm")
async def check_manager_perm(ctx):
    (code, msg) = await checks["exec_perm"](ctx)
    if code == 0:
        return (code, msg)
    if int(ctx.authid) not in ctx.bot.bot_conf.getintlist("managers"):
        return (1, "You lack the required bot manager perms to do this!")
    return (0, "")


@check("can_embed")
async def check_can_embed(ctx):
    pass


@check("in_server")
async def check_in_server(ctx):
    if not ctx.server:
        return (1, "This can only be used in a server!")
    return (0, "")


@check("has_manage_server")
async def perm_manage_server(ctx):
    if (ctx.user is None) or (ctx.server is None):
        return (2, "An internal error occurred.")
    if not (ctx.user.server_permissions.manage_server or
            ctx.user.server_permissions.administrator):
        return (1, "You lack the `Manage Server` permission on this server!")
    return (0, "")


@check("has_ban_members")
async def perm_ban_members(ctx):
    if (ctx.user is None) or (ctx.server is None):
        return (2, "An internal error occurred.")
    if not (ctx.user.server_permissions.ban_members or
            ctx.user.server_permissions.administrator):
        return (1, "You lack the `Ban Members` permission on this server!")
    return (0, "")

@check("has_kick_members")
async def perm_kick_members(ctx):
    if (ctx.user is None) or (ctx.server is None):
        return (2, "An internal error occurred.")
    if not (ctx.user.server_permissions.kick_members or
            ctx.user.server_permissions.administrator):
        return (1, "You lack the `Kick Members` permission on this server!")
    return (0, "")

# Mod action checks

@check("in_server_has_mod")
async def check_in_server_has_mod(ctx):
    if (ctx.user is None) or (ctx.server is None):
        return (2, "An internal error occurred.")
    mod_role = await ctx.server_conf.mod_role.get(ctx)
    if mod_role:
        mod_role = discord.utils.get(ctx.server.roles, id=mod_role)
    if not mod_role:
        (code, msg) = await checks["has_manage_server"](ctx)
        return (code, msg)
    if mod_role in ctx.member.roles:
        return (0, "")
    else:
        return (1, "You don't have the moderator role in this server!")



@check("in_server_can_ban")
async def check_in_server_can_ban(ctx):
    """
    TODO: Need to do proper custom checks here
    """
    (code, msg) = await checks["in_server_has_mod"](ctx)
    if code == 0:
        return (code, msg)
    (code, msg) = await checks["has_ban_members"](ctx)
    if code == 0:
        return (code, msg)
    else:
        return (1, "You don't have permission to ban users in this server!")
    return (0, "")

@check("in_server_can_unban")
async def check_in_server_can_unban(ctx):
    """
    TODO: Need to do proper custom checks here
    """
    (code, msg) = await checks["in_server_has_mod"](ctx)
    if code == 0:
        return (code, msg)
    (code, msg) = await checks["has_ban_members"](ctx)
    if code == 0:
        return (code, msg)
    else:
        return (1, "You don't have permission to unban users in this server!")
    return (0, "")

@check("in_server_can_hackban")
async def check_in_server_can_ban(ctx):
    """
    TODO: Need to do proper custom checks here
    """
    (code, msg) = await checks["in_server_has_mod"](ctx)
    if code == 0:
        return (code, msg)
    (code, msg) = await checks["has_ban_members"](ctx)
    if code == 0:
        return (code, msg)
    else:
        return (1, "You don't have permission to hackban users in this server!")
    return (0, "")

@check("in_server_can_kick")
async def check_in_server_can_kick(ctx):
    """
    TODO: Need to do proper custom checks here
    """
    (code, msg) = await checks["in_server_has_mod"](ctx)
    if code == 0:
        return (code, msg)
    (code, msg) = await checks["has_kick_members"](ctx)
    if code == 0:
        return (code, msg)
    else:
        return (1, "You don't have permission to kick users in this server!")
    return (0, "")


@check("in_server_can_softban")
async def check_in_server_can_softban(ctx):
    """
    TODO: Need to do proper custom checks here
    """
    (code, msg) = await checks["in_server_has_mod"](ctx)
    if code == 0:
        return (code, msg)
    (code, msg) = await checks["has_ban_members"](ctx)
    if code == 0:
        return (code, msg)
    else:
        return (1, "You don't have permission to softban users in this server!")
    return (0, "")

@check("in_server_can_mute")
async def check_in_server_can_softban(ctx):
    """
    TODO: Need to do proper custom checks here
    """
    (code, msg) = await checks["in_server_has_mod"](ctx)
    if code == 0:
        return (code, msg)
    else:
        return (1, "You don't have permission to mute users in this server!")
    return (0, "")

@check("in_server_can_unmute")
async def check_in_server_can_softban(ctx):
    """
    TODO: Need to do proper custom checks here
    """
    (code, msg) = await checks["in_server_has_mod"](ctx)
    if code == 0:
        return (code, msg)
    else:
        return (1, "You don't have permission to unmute users in this server!")
    return (0, "")
