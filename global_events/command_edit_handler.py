async def handle_command_edit(bot, before, after):
    if before.content != after.content:
        if before.id in bot.objects["command_cache"]:
            ctx = bot.objects["command_cache"][before.id]
            if ctx.cmd.edit_handler is not None:
                await ctx.cmd.edit_handler(ctx, after)


def load_into(bot):
    bot.add_after_event("message_edit", handle_command_edit, priority=5)
