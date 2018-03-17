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
