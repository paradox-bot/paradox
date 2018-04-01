import discord
from paraCH import paraCH
from datetime import datetime
import sys
import platform
import psutil


cmds = paraCH()


@cmds.cmd("about",
          category="General",
          short_help="Provides information about the bot.")
async def cmd_about(ctx):
    """
    Usage: {prefix}about

    Sends a message containing information about the bot.
    """
    devs = ["298706728856453121", "299175087389802496", "225773687037493258", "300992784020668416"]  #TODO: Don't hard code these here!!
    devnames = ', '.join([str(discord.utils.get(ctx.bot.get_all_members(), id=str(devs))) for devs in devs])
    pform = platform.platform()
    py_vers = sys.version
    mem = psutil.virtual_memory()
    mem_str = "{0:.2f}GB used out of {1:.2f}GB ({mem.percent}\%)".format(mem.used/(1024 ** 3), mem.total/(1024 ** 3), mem=mem)
    cpu_usage_str = "{}\%".format(psutil.cpu_percent())
    info = "I am a multi-purpose guild automation bot from Team Paradøx, coded in Discord.py!\
        \nI am under active development and constantly evolving with new commands and features."
    links = "[Support Server]({sprt}), [Invite Me]({invite})".format(sprt=ctx.bot.objects["support guild"],
                                                                     invite=ctx.bot.objects["invite_link"])

    emb_fields = [("Info", info, 1),
                  ("Developed by", devnames, 0),
                  ("Python version", py_vers, 0),
                  ("Platform", pform, 0),
                  ("Memory", mem_str, 0),
                  ("CPU usage", cpu_usage_str, 0),
                  ("Links", links, 0)]
    embed = discord.Embed(title="About Me", color=discord.Colour.red())
    await ctx.emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)
    # Uptime as well, of system and bot
    # Commands used? Or that goes in stats
# TODO: Interactive bug reporting

# TODO: cooldown on feedback


@cmds.cmd("feedback",
          category="General",
          short_help="Send feedback to my creators")
async def cmd_feedback(ctx):
    """
    Usage {prefix}feedback [msg]

    Sends a message back to the developers of the bot.
    This can be used for suggestions, bug reporting, or general feedback.
    Note that abuse or overuse of this command will lead to blacklisting.
    """
    response = ctx.arg_str
    if response == "":
        response = await ctx.input("What message would you like to send? (`c` to cancel)", timeout=240)
        if not response:
            await ctx.reply("Question timed out, aborting!")
            return
        elif response.lower() == "c":
            await ctx.reply("User cancelled, aborting!")
            return
    embed = discord.Embed(title="Feedback", color=discord.Colour.green()) \
        .set_author(name="{} ({})".format(ctx.author, ctx.authid),
                    icon_url=ctx.author.avatar_url) \
        .add_field(name="Message", value=response, inline=False) \
        .set_footer(text=datetime.utcnow().strftime("Sent from {} at %-I:%M %p, %d/%m/%Y".format(ctx.server.name if ctx.server else "private message")))
    await ctx.reply(embed=embed)
    response = await ctx.ask("Are you sure you wish to send the above message to the developers?")
    if not response:
        await ctx.reply("User cancelled, aborting.")
        return
    await ctx.bot.send_message(ctx.bot.objects["feedback_channel"], embed=embed)
    await ctx.reply("Thank you! Your feedback has been sent.")


@cmds.cmd("cheatreport",
          category="General",
          short_help="Reports a user for cheating with rep/level/xp.")
@cmds.execute("flags", flags=["e=="])
async def cmd_cr(ctx):
    """
    Usage: {prefix}cheatreport <user> <cheat> [-e <evidence>]

    Reports a user for cheating on a social system.
    Please provide the user you wish to report, the way they cheated, and your evidence.
    If reporting the user in DM or another server, please use their user id.
    Note that abuse or overuse of this command will lead to your account being blacklisted.
    """
    if len(ctx.params) < 2:
        await ctx.reply("Insufficient arguments, see help for usage")
        return
    user = ctx.params[0]
    cheat = ' '.join(ctx.params[1:])
    evidence = ctx.flags['e'] if ctx.flags['e'] else "None. (Note that cheat reports without evidence are not recommended)"
    if not user.isdigit():
        if not ctx.server:
            await ctx.reply("Please provide a valid userid when reporting from private message")
            return
        user = await ctx.find_user(ctx.params[0], in_server=True, interactive=True)
        if ctx.cmd_err[0]:
            return
    else:
        user = discord.utils.get(ctx.bot.get_all_members(), id=user)
    if not user:
        await ctx.reply("Couldn't find this user!")
        return
    embed = discord.Embed(title="Cheat Report", color=discord.Colour.red()) \
        .set_author(name="{} ({})".format(ctx.author, ctx.authid),
                    icon_url=ctx.author.avatar_url) \
        .add_field(name="Reported User", value="`{0}` (`{0.id}`)".format(user), inline=True) \
        .add_field(name="Cheat", value=cheat, inline=True) \
        .add_field(name="Evidence", value=evidence, inline=False) \
        .set_footer(text=datetime.utcnow().strftime("Reported in {} at %-I:%M %p, %d/%m/%Y".format(ctx.server.name if ctx.server else "private message")))
    await ctx.reply(embed=embed)
    response = await ctx.ask("Are you sure you wish to send the above cheat report?")
    if not response:
        await ctx.reply("User cancelled, aborting.")
        return
    await ctx.bot.send_message(ctx.bot.objects["cheat_report_channel"], embed=embed)
    await ctx.reply("Thank you. Your cheat report has been sent.")


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
    await ctx.reply("Here's my invite link! \n<{}>".format(ctx.bot.objects["invite_link"]))


