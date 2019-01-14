from paraCH import paraCH
import discord
import asyncio

cmds = paraCH()


@cmds.cmd("cleanch",
          category="Server Admin",
          short_help="Enable or disable automatic deletion on a channel.",
          aliases=["chclean"])
@cmds.require("has_manage_server")
async def cmd_cleanch(ctx):
    """
    Usage:
        {prefix}cleanch
    Description:
        Enables or disables automatic deletion of messages in a channel.
    """
    if ctx.server.id not in ctx.bot.objects["cleaned_channels"]:
        ctx.bot.objects["cleaned_channels"][ctx.server.id] = []
    cleaned = ctx.bot.objects["cleaned_channels"][ctx.server.id]
    if ctx.ch.id in cleaned:
        cleaned.remove(ctx.ch.id)
        await ctx.reply("I have stopped auto-deleting messages in this channel")
    else:
        cleaned.append(ctx.ch.id)
        await ctx.reply("I will now auto-delete messages in this channel.")
    await ctx.bot.data.servers.set(ctx.server.id, "clean_channels", cleaned)


async def channel_cleaner(ctx):
    if not ctx.server:
        return
    if not (ctx.server.id in ctx.bot.objects["cleaned_channels"] and ctx.ch.id in ctx.bot.objects["cleaned_channels"][ctx.server.id]):
        return
    await asyncio.sleep(30)
    if ctx.msg.pinned:
        return
    try:
        await ctx.bot.delete_message(ctx.msg)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass


async def register_channel_cleaners(bot):
    cleaned_channels = {}
    for server in bot.servers:
        channels = await bot.data.servers.get(server.id, "clean_channels")
        if channels:
            cleaned_channels[server.id] = channels
    bot.objects["cleaned_channels"] = cleaned_channels
    await bot.log("Loaded {} servers with channels to clean.".format(len(cleaned_channels)))


def load_into(bot):
    bot.data.servers.ensure_exists("clean_channels", shared=False)

    bot.add_after_event("ready", register_channel_cleaners)
    bot.after_ctx_message(channel_cleaner)
