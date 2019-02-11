import discord
from paraCH import paraCH

cmds = paraCH()

# Provides bin2ascii, lenny


@cmds.cmd("bin2ascii", category="Fun", short_help="Converts binary to ascii", aliases=["bin2a", "binarytoascii"])
async def cmd_bin2ascii(ctx):
    """
    Usage:
        {prefix}bin2ascii <binary string>
    Description:
        Converts the provided binary string into ascii, then sends the output.
    Examples:
        {prefix}bin2ascii 01001000 01101001 00100001
    """
    # Would be cool if example could use username
    bitstr = ctx.arg_str.replace(' ', '')
    if (not bitstr.isdigit()) or (len(bitstr) % 8 != 0):
        await ctx.reply("Not a valid binary string!")
        return
    bytelist = map(''.join, zip(*[iter(bitstr)] * 8))
    asciilist = [chr(sum([int(b) << 7 - n for (n, b) in enumerate(byte)])) for byte in bytelist]
    await ctx.reply("Output: `{}`".format(''.join(asciilist)))


@cmds.cmd("lenny", category="Fun", short_help="( ͡° ͜ʖ ͡°)")
async def cmd_lenny(ctx):
    """
    Usage:
        {prefix}lenny
    Description:
        Sends lenny ( ͡° ͜ʖ ͡°).
    """
    try:
        await ctx.bot.delete_message(ctx.msg)
    except discord.Forbidden:
        pass
    await ctx.reply("( ͡° ͜ʖ ͡°)")


@cmds.cmd("discrim", category="Fun", short_help="Searches for users with a given discrim")
async def prim_cmd_discrim(ctx):
    """
    Usage:
        {prefix}discrim [discriminator]
    Description:
        Searches all guilds the bot is in for users matching the given discriminator.
    """
    p = ctx.bot.get_all_members()
    args = ctx.arg_str
    if (len(args) > 4) or not args.isdigit():
        await ctx.reply("You must give me at most four digits to find!")
        return
    discrim = "0" * (4 - len(args)) + args
    found_members = set(filter(lambda m: m.discriminator == discrim, p))
    if len(found_members) == 0:
        await ctx.reply("No users with this discrim found!")
        return
    user_info = [(str(m), "({})".format(m.id)) for m in found_members]
    max_len = len(max(list(zip(*user_info))[0], key=len))
    user_strs = ["{0[0]:^{max_len}} {0[1]:^25}".format(user, max_len=max_len) for user in user_info]
    await ctx.pager(
        ctx.paginate_list(
            user_strs, title="{} user{} found".format(len(user_strs), "s" if len(user_strs) > 1 else "", discrim)))
