import discord
from contextBot.Context import Context

"""
star format:
    source_msg_id,
    out_msg_id
"""


async def register_starboard_emojis(bot):
    bot.objects["server_starboard_emojis"] = {}
    bot.objects["server_starboards"] = {}
    for serverid in await bot.data.servers.find("starboard_enabled", True, read=True):
        emoji = await bot.data.servers.get(str(serverid), "starboard_emoji")
        emoji = emoji if emoji else bot.s_conf.starboard_emoji.default
        bot.objects["server_starboard_emojis"][str(serverid)] = emoji
        bot.objects["server_starboards"][str(serverid)] = {}
    await bot.log("Loaded {} servers with active starboards.".format(len(bot.objects["server_starboard_emojis"])))


async def starboard_listener(bot, reaction, user):
    message = reaction.message
    if not message.server:
        return

    if message.server.id not in bot.objects["server_starboard_emojis"]:
        return
    sb_emoji = bot.objects["server_starboard_emojis"][message.server.id]
    emoji = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.id

    if emoji != sb_emoji:
        return

    ctx = Context(bot=bot, message=message, server=message.server)

    sb_channel = await ctx.server_conf.starboard_channel.get(ctx)
    if not sb_channel:
        return

    sb_channel = ctx.server.get_channel(sb_channel)
    if not sb_channel:
        return

    if message.embeds:
        return

    server_board = bot.objects["server_starboards"][ctx.server.id]

    if reaction.count == 0:
        if message.id in server_board:
            try:
                await bot.delete_message(await bot.get_message(sb_channel, server_board[message.id]))
            except discord.NotFound:
                pass
            server_board.pop(message.id, None)
            return

    post_msg = "{} {} in {}".format(str(reaction.emoji), reaction.count, message.channel.mention)

    embed = discord.Embed(colour=discord.Colour.light_grey(), description=message.content)
    embed.set_author(name="{user.name}".format(user=message.author),
                     icon_url=message.author.avatar_url)
    embed.add_field(name="Message link", value="[Click to jump to message]({})".format(ctx.msg_jumpto(message)), inline=False)
    embed.set_footer(text=message.timestamp.strftime("Sent at %-I:%M %p, %d/%m/%Y"))
    if message.attachments and "height" in message.attachments[0]:
        embed.set_image(url=message.attachments[0]["proxy_url"])

    if message.id in server_board:
        star = server_board[message.id]
        out_msg = await bot.get_message(sb_channel, star)
        if not out_msg:
            return
        await bot.edit_message(out_msg, new_content=post_msg, embed=embed)
    else:
        out_msg = await ctx.send(sb_channel, message=post_msg, embed=embed)
        server_board[message.id] = out_msg.id


def load_into(bot):
    bot.data.servers.ensure_exists("starboard_channel", "starboard_enabled", "starboard_emoji", shared=False)

    bot.add_after_event("reaction_add", starboard_listener)
    bot.add_after_event("reaction_remove", starboard_listener)
    bot.add_after_event("ready", register_starboard_emojis)