@cmds.cmd("support",
          category="General",
          short_help="Sends the link to the bot guild")
async def cmd_support(ctx):
    """
    Usage: {prefix}support

    Sends the invite link to the Paradøx support guild.
    """
    await ctx.reply("Join my server here!\n\n<{}>".format(ctx.bot.objects["support guild"]))


@cmds.cmd("serverinfo",
          category="General",
          short_help="Shows server info.")
async def cmd_serverinfo(ctx):
    regions = {
        "brazil": "Brazil",
        "eu-central": "Central Europe",
        "hongkong": "Hong Kong",
        "japan": "Japan",
        "russia": "Russia",
        "singapore": "Singapore",
        "sydney": "Sydney",
        "us-central": "Central United States",
        "us-east": "Eastern United States",
        "us-south": "Southern United States",
        "us-west": "Western United States",
        "eu-west": "Western Europe",
        "vip-amsterdam": "Amsterdam (VIP)",
        "vip-us-east": "Eastern United States (VIP)",
    }

    ver = {
        "none": "None",
        "low": "1 - Must have a verified email",
        "medium": "2 - Must also be registered for more than 5 minutes",
        "high": "3 - Must also be member of the server for more than 10 minutes",
        4: "4 - Must have a verified phone number"
    }

    mfa = {
        0: "Disabled",
        1: "Enabled"
    }

    text = len([c for c in ctx.server.channels if c.type == discord.ChannelType.text])
    total = len(ctx.server.channels)
    voice = total - text

    online = 0
    idle = 0
    offline = 0
    dnd = 0
    total = len(ctx.server.members)
    for m in ctx.server.members:
        if m.status == discord.Status.online:
            online = online + 1
        elif m.status == discord.Status.idle:
            idle = idle + 1
        elif m.status == discord.Status.offline:
            offline = offline + 1
        elif m.status == discord.Status.dnd:
            dnd = dnd + 1

    Online = ctx.bot.objects["emoji_online"]
    Idle = ctx.bot.objects["emoji_idle"]
    Dnd = ctx.bot.objects["emoji_dnd"]
    Offline = ctx.bot.objects["emoji_offline"]

    embed = discord.Embed(color=discord.Colour.teal()) \
        .set_author(name="{}".format(ctx.server)) \
        .add_field(name="Owner", value="{} ({})".format(ctx.server.owner, ctx.server.owner.id), inline=False) \
        .add_field(name="Members", value="{} humans, {} bots | {} total".format(str(len([m for m in ctx.server.members if not m.bot])),
                                                                                str(len([m for m in ctx.server.members if m.bot])),
                                                                                ctx.server.member_count), inline=False) \
        .add_field(name="ID", value="{}".format(ctx.server.id), inline=False) \
        .add_field(name="Region", value="{}".format(regions[str(ctx.server.region)]), inline=False) \
        .add_field(name="Created at", value="{}".format(ctx.server.created_at), inline=False) \
        .add_field(name="Channels", value="{} text, {} voice | {} total".format(text, voice, total), inline=False) \
        .add_field(name="Roles", value="{}".format(len(ctx.server.roles)), inline=False) \
        .add_field(name="Large server", value="{}".format(ctx.server.large), inline=False) \
        .add_field(name="Verification", value="{}".format(ver[str(ctx.server.verification_level)]), inline=False) \
        .add_field(name="2FA", value="{}".format(mfa[ctx.server.mfa_level]), inline=False) \
        .add_field(name="Member Status", value="{} - **{}**\n{} - **{}**\n{} - **{}**\n{} - **{}**".format(Online, online, Idle, idle, Dnd, dnd, Offline, offline), inline=False)
    await ctx.reply(embed=embed)
