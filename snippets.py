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
    ctx.objs["found_user"] = await ctx.find_user(ctx.params[0], in_server)
    return ctx.objs["found_user"]
