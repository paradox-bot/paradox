async def store_names(bot, before, after):
    if before.name != after.name:
        history = await bot.data.users.get(before.id, "name_history")
        history = history if history else []
        names = [before.name, after.name]
        history.extend([name for name in names if name not in history])
        await bot.data.users.set(before.id, "name_history", history)

    if before.nick != after.nick:
        history = await bot.data.members.get(before.server.id, before.id, "nickname_history")
        history = history if history else []
        names = [before.nick, after.nick]
        history.extend([name for name in names if name not in history and name is not None])
        await bot.data.members.set(before.server.id, before.id, "nickname_history", history)


def load_into(bot):
    bot.data.users.ensure_exists("name_history")
    bot.data.members.ensure_exists("nickname_history")
    bot.add_after_event("member_update", store_names)
