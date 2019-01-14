async def send_join_msg(bot, member):
    ch = await bot.data.servers.get(member.server.id, "join_ch")
    if not ch:
        return

    ch = member.server.get_channel(ch)
    if not ch:
        return

    ctx = bot.make_ctx(member=member)

    msg = await bot.s_conf.join_msgs_msg.get(ctx)
    if not msg:
        return

    msg = await ctx.ctx_format(msg)
    await bot.send_message(ch, msg)


async def send_leave_msg(bot, member):
    ch = await bot.data.servers.get(member.server.id, "leave_ch")
    if not ch:
        return

    ch = member.server.get_channel(ch)
    if not ch:
        return

    ctx = bot.make_ctx(member=member)

    msg = await bot.s_conf.leave_msgs_msg.get(ctx)
    if not msg:
        return

    msg = await ctx.ctx_format(msg)
    await bot.send_message(ch, msg)


def load_into(bot):
    bot.data.servers.ensure_exists("join_ch", "join_msgs_msg", "leave_ch", "leave_msgs_msg", shared=False)

    bot.add_after_event("member_join", send_join_msg)
    bot.add_after_event("member_remove", send_leave_msg)
