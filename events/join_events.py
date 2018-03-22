from contextBot.Context import Context


def load_into(bot):
    @bot.event
    async def on_member_join(member):
        ctx = Context(bot=bot, member=member)
        if not (await ctx.server_conf.join.get(ctx.data, ctx.server)):
            return

        ch = await ctx.server_conf.join_ch.get(ctx)
        msg = await ctx.server_conf.join_msg.get(ctx)

        if not ch:
            return

        ch = ctx.server.get_channel(ch)

        if not ch:
            return

        msg = await ctx.ctx_format(msg)
        await ctx.bot.send_message(ch, msg)

    @bot.event
    async def on_member_remove(member):
        ctx = Context(bot=bot, member=member)
        if not (await ctx.server_conf.leave.get(ctx)):
            return

        ch = await ctx.server_conf.leave_ch.get(ctx)
        msg = await ctx.server_conf.leave_msg.get(ctx)

        if not ch:
            return

        ch = ctx.server.get_channel(ch)

        if not ch:
            return

        msg = await ctx.ctx_format(msg)
        await ctx.bot.send_message(ch, msg)
