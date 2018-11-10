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
    Usage:
        {prefix}about
    Description:
        Sends a message containing information about the bot.
    """
    current_devs = ["299175087389802496", "408905098312548362", "300992784020668416"]
    devnames = ', '.join([str(discord.utils.get(ctx.bot.get_all_members(), id=str(devs))) for devs in current_devs])
    pform = platform.platform()
    py_vers = sys.version
    mem = psutil.virtual_memory()
    mem_str = "{0:.2f}GB used out of {1:.2f}GB ({mem.percent}%)".format(mem.used / (1024 ** 3), mem.total / (1024 ** 3), mem=mem)
    cpu_usage_str = "{}%".format(psutil.cpu_percent())
    info = "I am a high quality LaTeX rendering bot, coded in Discord.py!\
        \nSee `{}help` for information about how to use me.".format(ctx.used_prefix)
    links = "[Support Server]({sprt}), [Invite Me]({invite})".format(sprt=ctx.bot.objects["support guild"],
                                                                     invite=ctx.bot.objects["invite_link"])
    api_vers = "{} ({})".format(discord.__version__, discord.version_info[3])

    emb_fields = [("Developed by", "{}.".format(devnames), 0),
                  ("Python version", py_vers, 0),
                  ("Discord API version", api_vers, 0),
                  ("Platform", pform, 0),
                  ("Memory", mem_str, 0),
                  ("CPU usage", cpu_usage_str, 0),
                  ("Links", links, 0)]
    embed = discord.Embed(title="About Me", color=discord.Colour.red(), description=info)
    await ctx.emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)


@cmds.cmd("feedback",
          category="General",
          short_help="Send feedback to my creators")
async def cmd_feedback(ctx):
    """
    Usage:
        {prefix}feedback [msg]
    Description:
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


@cmds.cmd("ping",
          category="General",
          short_help="Checks the bot's latency",
          aliases=["pong"])
async def cmd_ping(ctx):
    """
    Usage:
        {prefix}ping
    Description:
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
          short_help="Sends the bot's invite link",
          aliases=["inv"])
async def cmd_invite(ctx):
    """
    Usage:
        {prefix}invite
    Description:
        Sends the link to invite the bot to your server.
    """
    await ctx.reply("Visit <{}> to invite me!".format(ctx.bot.objects["invite_link"]))


@cmds.cmd("support",
          category="General",
          short_help="Sends the link to the bot guild")
async def cmd_support(ctx):
    """
    Usage:
        {prefix}support
    Description:
        Sends the invite link to the Paradøx support guild.
    """
    await ctx.reply("Join my server here!\n\n<{}>".format(ctx.bot.objects["support guild"]))
