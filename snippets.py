snippets = {}


def snip(name):
    def decorator(func):
        snippets[name] = func
        return func
    return decorator


@snip("serverlist")
async def snip_serverlist(ctx):
    servs = [(s.name, s.owner.name) for s in ctx.client.servers]
    servs.sort(key=lambda tup: tup[1].lower())
    servlist = ["{:^25} - {:^15}".format(st[0], st[1]) for st in servs]
    await ctx.reply("```" + "\n".join(servlist) + "```")
