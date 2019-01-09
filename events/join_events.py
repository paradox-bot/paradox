from contextBot.Context import Context
import discord
from datetime import datetime

# TODO: Break this into separate modules

def load_into(bot):
    @bot.event
    async def on_member_join(member):
        ctx = Context(bot=bot, member=member)

        autorole = (await ctx.server_conf.guild_autorole_bot.get(ctx)) if ctx.member.bot else (await ctx.server_conf.guild_autorole.get(ctx))
        autorole = discord.utils.get(ctx.server.roles, id=autorole)
        if autorole:
            try:
                await ctx.bot.add_roles(ctx.member, autorole)
            except Exception:
                """
                TODO: Alert whoever gets bot errors in this server.
                """
                pass

        autoroles = await ctx.server_conf.guild_autoroles.get(ctx)
        autoroles = autoroles if autoroles else []
        autoroles = [discord.utils.get(ctx.server.roles, id=autorole) for autorole in autoroles]
        for autorole in autoroles:
            if autorole:
                try:
                    await ctx.bot.add_roles(ctx.member, autorole)
                except Exception:
                    pass

        if (await ctx.server_conf.join_msgs_enabled.get(ctx)):
            ch = await ctx.server_conf.join_ch.get(ctx)
            msg = await ctx.server_conf.join_msgs_msg.get(ctx)

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
        if (await ctx.server_conf.leave_msgs_enabled.get(ctx)):
            ch = await ctx.server_conf.leave_ch.get(ctx)
            msg = await ctx.server_conf.leave_msgs_msg.get(ctx)

            if not ch:
                return

            ch = ctx.server.get_channel(ch)

            if not ch:
                return

            msg = await ctx.ctx_format(msg)
            await ctx.bot.send_message(ch, msg)
