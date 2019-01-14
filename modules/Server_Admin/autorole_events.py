import discord

async def give_autorole(bot, member):
    server = member.server
    autorole = await bot.data.servers.get(server.id, "guild_autorole_bot" if ctx.member.bot else "guild_autorole")
    if not autorole:
        return

    autorole = discord.utils.get(server.roles, id=autorole)
    if not autorole:
        return

    try:
        await bot.add_roles(member, autorole)
    except Exception:
        """
        TODO: Alert whoever gets bot errors in this server.
        """
        pass

async def give_autoroles(bot, member):
    server = member.server
    autoroles = await bot.data.servers.get(server.id, "guild_autoroles")
    if not autoroles:
        return

    autoroles = [discord.utils.get(server.roles, id=autorole) for autorole in autoroles]
    for autorole in autoroles:
        if autorole:
            try:
                await ctx.bot.add_roles(ctx.member, autorole)
            except Exception:
                pass


def load_into(bot):
    bot.data.servers.ensure_exists("guild_autorole", "guild_autorole_bot", "guild_autoroles", shared=False)

    bot.add_after_event("member_join", give_autorole)
    bot.add_after_event("member_join", give_autoroles)
