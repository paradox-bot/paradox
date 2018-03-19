from contextBot.Context import Context


def load_into(bot):
    @bot.event
    async def on_member_join(member):
        ctx = Context(bot=bot, member=member)
        if not ctx.bot.serv_conf["join"].get(ctx.data, ctx.server):
            return

        ch = ctx.bot.serv_conf["join_ch"].get(ctx.data, ctx.server)
        msg = ctx.bot.serv_conf["join_msg"].get(ctx.data, ctx.server)

        if not ch:
            return

        ch = ctx.server.get_channel(ch)

        if not ch:
            return

        msg = await ctx.para_format(msg)
        await ctx.client.send_message(ch, msg)

    @bot.event
    async def on_member_remove(member):
        ctx = Context(bot=bot, member=member)
        if not ctx.bot.serv_conf["leave"].get(ctx.data, ctx.server):
            return

        ch = ctx.bot.serv_conf["leave_ch"].get(ctx.data, ctx.server)
        msg = ctx.bot.serv_conf["leave_msg"].get(ctx.data, ctx.server)

        if not ch:
            return

        ch = ctx.server.get_channel(ch)

        if not ch:
            return

        msg = await ctx.para_format(msg)
        await ctx.client.send_message(ch, msg)
