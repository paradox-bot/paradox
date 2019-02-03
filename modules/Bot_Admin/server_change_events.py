from contextBot.Context import Context
import discord
from datetime import datetime

# Provides logging events for when the bot joins and leaves servers

async def log_left_server(bot, server):
    owner = server.owner
    icon = server.icon_url
    servers = bot.servers

    embed = discord.Embed(title="`{0.name} (ID: {0.id})`".format(server), colour=discord.Colour.red())
    embed.set_author(name="Left server!")
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value="{0.name} (ID: {0.id})".format(owner), inline=False)
    embed.add_field(name="Now playing in", value="{} servers".format(len(servers)), inline=False)
    embed.set_footer(text=datetime.utcnow().strftime("Left at %-I:%M %p, %d/%m/%Y"))
    log_ch = bot.objects["server_change_log_channel"]
    if log_ch:
        await bot.send_message(log_ch, embed=embed)

    status = await Context(bot=bot).ctx_format(bot.objects["GAME"])
    await bot.change_presence(game=discord.Game(name=status))


async def log_joined_server(bot, server):
    owner = server.owner
    icon = server.icon_url

    bots = 0
    known = 0
    unknown = 0
    other_members = list(set([mem.id for mem in bot.get_all_members() if mem.server != server]))

    for member in server.members:
        if member.bot:
            bots += 1
        elif member.id in other_members:
            known += 1
        else:
            unknown += 1

    mem1 = "people I know" if known != 1 else "person I know"
    mem2 = "new friends" if unknown != 1 else "new friend"
    mem3 = "bots" if bots != 1 else "bot"
    mem4 = "total members"
    known = "`{}`".format(known)
    unknown = "`{}`".format(unknown)
    bots = "`{}`".format(bots)
    total = "`{}`".format(server.member_count)
    mem_str = "{0:<5}\t{4},\n{1:<5}\t{5},\n{2:<5}\t{6}, and\n{3:<5}\t{7}.".format(known, unknown, bots, total, mem1, mem2, mem3, mem4)

    created = server.created_at.strftime("%-I:%M %p, %d/%m/%Y")

    embed = discord.Embed(title="`{0.name} (ID: {0.id})`".format(server), colour=owner.colour if owner.colour.value else discord.Colour.light_grey())
    embed.set_author(name="Joined server!")
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value="{0.name} (ID: {0.id})".format(owner), inline=False)
    embed.add_field(name="Region", value=bot.objects["regions"][str(server.region)], inline=False)
    embed.add_field(name="Created at", value="{}".format(created), inline=False)
    embed.add_field(name="Members", value=mem_str, inline=False)
    embed.add_field(name="Now playing in", value="{} servers".format(len(bot.servers)), inline=False)
    embed.set_footer(text=datetime.utcnow().strftime("Joined at %-I:%M %p, %d/%m/%Y"))

    log_ch = bot.objects["server_change_log_channel"]
    if log_ch:
        await bot.send_message(log_ch, embed=embed)

    status = await Context(bot=bot).ctx_format(bot.objects["GAME"])
    await bot.change_presence(game=discord.Game(name=status))


def load_into(bot):
    bot.add_after_event("server_join", log_joined_server, priority = 10)
    bot.add_after_event("server_remove", log_left_server, priority = 10)
