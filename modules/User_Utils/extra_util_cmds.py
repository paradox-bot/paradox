from paraCH import paraCH
import discord
from datetime import datetime
from pytz import timezone
import pytz
import iso8601
import aiohttp
import string


cmds = paraCH()


@cmds.cmd("echo",
          category="Utility",
          short_help="Sends what you tell me to!")
async def cmd_echo(ctx):
    """
    Usage:
        {prefix}echo <text>
    Description:
        Replies to the message with <text>.
    """
    await ctx.reply(ctx.arg_str if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("jumpto",
          category="Utility",
          short_help="Generates a jump to link with a given message ID.")
@cmds.require("in_server")
async def cmd_jumpto(ctx):

    msgid = ctx.arg_str
    if msgid == "" or not msgid.isdigit():
        await ctx.reply("Please provide a valid message ID.")
        return
    message = None
    try:
        message = await ctx.bot.get_message(ctx.ch, msgid)
    except Exception:
        pass
    for channel in ctx.server.channels:
        if message:
            break
        if channel.type != discord.ChannelType.text:
            continue
        if channel == ctx.ch:
            continue
        try:
            message = await ctx.bot.get_message(channel, msgid)
        except Exception:
            pass
    if not message:
        await ctx.reply("Couldn't find the message!")
        return
    embed = discord.Embed(colour=discord.Colour.green(), title="Jump to for message ID {}".format(msgid), description="[Click to jump to message]({})".format(ctx.msg_jumpto(message)))
    await ctx.reply(embed=embed)


@cmds.cmd("quote",
          category="Utility",
          short_help="Quotes a message by ID")
@cmds.execute("flags", flags=["a"])
@cmds.require("in_server")
async def cmd_quote(ctx):
    """
    Usage:
        {prefix}quote <messageid> [-a]
    Description:
        Replies with the specified message in an embed.
        Note that the message must be from the same server.
    Flags:
        -a:  (anonymous) Removes author information from the quote.
    """
    msgid = ctx.arg_str
    if msgid == "" or not msgid.isdigit():
        await ctx.reply("Please provide a valid message ID.")
        return
    out_msg = await ctx.reply("Searching for message, please wait {}".format(ctx.aemoji_mention(ctx.bot.objects["emoji_loading"])))

    message = None
    try:
        message = await ctx.bot.get_message(ctx.ch, msgid)
    except Exception:
        pass
    message = await ctx.find_message(msgid, ignore=[ctx.ch])

    if not message:
        await ctx.bot.edit_message(out_msg, "Couldn't find the message!")
        return

    embed = discord.Embed(colour=discord.Colour.light_grey(),
                          description=message.content,
                          title="Click to jump to message",
                          url=ctx.msg_jumpto(message))

    if not ctx.flags["a"]:
        embed.set_author(name="{user.name}".format(user=message.author),
                         icon_url=message.author.avatar_url)
    embed.set_footer(text=message.timestamp.strftime("Sent at %-I:%M %p, %d/%m/%Y in #{}".format(message.channel.name)))
    if message.attachments:
        embed.set_image(url=message.attachments[0]["proxy_url"])
    await ctx.bot.edit_message(out_msg, " ", embed=embed)


@cmds.cmd("secho",
          category="Utility",
          short_help="Like echo but deletes.")
async def cmd_secho(ctx):
    """
    Usage:
        {prefix}secho <text>
    Description:
        Replies to the message with <text> and deletes your message.
    """
    try:
        await ctx.bot.delete_message(ctx.msg)
    except Exception:
        pass
    await ctx.reply("{}".format(ctx.arg_str) if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("invitebot",
          category="Utility",
          short_help="Generates a bot invite link for a bot",
          aliases=["ibot"])
@cmds.execute("user_lookup", in_server=True, greedy=True)
async def cmd_invitebot(ctx):
    """
    Usage:
        {prefix}invitebot <bot>
    Description:
        Replies with an invite link for the bot.
    """
    user = ctx.objs["found_user"]
    if ctx.arg_str.isdigit():
        userid = ctx.arg_str
    elif not user:
        await ctx.reply("I couldn't find any matching bots in this server")
        return
    elif not user.bot:
        await ctx.reply("Maybe you could try asking them nicely?")
        return
    if user:
        userid = user.id
    await ctx.reply("<https://discordapp.com/api/oauth2/authorize?client_id={}&permissions=0&scope=bot>".format(userid))


@cmds.cmd("piggybank",
          category="Utility",
          short_help="Keep track of money added towards a goal.",
          aliases=["bank"])
async def cmd_piggybank(ctx):
    """
    Usage:
        {prefix}piggybank [+|- <amount>] | [list [clear]] | [goal <amount>|none]
    Description:
        [+|- <amount>]: Adds or removes an amount to your piggybank.
        [list [clear]]: Sends you a DM with your previous transactions or clears your history.
        [goal <amount>|none]: Sets your goal!
        Or with no arguments, lists your current amount and progress to the goal.
    """
    bank_amount = await ctx.data.users.get(ctx.authid, "piggybank_amount")
    transactions = await ctx.data.users.get(ctx.authid, "piggybank_history")
    goal = await ctx.data.users.get(ctx.authid, "piggybank_goal")
    bank_amount = bank_amount if bank_amount else 0
    transactions = transactions if transactions else {}
    goal = goal if goal else 0
    if ctx.arg_str == "":
        msg = "You have ${:.2f} in your piggybank!".format(bank_amount)
        if goal:
            msg += "\nYou have achieved {:.1%} of your goal (${:.2f})".format(bank_amount / goal, goal)
        await ctx.reply(msg)
        return
    elif (ctx.params[0] in ["+", "-"]) and len(ctx.params) == 2:
        action = ctx.params[0]
        now = datetime.utcnow().strftime('%s')
        try:
            amount = float(ctx.params[1].strip("$#"))
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        transactions[now] = {}
        transactions[now]["amount"] = "{}${:.2f}".format(action, amount)
        bank_amount += amount if action == "+" else -amount
        await ctx.data.users.set(ctx.authid, "piggybank_amount", bank_amount)
        await ctx.data.users.set(ctx.authid, "piggybank_history", transactions)
        msg = "${:.2f} has been {} your piggybank. You now have ${:.2f}!".format(amount,
                                                                                 "added to" if action == "+" else "removed from",
                                                                                 bank_amount)
        if goal:
            if bank_amount >= goal:
                msg += "\nYou have achieved your goal!"
            else:
                msg += "\nYou have now achieved {:.1%} of your goal (${:.2f}).".format(bank_amount / goal, goal)
        await ctx.reply(msg)
    elif (ctx.params[0] == "goal") and len(ctx.params) == 2:
        if ctx.params[1].lower() in ["none", "remove", "clear"]:
            await ctx.data.users.set(ctx.authid, "piggybank_goal", amount)
            await ctx.reply("Your goal has been cleared")
            return
        try:
            amount = float(ctx.params[1].strip("$#"))
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        await ctx.data.users.set(ctx.authid, "piggybank_goal", amount)
        await ctx.reply("Your goal has been set to ${}. ".format(amount))
    elif (ctx.params[0] == "list"):
        if len(transactions) == 0:
            await ctx.reply("No transactions to show! Start adding money to your piggy bank with `{}piggybank + <amount>`".format(ctx.used_prefix))
            return
        if (len(ctx.params) == 2) and (ctx.params[1] == "clear"):
            await ctx.data.users.set(ctx.authid, "piggybank_history", {})
            await ctx.reply("Your transaction history has been cleared!")
            return

        msg = "```\n"
        for trans in sorted(transactions):
            trans_time = datetime.utcfromtimestamp(int(trans))
            tz = await ctx.data.users.get(ctx.authid, "tz")
            if tz:
                try:
                    TZ = timezone(tz)
                except Exception:
                    pass
            else:
                TZ = timezone("UTC")
            timestr = '%-I:%M %p, %d/%m/%Y (%Z)'
            timestr = TZ.localize(trans_time).strftime(timestr)
            msg += "{}\t {:^10}\n".format(timestr, str(transactions[trans]["amount"]))
        await ctx.reply(msg + "```", dm=True)
    else:
        await ctx.reply("Usage: {}piggybank [+|- <amount>] | [list] | [goal <amount>|none]".format(ctx.used_prefix))


@cmds.cmd("timezone",
          category="Utility",
          short_help="Searches the timezone list",
          aliases=["tz"])
async def cmd_timezone(ctx):
    """
    Usage:
        {prefix}timezone <partial>
    Description:
        Searches for <partial> amongst the available timezones and shows you the current time in each!
    """
    timestr = '%-I:%M %p'
    tzlist = [(tz, iso8601.parse_date(datetime.now().isoformat()).astimezone(timezone(tz)).strftime(timestr)) for tz in pytz.all_timezones]
    if ctx.arg_str:
        tzlist = [tzpair for tzpair in tzlist if (ctx.arg_str.lower() in tzpair[0].lower()) or (ctx.arg_str.lower() in tzpair[1].lower())]
    if not tzlist:
        await ctx.reply("No timezones were found matching these criteria!")
        return

    tz_blocks = [tzlist[i:i + 20] for i in range(0, len(tzlist), 20)]
    max_block_lens = [len(max(list(zip(*tz_block))[0], key=len)) for tz_block in tz_blocks]
    block_strs = [["{0[0]:^{max_len}} {0[1]:^10}".format(tzpair, max_len=max_block_lens[i]) for tzpair in tzblock] for i, tzblock in enumerate(tz_blocks)]
    tz_pages = ["```\n{}\n```".format("\n".join(block)) for block in block_strs]
    await ctx.pager(tz_pages)


@cmds.cmd(name="emoji",
          category="Utility",
          short_help="Displays info and enlarges a custom emoji",
          aliases=["e", "ee", "ree", "sree"])
@cmds.execute("flags", flags=["e", "a"])
async def cmd_emoji(ctx):
    """
    Usage:
        {prefix}emoji <emoji> [-e]
        {prefix}ee <emoji>
        {prefix}ree <emoji>
    Description:
        Displays some information about the provided custom emoji, and sends an enlarged version.
        If the emoji isn't found, instead searches for the emoji amongst all emojis I can see.
        If used as ee or given with -e flag, only shows the enlarged image.
        If used as ree, reacts with the emoji.
        Built in emoji support is coming soon!
    Flags:
        -e:  (enlarge) Only shows the enlarged emoji, with no other info.
        -a:  (animated) Forces to show the emoji as animated (if possible).
    Examples:
        {prefix}e catThink
    """
    # TODO: Handle the case where a builtin emoji has the same name as a custom emoji
    # Any way of testing whether an emoji from get is a builtin?
    # Emojis with the same name are shown
    if not ctx.arg_str and ctx.used_cmd_name in ["ree", "sree"]:
        ctx.arg_str = "reeeeeeeeeee"
    if not ctx.arg_str:
        if ctx.server:
            emojis = filter(lambda e: e.server == ctx.server, ctx.bot.get_all_emojis())
            if emojis:
                await ctx.reply("Custom emojis in this server:\n{}".format(" ".join(map(str, emojis))))
                return
            else:
                await ctx.reply("No custom emojis in this server! You can search for emojis using this command!")
                return
        else:
            await ctx.reply("Search for emojis using {}`emoji <search>`".format(ctx.used_prefix))
            return
    id_str = 0
    em_str = 0
    emoji = None
    emojis = []
    if ctx.used_cmd_name in ["ee", "ree", "sree"]:
        ctx.flags["e"] = True
    embed = discord.Embed(title=None if ctx.flags["e"] else "Emoji info!", color=discord.Colour.light_grey())
    if ctx.arg_str.endswith(">") and ctx.arg_str.startswith("<"):
        id_str = ctx.arg_str[ctx.arg_str.rfind(":") + 1:-1]
        if id_str.isdigit():
            emoji = discord.utils.get(ctx.bot.get_all_emojis(), id=id_str)
            if emoji is None:
                link = "https://cdn.discordapp.com/emojis/{}.{}".format(id_str, "gif" if ctx.arg_str[1] == "a" or ctx.flags["a"] else "png")
                embed.set_image(url=link)
                if not ctx.flags["e"]:
                    emb_fields = [("Name", ctx.arg_str[ctx.arg_str.find(":") + 1:ctx.arg_str.rfind(":")], 0),
                                  ("ID", id_str, 0),
                                  ("Link", "[Click me](" + link + ")", 0)]
                    await ctx.emb_add_fields(embed, emb_fields)
                try:
                    await ctx.reply(None if ctx.flags["e"] else "I couldn't find the emoji in my servers, but here is what I have!", embed=embed)
                except Exception:
                    await ctx.reply("I couldn't understand or find the emoji in your message")
                return
    else:
        em_str = ctx.arg_str.strip(":")
        emoji = discord.utils.get(ctx.bot.get_all_emojis(), name=em_str)
        emojis = list(filter(lambda e: (em_str.lower() in e.name.lower()), ctx.bot.get_all_emojis()))
        emoji = emoji if emoji else (emojis[0] if emojis else None)
        if not emoji:
            await ctx.reply("I cannot see any matching emojis.\nPlease note I cannot handle built in emojis at this time.")
            return
    url = "https://cdn.discordapp.com/emojis/{}.{}".format(emoji.id, "gif" if ctx.flags["a"] else "png")
    embed.set_image(url=url)
    if not ctx.flags["e"]:
        created_ago = ctx.strfdelta(datetime.utcnow() - emoji.created_at)
        created = emoji.created_at.strftime("%-I:%M %p, %d/%m/%Y")
        emojis = emojis[:10] if emojis else filter(lambda e: (e.name == emoji.name) and (e != emoji), ctx.bot.get_all_emojis())
        emoj_similar_str = " ".join(map(str, emojis))
        emb_fields = [("Name", emoji.name, 0),
                      ("ID", emoji.id, 0),
                      ("Link", emoji.url, 0),
                      ("Originating server", emoji.server.name if emoji.server else "Built in", 0),
                      ("Created at", "{}({} ago)".format(created, created_ago), 0)]
        if emoj_similar_str:
            emb_fields.append(("Some other matching emojis", emoj_similar_str, 0))
        await ctx.emb_add_fields(embed, emb_fields)
    try:
        if ctx.used_cmd_name in ["ree", "sree"]:
            logs = ctx.bot.logs_from(ctx.ch, limit=2)
            async for message in logs:
                message = message
            await ctx.bot.add_reaction(message, emoji)
            if ctx.used_cmd_name == "sree":
                try:
                    await ctx.bot.delete_message(ctx.msg)
                except discord.Forbidden:
                    pass
        else:
            await ctx.reply(embed=embed)
    except discord.HTTPException:
        if ctx.flags["a"]:
            await ctx.reply("Failed to send animated emoji. Maybe this emoji isn't animated?")
        else:
            await ctx.reply("Failed to send the emoji!")


@cmds.cmd(name="colour",
          category="Utility",
          short_help="Displays information about a colour",
          aliases=["color"])
async def cmd_colour(ctx):
    """
    Usage:
        {prefix}colour <hexvalue>
    Description:
        Displays some detailed information about the colour, including a picture.
    Examples:
        {prefix}colour #0047AB
        {prefix}colour 0047AB
    """
    # TODO: Support for names, rgb etc as well
    hexstr = ctx.arg_str.strip("#")
    if not (len(hexstr) == 6 and all(c in string.hexdigits for c in hexstr)):
        await ctx.reply("Please give me a valid hex colour (e.g. #0047AB)")
        return
    fetchstr = "http://thecolorapi.com/id?hex={}&format=json".format(hexstr)
    async with aiohttp.get(fetchstr) as r:
        if r.status == 200:
            js = await r.json()
            inverted = col_invert(hexstr)
            prop_list = ["rgb", "hsl", "hsv", "cmyk", "XYZ"]
            value_list = [js[prop]["value"][len(prop):] for prop in prop_list]
            desc = ctx.prop_tabulate(prop_list, value_list)
            embed = discord.Embed(title="Colour info for `#{}`".format(hexstr), color=discord.Colour(int(hexstr, 16)), description=desc)
            embed.set_thumbnail(url="http://placehold.it/150x150.png/{}/{}?text={}".format(hexstr, inverted, "%23" + hexstr))
            embed.add_field(name="Closest named colour", value="`{}` (Hex `{}`)".format(js["name"]["value"], js["name"]["closest_named_hex"]))
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("Sorry, something went wrong while fetching your colour! Please try again later")
            return


def col_invert(color_to_convert):
    table = str.maketrans('0123456789abcdef', 'fedcba9876543210')
    return color_to_convert.lower().translate(table).upper()


@cmds.cmd(name="names",
          category="Info",
          short_help="Lists previous recorded names for a user.",
          aliases=["namesfor", "whowas"])
@cmds.execute("user_lookup", in_server=True, greedy=True)
async def cmd_names(ctx):
    """
    Usage:
        {prefix}names [user]
    Description:
        Displays the past names I have seen for the provided user, or yourself.
    """
    user = ctx.author
    if ctx.arg_str != "":
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return
    usernames = await ctx.bot.data.users.get(user.id, "name_history")
    if not usernames:
        await ctx.reply("I haven't seen this user change their name!")
        return
    await ctx.pager(ctx.paginate_list(usernames, title="Usernames for {}".format(user)))


def load_into(bot):
    bot.data.users.ensure_exists("piggybank_amount", "piggybank_history", "piggybank_goal", shared=False)
