import discord

async def recall_roles(bot, member):
    persist = await bot.data.servers.get(member.server.id, "role_persistence")
    if persist is not None and not persist:
        return

    stored = await bot.data.servers.get(member.server.id, "persistent_roles")
    if member.id not in stored:
        return

    for role in stored[member.id]:
        actual_role = discord.utils.get(member.server.roles, id=role)
        if not actual_role:
            continue
        try:
            await bot.add_roles(member, actual_role)
        except discord.Forbidden:
            pass


async def store_roles(bot, member):
    role_list = [role.id for role in member.roles]
    stored = await bot.data.servers.get(member.server.id, "persistent_roles")
    if not stored:
        stored = {}
    stored[member.id] = role_list
    await bot.data.servers.set(member.server.id, "persistent_roles", stored)

def load_into(bot):
    # TODO: Ensure persistent_roles and role_persistence columns exist
    bot.add_after_event("member_join", recall_roles)
    bot.add_after_event("member_remove", store_roles)
