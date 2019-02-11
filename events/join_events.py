from datetime import datetime

import discord
from contextBot.Context import Context

# TODO: Break this into separate modules


def load_into(bot):
    @bot.event
    async def on_member_join(member):
        ctx = Context(bot=bot, member=member)

        autorole = (await ctx.server_conf.guild_autorole_bot.get(ctx)
                    ) if ctx.member.bot else (
                        await ctx.server_conf.guild_autorole.get(ctx))
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
        autoroles = [
            discord.utils.get(ctx.server.roles, id=autorole)
            for autorole in autoroles
        ]
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

        joinlog = await ctx.server_conf.joinlog_ch.get(ctx)
        if joinlog:
            joinlog = ctx.server.get_channel(joinlog)
            if not joinlog:
                return
            user = member
            statusdict = {
                "offline": "Offline/Invisible",
                "dnd": "Do Not Disturb",
                "online": "Online",
                "idle": "Idle/Away"
            }
            colour = (user.colour
                      if user.colour.value else discord.Colour.light_grey())

            game = user.game if user.game else "Nothing"
            status = statusdict[str(user.status)]
            shared = "{} servers".format(
                len(
                    list(
                        filter(lambda m: m.id == user.id,
                               ctx.bot.get_all_members()))))
            created_ago = "({} ago)".format(
                ctx.strfdelta(datetime.utcnow() - user.created_at))
            created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")

            prop_list = ["Status", "Playing", "Seen in", "Created at", ""]
            value_list = [status, game, shared, created, created_ago]
            desc = ctx.prop_tabulate(prop_list, value_list)

            embed = discord.Embed(type="rich", color=colour, description=desc)
            embed.set_author(
                name="New {type} joined: {user} (id: {user.id})".format(
                    type="bot" if user.bot else "user", user=user),
                icon_url=user.avatar_url,
                url=user.avatar_url)
            embed.set_thumbnail(url=user.avatar_url)
            embed.set_footer(
                text=datetime.utcnow().strftime("Sent at %-I:%M %p, %d/%m/%Y"))

            await ctx.send(joinlog, embed=embed)

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
