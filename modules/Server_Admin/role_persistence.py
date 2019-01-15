import discord


async def recall_roles(bot, member):
    persist = await bot.data.servers.get(member.server.id, "role_persistence")
    if persist is not None and not persist:
        return

    stored = await bot.data.members.get(member.server.id, member.id, "persistent_roles")
    if stored is None or not stored:
        return

    for role in stored:
        actual_role = discord.utils.get(member.server.roles, id=role)
        if actual_role:
            try:
                await bot.add_roles(member, actual_role)
            except discord.Forbidden:
                pass


async def store_roles(bot, member):
    role_list = [role.id for role in member.roles]
    await bot.data.members.set(member.server.id, member.id, "persistent_roles", role_list)


def load_into(bot):
    bot.data.servers.ensure_exists("role_persistence")
    bot.data.members.ensure_exists("persistent_roles")

    bot.add_after_event("member_join", recall_roles)
    bot.add_after_event("member_remove", store_roles)
