from commands.mod_cmds import request_reason as rrequest
from datetime import datetime

import discord
from paraCH import paraCH

cmds = paraCH()


@cmds.cmd(
    "prune",
    category="Moderation",
    short_help="Prunes messages",
    aliases=["purge"])
@cmds.execute(
    "flags",
    flags=[
        "r==", "bot", "bots", "user", "embed", "file", "me", "from==",
        "after==", "force"
    ])
@cmds.require("in_server")
@cmds.require("in_server_has_mod")
async def cmd_prune(ctx):
    """
    Usage:
        {prefix} prune [number] [--bot] [--user] [--embed] [--file] [--me] [-r <reason>] [--from <user>]
    Description:
        Deletes your command message and the given number of messages before that.
        If the number is not given, deletes 100 messages.
        The flags can restrict what types of messages are deleted.
        If there are multiples flags, only messages matching all the conditions will be deleted.
        You may only delete messages from the last thousand messages.
    Flags:3
        --bot:: Only delete messages from bots.
        --user::  Only delete messages from non-bots.
        --embed::  Only delete messages with embeds.
        --file:: Only delete messages with files (e.g. images).
        --me:: Only delete my messages.
        --from:: Only delete messages from this user (interactive lookup).
        --force:: Force a prune without asking for confirmation.
        --after:: Deletes all messages after (not including) the given message id
        -r::  Reason for the message purge (goes in the modlog).
    """
    # TODO: --after
    # TODO: --role? Maybe?
    # TODO: find_user won't work for users not in the server. Construct a collection based on message list.
    if not ctx.arg_str:
        number = 1000 if ctx.flags["after"] else 100
    elif not ctx.arg_str.isdigit():
        await ctx.reply(
            "Please give me a valid number of messages to delete. See the help for this command for usage."
        )
        return
    else:
        number = int(ctx.arg_str)

    if ctx.flags["from"]:
        user = await ctx.find_user(
            ctx.flags["from"], in_server=True, interactive=True)
        if user is None:
            if ctx.cmd_err[0] != -1:
                await ctx.reply("Couldn't find this user, aborting.".format(
                    ctx.flags["from"]))
            else:
                await ctx.reply("User selection timed out, aborting.")
                ctx.cmd_err = (0, "")
            return

    if not ctx.flags["r"]:
        reason = "None, forced prune" if ctx.flags["force"] else await rrequest(
            ctx, action="purge")
        if reason is None:
            return
    else:
        reason = ctx.flags["r"]

    try:
        await ctx.bot.delete_message(ctx.msg)
    except discord.NotFound:
        pass
    except discord.Forbidden:
        await ctx.reply(
            "I do not have permissions to delete messages here. If this is in error, please give me the MANAGE_MESSAGES permission."
        )
        return

    count_dict = {"bots": {}, "users": {}}
    message_list = []
    i = 0

    after_msg_id = ctx.flags["after"] if ctx.flags["after"] else None
    msg_found = False

    async for message in ctx.bot.logs_from(ctx.ch, limit=1000):
        if i == number:
            break
        if message.id == after_msg_id:
            msg_found = True
            break

        to_delete = True
        to_delete = to_delete and (not (ctx.flags["bot"] or ctx.flags["bots"])
                                   or message.author.bot)
        to_delete = to_delete and (not ctx.flags["user"]
                                   or not message.author.bot)
        to_delete = to_delete and (not ctx.flags["embed"] or message.embeds)
        to_delete = to_delete and (not ctx.flags["file"]
                                   or message.attachments)
        to_delete = to_delete and (not ctx.flags["from"]
                                   or message.author == user)
        to_delete = to_delete and (not ctx.flags["me"]
                                   or message.author == ctx.me)
        if to_delete:
            i += 1
            message_list.append(message)
            listing = count_dict["bots" if message.author.bot else "users"]
            if message.author.id not in listing:
                listing[message.author.id] = {
                    "count": 0,
                    "name": "{}".format(message.author)
                }
            listing[message.author.id]["count"] += 1

    if ctx.flags["after"] and not msg_found:
        await ctx.reply(
            "The given message wasn't found in the last {} messages".format(
                number))
        return

    bot_lines = "\n".join([
        "\t**{name}** ({key}): ***{count}*** messages".format(
            **count_dict["bots"][key], key=key) for key in count_dict["bots"]
    ])
    user_lines = "\n".join([
        "\t**{name}** ({key}): ***{count}*** messages".format(
            **count_dict["users"][key], key=key) for key in count_dict["users"]
    ])
    bot_counts = "__**Bots**__\n{}".format(bot_lines) if bot_lines else ""
    user_counts = "__**Users**__\n{}".format(user_lines) if user_lines else ""
    if len(message_list) == 0:
        await ctx.reply("No messages matching these criteria were found!")
        return
    counts = "{}\n{}".format(bot_counts, user_counts)
    abort = False
    if not ctx.flags["force"]:
        out_msg = await ctx.reply("Purging **{}** messages. Message Breakdown:\
                                  \n{}\n--------------------\nPlease type `confirm` to delete the above messages or `abort` to abort now."
                                  .format(len(message_list), counts))
        reply_msg = await ctx.listen_for(
            chars=["abort", "confirm"], timeout=60)
        if reply_msg is None:
            await ctx.reply("Confirmation request timed out, aborting purge.")
            abort = True
        else:
            try:
                await ctx.bot.delete_message(reply_msg)
            except Exception:
                pass
            if reply_msg.content.lower() == "abort":
                await ctx.reply("User requested abort, aborting purge.")
                abort = True

    if not abort:
        if not ctx.flags["force"]:
            await ctx.bot.delete_message(out_msg)
        try:
            if len(message_list) == 1:
                await ctx.bot.delete_message(message_list[0])
            else:
                msgids = [msg.id for msg in message_list]
                await ctx.bot.purge_from(
                    ctx.ch, limit=1000, check=lambda msg: msg.id in msgids)
        except discord.Forbidden:
            await ctx.reply(
                "I have insufficient permissions to delete these messages.")
            abort = True
        except discord.HTTPException:
            try:
                for msg in message_list:
                    await ctx.bot.delete_message(msg)
            except discord.Forbidden:
                await ctx.reply(
                    "I have insufficient permissions to delete these messages."
                )
                abort = True
    if abort:
        return


#    final_message = "Purged **{}** messages. Message breakdown:\n{}".format(len(message_list), counts)
#    await ctx.reply(final_message)

# modlog posting should be integrated with mod commands
# have a modlog method which makes an embed post labelled with time and moderator name.
    modlog = await ctx.server_conf.modlog_ch.get(ctx)
    if not modlog:
        return
    modlog = ctx.server.get_channel(modlog)
    if not modlog:
        return

    embed = discord.Embed(
        title="Messages purged",
        color=discord.Colour.red(),
        description="**{}** messages purged in {}.".format(
            len(message_list), ctx.ch.mention))
    embed.add_field(name="Message Breakdown", value=counts, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(
        icon_url=ctx.author.avatar_url,
        text=datetime.utcnow().strftime(
            "Acting Moderator: {} at %-I:%M %p, %d/%m/%Y".format(ctx.author)))
    try:
        await ctx.bot.send_message(modlog, embed=embed)
    except discord.Forbidden:
        await ctx.reply(
            "Tried to post to the modlog but had insufficient permissions")
    except Exception:
        pass
