async def enable_latex_listening(bot, server):
    listening = await bot.data.servers.get(server.id, "latex_listen_enabled")

    if listening is None:
        await bot.data.servers.set(server.id, "latex_listen_enabled", True)

        listens = bot.objects["server_tex_listeners"]
        channels = await bot.data.servers.get(server.id, "maths_channels")
        listens[str(server.id)] = channels if channels else []


def load_into(bot):
    bot.data.servers.ensure_exists("latex_listen_enabled", shared=False)

    bot.add_after_event("server_join", enable_latex_listening)
