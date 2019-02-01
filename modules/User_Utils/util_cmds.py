from paraCH import paraCH
import discord
from datetime import datetime
from pytz import timezone
import pytz
import iso8601
import traceback
import aiohttp
from PIL import Image, ImageChops
from io import BytesIO
import itertools


cmds = paraCH()
# Provides time, rotate


@cmds.cmd("rotate",
          category="Utility",
          short_help="Rotates the last sent image.")
async def cmd_rotate(ctx):
    """
    Usage:
        {prefix}rotate [amount]
    Description:
        Rotates the attached image or the last sent image (within the last 10 messages) by <amount>.
        If <amount> is not specified, rotates backwards by 90.
    """
    amount = -1 * int(ctx.arg_str) if ctx.arg_str and (ctx.arg_str.isdigit() or (len(ctx.arg_str) > 1 and ctx.arg_str[0] == '-' and ctx.arg_str[1:].isdigit())) else 90
    try:
        message_list = ctx.bot.logs_from(ctx.ch, limit=10)
    except discord.Forbidden:
        await ctx.reply("I need permisions to get message logs to use this command")
        return
    file_dict = None
    async for message in message_list:
        if message.attachments and "height" in message.attachments[0]:
            file_dict = message.attachments[0]
            break
    if not file_dict:
        await ctx.reply("Couldn't find an attached image in the last 10 messages")
        return
    image_url = file_dict["url"]

    async with aiohttp.get(image_url) as r:
        response = await r.read()

    with Image.open(BytesIO(response)) as im:
        exif = im.info.get('exif', None)
        rotated = im.rotate(amount, expand=1)
        bbox = rotated.getbbox()
        rotated = rotated.crop(bbox)
        with BytesIO() as output:
            rotated.convert("RGB").save(output, exif=exif, format="JPEG", quality=85, optimize=True)
            output.seek(0)
            out_msg = await ctx.bot.send_file(ctx.ch, fp=output, filename="{}.png".format(file_dict["id"]))
            if out_msg:
                await ctx.offer_delete(out_msg)


async def timezone_lookup(ctx):
    search_str = ctx.flags["set"].strip("<>")
    if search_str in pytz.all_timezones:
        return search_str
    timestr = '%-I:%M %p'
    tzlist = [(tz, iso8601.parse_date(datetime.now().isoformat()).astimezone(timezone(tz)).strftime(timestr)) for tz in pytz.all_timezones]
    if search_str:
        tzlist = [tzpair for tzpair in tzlist if (search_str.lower() in tzpair[0].lower()) or (search_str.lower() in tzpair[1].lower())]
    if not tzlist:
        await ctx.reply("No timezones were found matching these criteria!")
        return
    if len(tzlist) == 1:
        return tzlist[0][0]

    tz_blocks = [tzlist[i:i + 20] for i in range(0, len(tzlist), 20)]
    max_block_lens = [len(max(list(zip(*tz_block))[0], key=len)) for tz_block in tz_blocks]
    block_strs = [["{0[0]:^{max_len}} {0[1]:^10}".format(tzpair, max_len=max_block_lens[i]) for tzpair in tzblock] for i, tzblock in enumerate(tz_blocks)]
    blocks = list(itertools.chain(*block_strs))
    tz_num = await ctx.selector("Multiple matching timezones found, please select one!", blocks)
    return tzlist[tz_num][0] if tz_num is not None else None


@cmds.cmd("time",
          category="Utility",
          short_help="Shows the current time for a user",
          aliases=["ti"])
@cmds.execute("user_lookup", in_server=True)
@cmds.execute("flags", flags=["set=="])
async def cmd_time(ctx):
    """
    Usage:
        {prefix}time [mention | id | partial name] [--set <timezone>]
    Description:
        Gives the time for the mentioned user or yourself.
        Requires the user to have set the usersetting "timezone".
    Flags:2
        set:: Sets your timezone to the one given, or displays the options if multiple are found.
    Examples:
        {prefix}time {msg.author.name}
        {prefix}time --set Australia/Melbourne
        {prefix}time --set 10:52
    """
    if ctx.flags["set"]:
        TZ = await timezone_lookup(ctx)
        if not TZ:
            return
        await ctx.data.users.set(ctx.authid, "tz", TZ)
        await ctx.reply("Your timezone has been set to `{}`".format(TZ))
        return

    if ctx.arg_str == "":
        user = ctx.author
    else:
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return
    user = user.id
    tz = await ctx.data.users.get(user, "tz")
    if not tz:
        general_prefix = (await ctx.bot.get_prefixes(ctx))[0]
        if user == ctx.authid:
            await ctx.reply("You haven't set your timezone! Set it using `{0}time --set <timezone>`!`".format(general_prefix))
        else:
            await ctx.reply("This user hasn't set their timezone. Ask them to set it using `{0}time --set <timezone>`!".format(general_prefix))
        return
    try:
        TZ = timezone(tz)
    except Exception:
        await ctx.reply("An invalid timezone was provided in the database. Aborting... \n **Error Code:** `ERR_OBSTRUCTED_DB`")
        trace = traceback.format_exc()
        await ctx.log(trace)
        return
    timestr = 'The current time for **{}** is **%-I:%M %p (%Z(%z))** on **%a, %d/%m/%Y**'\
        .format(ctx.server.get_member(user).display_name if ctx.server else ctx.author.name)
    timestr = iso8601.parse_date(datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
    await ctx.reply(timestr)


def load_into(bot):
    bot.data.users.ensure_exists("tz")
