from paraCH import paraCH
import discord
from datetime import datetime

cmds = paraCH()


@cmds.cmd("ping",
          category="General",
          short_help="Checks the bot's latency")
async def cmd_ping(ctx):
    """
    Usage: {prefix}ping

    Checks the response delay of the bot.
    Usually used to test whether the bot is responsive or not.
    """
    msg = await ctx.reply("Beep")
    msg_tstamp = msg.timestamp
    emsg = await ctx.bot.edit_message(msg, "Boop")
    emsg_tstamp = emsg.edited_timestamp
    latency = ((emsg_tstamp - msg_tstamp).microseconds) // 1000
    await ctx.bot.edit_message(msg, "Ping: {}ms".format(str(latency)))


@cmds.cmd("invite",
          category="General",
          short_help="Sends the bot's invite link")
async def cmd_invite(ctx):
    """
    Usage: {prefix}invite

    Sends the link to invite the bot to your server.
    """
    await ctx.reply("Here's my invite link! \n<{}>".format(ctx.bot.objects["invite link"]))


@cmds.cmd("echo",
          category="General",
          short_help="Sends what you tell me to!")
async def cmd_echo(ctx):
    """
    Usage: {prefix}echo <text>

    Replies to the message with <text>.
    """
    await ctx.reply(ctx.arg_str if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("secho",
          category="General",
          short_help="Like echo but deletes.")
async def cmd_secho(ctx):
    """
    Usage: {prefix}secho <text>

    Replies to the message with <text> and deletes your message.
    """
    try:
        await ctx.bot.delete_message(ctx.msg)
    except Exception:
        pass
    await ctx.reply(ctx.arg_str if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("support",
          category="General",
          short_help="Sends the link to the bot guild")
async def cmd_support(ctx):
    """
    Usage: {prefix}support

    Sends the invite link to the Paradøx support guild.
    """
    await ctx.reply("Join my server here!\n\n<{}>".format(ctx.bot.objects["support guild"]))


@cmds.cmd("userinfo",
          category="User info",
          short_help="Shows the user's information")
@cmds.require("in_server")
@cmds.execute("user_lookup", in_server=True)
async def cmd_userinfo(ctx):
    """
    Usage: {prefix}userinfo (mention)

    Sends information on the mentioned user, or yourself if no one is provided.
    """
    if ctx.arg_str == "":
        user = ctx.author
    else:
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return

    bot_emoji = ctx.bot.objects["emoji_bot"]
    statusdict = {"offline": "Offline/Invisible",
                  "dnd": "Do Not Disturb",
                  "online": "Online",
                  "idle": "Idle/Away"}

    embed = discord.Embed(type="rich", color=(user.colour if user.colour.value else discord.Colour.light_grey()))
    embed.set_author(name="{user.name} ({user.id})".format(user=user), icon_url=user.avatar_url, url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name="Full name", value=("{} ".format(bot_emoji) if user.bot else "")+str(user), inline=False)

    game = "Playing {}".format(user.game if user.game else "nothing")
    embed.add_field(name="Status", value="{}, {}".format(statusdict[str(user.status)], game), inline=False)

    embed.add_field(name="Nickname", value=str(user.display_name), inline=False)

    shared = len(list(filter(lambda m: m.id == user.id, ctx.bot.get_all_members())))
    embed.add_field(name="Shared servers", value=str(shared), inline=False)

    joined_ago = ctx.strfdelta(datetime.utcnow()-user.joined_at)
    joined = user.joined_at.strftime("%-I:%M %p, %d/%m/%Y")
    created_ago = ctx.strfdelta(datetime.utcnow()-user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    embed.add_field(name="Joined at", value="{} ({} ago)".format(joined, joined_ago), inline=False)
    embed.add_field(name="Created at", value="{} ({} ago)".format(created, created_ago), inline=False)

    roles = [r.name for r in user.roles if r.name != "@everyone"]
    embed.add_field(name="Roles", value=('`' + '`, `'.join(roles) + '`'), inline=False)
    await ctx.reply(embed=embed)

    @cmds.cmd("discrim",
              category="General",
              short_help="Searches for users with a given discrim")
                 # "Usage: discrim [discriminator]\n\nSearches all guilds the bot is in for a user with the given discriminator.")
    async def prim_cmd_discrim(ctx):
         p = ctx.bot.get_all_members()
         found_members = set(filter(lambda m: m.discriminator.endswith(ctx.args), p))
         if len(found_members) == 0:
             await ctx.reply("No users with this discrim found!")
             return
         user_info = [ (str(m), "({})".format(m.id)) for m in found_members]
         max_len = len(max(list(zip(*user_info))[0],key=len))
         user_strs = [ "{0[0]:^{max_len}} {0[1]:^25}".format(user, max_len = max_len) for user in user_info]
         await ctx.reply("```asciidoc\n= Users found =\n{}\n```".format('\n'.join(user_strs)))
