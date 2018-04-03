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
async def snip_user_lookup(ctx, in_server=False):
    """
    Snippet to look up a user, assuming a partial user sting, mention, or id was given as the first arg.

    Expected to interactively ask and select if multiple users are found.
    Sets ctx.objs["found_user"]
    """
    ctx.objs["found_user"] = await ctx.find_user(ctx.params[0], in_server, interactive=True)
    return ctx.objs["found_user"]


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
