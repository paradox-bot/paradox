from paraCH import paraCH
import discord
from datetime import datetime
from pytz import timezone
import iso8601
import traceback
import string
import aiohttp


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
    await ctx.reply(ctx.arg_str if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("userinfo",
          category="Utility",
          short_help="Shows the user's information")
@cmds.require("in_server")
@cmds.execute("user_lookup", in_server=True)
async def cmd_userinfo(ctx):
    """
    Usage:
        {prefix}userinfo [user]
    Description:
        Sends information on the provided user, or yourself.
    """
    user = ctx.author
    if ctx.arg_str != "":
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return

    bot_emoji = ctx.bot.objects["emoji_bot"]
    statusdict = {"offline": "Offline/Invisible",
                  "dnd": "Do Not Disturb",
                  "online": "Online",
                  "idle": "Idle/Away"}
    colour = (user.colour if user.colour.value else discord.Colour.light_grey())
    embed = discord.Embed(type="rich", color=colour)
    embed.set_author(name="{user.name} ({user.id})".format(user=user),
                     icon_url=user.avatar_url,
                     url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)

    name = "{}{}".format(bot_emoji if user.bot else "", user)
    game = "Playing {}".format(user.game if user.game else "nothing")
    status = "{}, {}".format(statusdict[str(user.status)], game)
    shared = len(list(filter(lambda m: m.id == user.id, ctx.bot.get_all_members())))
    joined_ago = ctx.strfdelta(datetime.utcnow()-user.joined_at)
    joined = user.joined_at.strftime("%-I:%M %p, %d/%m/%Y")
    created_ago = ctx.strfdelta(datetime.utcnow()-user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    roles = [r.name for r in user.roles if r.name != "@everyone"]
    roles = ('`' + '`, `'.join(roles) + '`') if roles else "None"

    emb_fields = [("Full name", name, 0),
                  ("Status", status, 0),
                  ("Nickname", user.display_name, 0),
                  ("Shared servers", shared, 0),
                  ("Joined at", "{} ({} ago)".format(joined, joined_ago), 0),
                  ("Created at", "{} ({} ago)".format(created, created_ago), 0),
                  ("Roles", roles, 0)]
    await ctx.emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)


@cmds.cmd("discrim",
          category="Utility",
          short_help="Searches for users with a given discrim")
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
    discrim = "0"*(4-len(args)) + args
    found_members = set(filter(lambda m: m.discriminator == discrim, p))
    if len(found_members) == 0:
        await ctx.reply("No users with this discrim found!")
        return
    user_info = [(str(m), "({})".format(m.id)) for m in found_members]
    max_len = len(max(list(zip(*user_info))[0], key=len))
    user_strs = ["{0[0]:^{max_len}} {0[1]:^25}".format(user, max_len=max_len) for user in user_info]
    await ctx.reply("`{2}` user{1} found:```asciidoc\n= Users found =\n{0}\n```".format('\n'.join(user_strs),
                                                                                        "s" if len(user_strs) > 1 else "",
                                                                                        len(user_strs)))
    # TODO: Make this splittable across codeblocks


@cmds.cmd("piggybank",
          category="Utility",
          short_help="Keep track of money added towards a goal.")
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
            msg += "\nYou have achieved {:.1%} of your goal (${:.2f})".format(bank_amount/goal, goal)
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
                msg += "\nYou have now achieved {:.1%} of your goal (${:.2f}).".format(bank_amount/goal, goal)
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


@cmds.cmd("set",
          category="User info",
          short_help="Shows or sets a user setting")
async def cmd_set(ctx):
    """
    Usage:
        {prefix}set [settingname [value]]
    Description:
        Sets <settingname> to <value>, shows the value of <settingname>, or lists your available settings.
        Temporary implementation, more is coming soon!
    """
    if ctx.arg_str == '':
        await ctx.reply("```timezone: Country/City, some short-hands are accepted, use ETC/+10 etc to set to GMT-10.```")
        return
    action = ctx.params[0]
    if action == "timezone":
        if len(ctx.params) == 1:
            tz = await ctx.data.users.get(ctx.authid, "tz")
            if tz:
                msg = "Your current timezone is `{}`".format(tz)
            else:
                msg = "You haven't set your timezone! Use `{prefix}set timezone <timezone>` to set it!".format(ctx.used_prefix)
            await ctx.reply(msg)
            return
        tz = ' '.join(ctx.params[1:])
        try:
            timezone(tz)
        except Exception:
            await ctx.reply("Unfortunately, I don't understand this timezone. More options will be available soon.")
            return
        await ctx.data.users.set(ctx.authid, "tz", tz)
        await ctx.reply("Your timezone has been set to `{}`".format(tz))

# User info commands


@cmds.cmd("time",
          category="User info",
          short_help="Shows the current time for a user")
@cmds.execute("user_lookup", in_server=True)
async def cmd_time(ctx):
    """
    Usage:
        {prefix}time [mention | id | partial name]
    Description:
        Gives the time for the mentioned user or yourself.
        Requires the user to have set the usersetting "timezone".
    """
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
        if user == ctx.authid:
            await ctx.reply("You haven't set your timezone! Set it using \"{}set timezone <timezone>\"!".format(ctx.used_prefix))
        else:
            await ctx.reply("This user hasn't set their timezone. Ask them to set it using \"{}set timezone <timezone>\"!".format(ctx.used_prefix))
        return
    try:
        TZ = timezone(tz)
    except Exception:
        await ctx.reply("An invalid timezone was provided in the database. Aborting... \n **Error Code:** `ERR_OBSTRUCTED_DB`")
        trace = traceback.format_exc()
        await ctx.log(trace)
        return
    timestr = 'The current time for **{}** is **%-I:%M %p (%Z(%z))** on **%a, %d/%m/%Y**'\
        .format(ctx.server.get_member(user).display_name)
    timestr = iso8601.parse_date(datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
    await ctx.reply(timestr)


@cmds.cmd("profile",
          category="User info",
          short_help="Displays a user profile")
@cmds.execute("user_lookup", in_server=True)
async def cmd_profile(ctx):
    """
    Usage:
        {prefix}profile [user]
    Description:
        Displays the provided user's profile, or your own.
    """
    user = ctx.author
    if ctx.arg_str != "":
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return

    badge_dict = {"master_perm": "botowner",
                  "manager_perm": "botmanager"}
    badges = ""
    for badge in badge_dict:
        (code, msg) = await cmds.checks[badge](ctx)
        if code == 0:
            badge_emoj = ctx.bot.objects["emoji_"+badge_dict[badge]]
            if badge_emoj is not None:
                badges += str(badge_emoj) + " "

    created_ago = ctx.strfdelta(datetime.utcnow()-user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    rep = await ctx.data.users.get(user.id, "rep")

    embed = discord.Embed(type="rich", color=user.colour) \
        .set_author(name="{user} ({user.id})".format(user=user),
                    icon_url=user.avatar_url)
    if badges:
        embed.add_field(name="Badges", value=badges, inline=False)

    embed.add_field(name="Level",
                    value="(Coming Soon!)", inline=True) \
        .add_field(name="XP",
                   value="(Coming Soon!)", inline=True) \
        .add_field(name="Reputation",
                   value=rep, inline=True) \
        .add_field(name="Premium",
                   value="No", inline=True)
    tz = await ctx.data.users.get(user.id, "tz")
    if tz:
        try:
            TZ = timezone(tz)
        except Exception:
            await ctx.reply("An invalid timezone was provided in the database. Aborting... \n **Error Code:** `ERR_CORRUPTED_DB`")
            return
        timestr = '%-I:%M %p on %a, %d/%m/%Y'
        timestr = iso8601.parse_date(datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
        embed.add_field(name="Current Time", value="{}".format(timestr), inline=False)
    embed.add_field(name="Created at",
                    value="{} ({} ago)".format(created, created_ago), inline=False)
    await ctx.reply(embed=embed)


@cmds.cmd(name="emoji",
          category="Utility",
          short_help="Displays info and enlarges a custom emoji",
          aliases=["e"])
@cmds.execute("flags", flags=["e"])
async def cmd_emoji(ctx):
    """
    Usage:
        {prefix}emoji <emoji> [-e]
    Description:
        Displays some information about the provided custom emoji, and sends an enlarged version.
        Built in emoji support is coming soon!
    Flags:
        -e:  (enlarge) Only shows the enlarged emoji, with no other info.
    """
    # TODO: Handle the case where a builtin emoji has the same name as a custom emoji
    # Any way of testing whether an emoji from get is a builtin?
    # Emojis with the same name are shown
    id_str = 0
    em_str = 0
    emoji = None
    embed = discord.Embed(title=None if ctx.flags["e"] else "Emoji info!", color=discord.Colour.light_grey())
    if ctx.arg_str.endswith(">") and ctx.arg_str.startswith("<"):
        id_str = ctx.arg_str[ctx.arg_str.rfind(":") + 1:-1]
        if id_str.isdigit():
            emoji = discord.utils.get(ctx.bot.get_all_emojis(), id=id_str)
            if emoji is None:
                link = "https://cdn.discordapp.com/emojis/{}.{}".format(id_str, "gif" if ctx.arg_str[1] == "a" else "png")
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
        if not emoji:
            await ctx.reply("I couldn't understand or find the emoji in your message. Please note I cannot handle built in emojis at this time.")
            return
    embed.set_image(url=emoji.url)
    if not ctx.flags["e"]:
        created_ago = ctx.strfdelta(datetime.utcnow()-emoji.created_at)
        created = emoji.created_at.strftime("%-I:%M %p, %d/%m/%Y")
        same_emojis = filter(lambda e: (e.name == emoji.name) and (e != emoji), ctx.bot.get_all_emojis())
        emoj_same_str = " ".join(map(str, same_emojis))
        emb_fields = [("Name", emoji.name, 0),
                      ("ID", emoji.id, 0),
                      ("Link", emoji.url, 0),
                      ("Originating server", emoji.server.name if emoji.server else "Built in", 0),
                      ("Created at", "{}({} ago)".format(created, created_ago), 0)]
        if emoj_same_str:
            emb_fields.append(("Emojis I can see with the same name", emoj_same_str, 0))
        await ctx.emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)


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
    if not (len(hexstr) == 6 or all(c in string.hexdigits for c in hexstr)):
        await ctx.reply("Please give me a valid hex colour (e.g. #0047AB)")
        return
    fetchstr = "http://thecolorapi.com/id?hex={}&format=json".format(hexstr)
    async with aiohttp.get(fetchstr) as r:
        if r.status == 200:
            js = await r.json()
            embed = discord.Embed(title="Colour info for `#{}`".format(hexstr), color=discord.Colour(int(hexstr, 16)))
            embed.set_thumbnail(url="http://placehold.it/150x150.png/{}/000000?text={}".format(hexstr, js["name"]["value"]))
            embed.add_field(name="Closest named colour", value="`{}` (Hex `{}`)".format(js["name"]["value"], js["name"]["closest_named_hex"]))
            embed.add_field(name="Values", value="```\n{}\n{}\n{}\n{}\n{}\n```".format(js["rgb"]["value"],
                                                                                       js["hsl"]["value"],
                                                                                       js["hsv"]["value"],
                                                                                       js["cmyk"]["value"],
                                                                                       js["XYZ"]["value"]))
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("Sorry, something went wrong while fetching your colour! Please try again later")
            return


@cmds.cmd(name="roleinfo",
          category="Utility",
          short_help="Displays information about a role",
          aliases=["role"])
@cmds.require("in_server")
async def cmd_role(ctx):
    """
    Usage:
        {prefix}roleinfo <rolename>
    Description:
        Provides information about the given role.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a role!")
        return
    # TODO: Letting find_role handle all input and output for finding.
    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return
    title = "Roleinfo for `{role.name}` (id: `{role.id}`)".format(role=role)
    colour = str(role.colour) if role.colour.value else str(discord.Colour.light_grey())
#    thumbnail = "http://placehold.it/150x150.png/{}/000000?text={}".format(colour.strip("#"), colour)
    num_users = len([user for user in ctx.server.members if (role in user.roles)])
    created_ago = ctx.strfdelta(datetime.utcnow()-role.created_at)
    created = role.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    created_at = "{} ({} ago)".format(created, created_ago)
    hoisted = "Yes" if role.hoist else "No"
    mentionable = "Yes" if role.mentionable else "No"

    pos = role.position
    server_roles = sorted(ctx.server.roles, key=lambda role: role.position)
    position = "```\n"
    for i in reversed(range(-3,4)):
        line_pos = pos + i
        if line_pos < 0:
            break
        if line_pos >= len(server_roles):
            continue
        position += "{0:<4}{1}{2:<20}\n".format(str(line_pos)+".", " " * 4 + (">" if i == 0 else " "), str(server_roles[line_pos]))
    position += "```"
    if role > ctx.author.top_role:
        diff_str = "(Higher than your highest role)"
    elif role < ctx.author.top_role:
        diff_str = "(Lower than your highest role)"
    elif role == ctx.author.top_role:
        diff_str = "(This is your highest role!)"
    position += diff_str

    embed = discord.Embed(title=title, colour=role.colour if role.colour.value else discord.Colour.light_grey())
#    embed.set_thumbnail(url=thumbnail)
    emb_fields = [("Colour", role.colour, 0),
                  ("Created at", created_at, 0),
                  ("Hoisted", hoisted, 0),
                  ("Mentionable", mentionable, 0),
                  ("Number of members", num_users, 0),
                  ("Position in the heirachy", position, 0)]
    await ctx.emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)




