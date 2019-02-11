snippets = {}


def snip(name):
    def decorator(func):
        snippets[name] = func
        return func

    return decorator


@snip("serverlist")
async def snip_serverlist(ctx):
    servs = [(s.name, s.owner.name) for s in ctx.bot.servers]
    servs.sort(key=lambda tup: tup[1].lower())
    servlist = ["{:^25} - {:^15}".format(st[0], st[1]) for st in servs]
    await ctx.reply("```" + "\n".join(servlist) + "```", split=True, code=True)


@snip("user_lookup")
async def snip_user_lookup(ctx, in_server=False, greedy=False, func=None):
    """
    Snippet to look up a user, assuming a partial user sting, mention, or id was given as the first arg.

    Expected to interactively ask and select if multiple users are found.
    Sets ctx.objs["found_user"]
    If greedy is set uses the entire arg-str to lookup the
    """
    if not ctx.arg_str or (in_server and not ctx.server):
        ctx.objs["found_user"] = None
        return None
    content = func(ctx) if func is not None else (ctx.arg_str if greedy else ctx.params[0])
    ctx.objs["found_user"] = await ctx.find_user(content, in_server, interactive=True)
    return ctx.objs["found_user"]


@snip("dm")
async def snip_dm(ctx, user_info=None, message=None):
    """
    Does a lookup on the provided user string and dms them the given message
    """
    user = await ctx.find_user(user_info, in_server=False, interactive=True)
    if not user:
        await ctx.reply("Couldn't find the user")
        return
    await ctx.send(user, message)


@snip("rep cooldown")
async def snip_rep_cooldown(ctx, userid=None):
    """
    Quick rep cooldown, for testing.
    """
    if not userid:
        userid = ctx.authid
    await ctx.data.users.set(userid, "last_rep_time", "0")
    await ctx.reply("The cooldown has been reset")


@snip("flags")
async def snip_flags(ctx, flags=[], override=True):
    (params, arg_str, flags) = await ctx.parse_flags(ctx.arg_str, flags)
    ctx.flags = flags
    if override:
        ctx.params = params
        ctx.arg_str = arg_str
    else:
        ctx.flagged_params = params
        ctx.flagged_arg_str = arg_str
    return flags
