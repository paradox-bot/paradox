from contextBot.Context import Context
import discord
from datetime import datetime

statusdict = {"offline": "Offline/Invisible",
              "dnd": "Do Not Disturb",
              "online": "Online",
              "idle": "Idle/Away"}


async def log_join(bot, member):
    joinlog = await bot.data.servers.get(member.server.id, "joinlog_ch")
    if not joinlog:
        return
    joinlog = member.server.get_channel(joinlog)
    if not joinlog:
        return

    ctx = Context(bot=bot, member=member)

    user = member
    colour = (user.colour if user.colour.value else discord.Colour.light_grey())

    game = user.game if user.game else "Nothing"
    status = statusdict[str(user.status)]
    shared = "{} servers".format(len(list(filter(lambda m: m.id == user.id, ctx.bot.get_all_members()))))
    created_ago = "({} ago)".format(ctx.strfdelta(datetime.utcnow() - user.created_at))
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")

    prop_list = ["Status", "Playing", "Seen in", "Created at", ""]
    value_list = [status, game, shared, created, created_ago]
    desc = ctx.prop_tabulate(prop_list, value_list)

    embed = discord.Embed(type="rich", color=colour, description=desc)
    embed.set_author(name="New {usertype} joined: {user} (id: {user.id})".format(usertype="bot" if user.bot else "user", user=user),
                     icon_url=user.avatar_url,
                     url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)
    embed.set_footer(text=datetime.utcnow().strftime("Sent at %-I:%M %p, %d/%m/%Y"))

    await ctx.send(joinlog, embed=embed)


async def log_leave(bot, member):
    joinlog = await bot.data.servers.get(member.server.id, "joinlog_ch")
    if not joinlog:
        return
    joinlog = member.server.get_channel(joinlog)
    if not joinlog:
        return

    ctx = Context(bot=bot, member=member)

    user = member
    colour = (user.colour if user.colour.value else discord.Colour.light_grey())

    joined_ago = "({} ago)".format(ctx.strfdelta(datetime.utcnow() - user.joined_at))
    joined = user.joined_at.strftime("%-I:%M %p, %d/%m/%Y")
    usernames = await ctx.bot.data.users.get(user.id, "name_history")
    name_list = "{}{}".format("..., " if len(usernames) > 10 else "",
                              ", ".join(usernames[-10:])) if usernames else "No recent past usernames."
    nicknames = await ctx.bot.data.members.get(ctx.server.id, user.id, "nickname_history")
    nickname_list = "{}{}".format("..., " if len(nicknames) > 10 else "",
                                  ", ".join(nicknames[-10:])) if nicknames else "No recent past nicknames."

    roles = [r.name for r in user.roles if r.name != "@everyone"]
    roles = ('`' + '`, `'.join(roles) + '`') if roles else "None"

    prop_list = ["Past names", "Past nicks", "Joined at", "", "Roles"]
    value_list = [name_list, nickname_list, joined, joined_ago, roles]
    desc = ctx.prop_tabulate(prop_list, value_list)

    embed = discord.Embed(type="rich", color=colour, description=desc)
    embed.set_author(name="{usertype} left: {user} (id: {user.id})".format(usertype="Bot" if user.bot else "User", user=user),
                     icon_url=user.avatar_url,
                     url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)
    embed.set_footer(text=datetime.utcnow().strftime("Sent at %-I:%M %p, %d/%m/%Y"))

    await ctx.send(joinlog, embed=embed)


def load_into(bot):
    bot.data.servers.ensure_exists("joinlog_ch", shared=False)
    bot.data.users.ensure_exists("name_history", shared=True)
    bot.data.members.ensure_exists("nickname_history", shared=True)

    bot.add_after_event("member_join", log_join)
    bot.add_after_event("member_remove", log_leave)
