import discord
from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("about",
          category="General",
          short_help="Provides information about the bot. (WIP)")
async def cmd_about(ctx):
    """
    Usage: {prefix}about

    Sends a message containing information about the bot.
    """
    devs = ["298706728856453121", "299175087389802496", "225773687037493258"]
    devnames = ', '.join([str(discord.utils.get(ctx.bot.get_all_members(), id=str(devs))) for devs in devs])
    embed = discord.Embed(title="About Paradøx", color=discord.Colour.red()) \
        .add_field(name="Info", value="Paradøx is a Discord.py bot coded by {}.".format(devnames), inline=True) \
        .add_field(name="Links", value="[Support Server](https://discord.gg/ECbUu8u)", inline=False)
    await ctx.reply(embed=embed)


@cmds.cmd("cheatreport",
          category="General",
          short_help="Reports a user for cheating with rep/level/xp. (WIP)")
async def cmd_cr(ctx):
    """
    Usage: {prefix}report [user] [cheat] [evidence]

    Reports a user for cheating on a social system.
    Please provide the user you wish to report, the form of cheat, and your evidence.
    (TBD)
    """
    embed = discord.Embed(title="Cheat Report", color=discord.Colour.red()) \
        .set_author(name="{} ({})".format(ctx.message.author, ctx.message.author.id),
                    icon_url=ctx.message.author.avatar_url) \
        .add_field(name="User", value=".", inline=True) \
        .add_field(name="Cheat", value="Alt Repping|Chatbot|Spamming", inline=True) \
        .add_field(name="Evidence", value="(Evidence from args)", inline=False) \
        .set_footer(text="Guild name|Timestamp")
    await ctx.reply(embed=embed)


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


@cmds.cmd("support",
          category="General",
          short_help="Sends the link to the bot guild")
async def cmd_support(ctx):
    """
    Usage: {prefix}support

    Sends the invite link to the Paradøx support guild.
    """
    await ctx.reply("Join my server here!\n\n<{}>".format(ctx.bot.objects["support guild"]))
