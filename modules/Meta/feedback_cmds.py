from datetime import datetime

import discord
from paraCH import paraCH

cmds = paraCH()

# Provides feedback, cheatreport

# TODO: Interactive bug reporting

# TODO: cooldown on feedback


@cmds.cmd("feedback", category="Meta", short_help="Send feedback to my creators")
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
    out_msg = await ctx.reply(embed=embed)
    response = await ctx.ask("Are you sure you wish to send the above message to the developers?")
    if not response:
        await ctx.reply("User cancelled, aborting.")
        return
    await ctx.bot.send_message(ctx.bot.objects["feedback_channel"], embed=embed)
    if ctx.bot.objects["brief"]:
        await ctx.bot.delete_message(out_msg)
    await ctx.reply("Thank you! Your feedback has been sent.")


@cmds.cmd("abusereport", category="Meta", short_help="Reports a user for abusing a bot command.", flags=["e=="])
async def cmd_cr(ctx):
    """
    Usage:
        {prefix}abusereport <user> <cheat> [-e <evidence>]
    Description:
        Reports a user for abusing a command, e.g. cheating on a social system.
        Please provide the user you wish to report, what they abused, and your evidence.
        If reporting the user in DM or another server, please use their user id.
        Note that abuse or overuse of this command will lead to your account being blacklisted.
    """
    if len(ctx.params) < 2:
        await ctx.reply("Insufficient arguments, see help for usage")
        return
    user = ctx.params[0]
    cheat = ' '.join(ctx.params[1:])
    evidence = ctx.flags['e'] if ctx.flags[
        'e'] else "None. (Note that cheat reports without evidence are not recommended)"
    if not user.isdigit():
        if not ctx.server:
            await ctx.reply("Please provide a valid user ID when reporting from private message")
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
    out_msg = await ctx.reply(embed=embed)
    response = await ctx.ask("Are you sure you wish to send the above cheat report?")
    if not response:
        await ctx.reply("User cancelled, aborting.")
        return
    await ctx.bot.send_message(ctx.bot.objects["cheat_report_channel"], embed=embed)
    if ctx.bot.objects["brief"]:
        await ctx.bot.delete_message(out_msg)
    await ctx.reply("Thank you. Your cheat report has been sent.")
