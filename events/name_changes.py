async def store_names(bot, before, after):
    if before.name != after.name:
        history = await bot.data.users.get(before.id, "name_history")
        history = history if history else []
        names = [before.name, after.name]
        history.extend([name for name in names if name not in history])
        await bot.data.users.set(before.id, "name_history", history)

    if before.nick != after.nick:
        history = await bot.data.servers.get(before.server.id, "nickname_history")
        history = history if history else {}
        member_hist = history[before.id] if before.id in history else []
        names = [before.nick, after.nick]
        member_hist.extend([name for name in names if name not in history and name is not None])
        history[before.id] = member_hist
        await bot.data.servers.set(before.server.id, "nickname_history", history)


def load_into(bot):
    # TODO: Ensure name_history column exists for user
    # TODO: user, server keypair for nickname_history
    bot.add_after_event("member_update", store_names)
