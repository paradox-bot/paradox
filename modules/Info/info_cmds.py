from datetime import datetime, timedelta

import discord
from paraCH import paraCH

cmds = paraCH()

# Provides serverinfo, userinfo, roleinfo, whohas, avatar


@cmds.cmd(
    name="roleinfo", category="Info", short_help="Displays information about a role", aliases=["role", "rinfo", "ri"])
@cmds.require("in_server")
async def cmd_role(ctx):
    """
    Usage:
        {prefix}roleinfo <rolename>
    Description:
        Provides information about the given role.
    """
    server_roles = sorted(ctx.server.roles, key=lambda role: role.position)

    if ctx.arg_str.strip() == "":
        await ctx.pager(ctx.paginate_list([role.name for role in reversed(server_roles)]))
        return
    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return

    title = "{role.name} (id: {role.id})".format(role=role)

    colour = role.colour if role.colour.value else discord.Colour.light_grey()
    #    thumbnail = "http://placehold.it/150x150.png/{}/000000?text={}".format(colour.strip("#"), colour)
    num_users = len([user for user in ctx.server.members if (role in user.roles)])
    created_ago = "({} ago)".format(ctx.strfdelta(datetime.utcnow() - role.created_at, minutes=False))
    created = role.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    #    created_at = "{} ({} ago)".format(created, created_ago)
    hoisted = "Yes" if role.hoist else "No"
    mentionable = "Yes" if role.mentionable else "No"

    prop_list = ["Colour", "Hoisted", "Mentionable", "Number of members", "Created at", ""]
    value_list = [str(role.colour), hoisted, mentionable, num_users, created, created_ago]
    desc = ctx.prop_tabulate(prop_list, value_list)

    pos = role.position
    position = "```markdown\n"
    for i in reversed(range(-3, 4)):
        line_pos = pos + i
        if line_pos < 0:
            break
        if line_pos >= len(server_roles):
            continue
        position += "{0:<4}{1}{2:<20}\n".format(
            str(line_pos) + ".", " " * 4 + (">" if str(server_roles[line_pos]) == str(role) else " "),
            str(server_roles[line_pos]))
    position += "```"
    if role > ctx.author.top_role:
        diff_str = "(Higher than your highest role)"
    elif role < ctx.author.top_role:
        diff_str = "(Lower than your highest role)"
    elif role == ctx.author.top_role:
        diff_str = "(This is your highest role!)"
    position += diff_str

    embed = discord.Embed(title=title, colour=colour, description=desc)
    #    embed.set_thumbnail(url=thumbnail)
    emb_fields = [("Position in the hierachy", position, 0)]
    await ctx.emb_add_fields(embed, emb_fields)
    out_msg = await ctx.reply(embed=embed, dm=ctx.bot.objects["brief"])
    if out_msg and ctx.bot.objects["brief"]:
        await ctx.confirm_sent(reply="Roleinfo sent!")


@cmds.cmd(
    name="rolemembers",
    category="Info",
    short_help="Lists members with a particular role.",
    aliases=["rolemems", "whohas"])
@cmds.require("in_server")
async def cmd_rolemembers(ctx):
    """
    Usage:
        {prefix}rolemembers <rolename>
    Description:
    Displays the users with this role.
    """

    if ctx.arg_str.strip() == "":
        await ctx.reply("Please give me a role to list the members of.")
        return

    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return

    members = [str(mem) for mem in ctx.server.members if role in mem.roles]
    if len(members) == 0:
        await ctx.reply("No members have this role")
        return

    out_msg = await ctx.pager(
        ctx.paginate_list(members, title="Members in {}".format(role.name)), dm=ctx.bot.objects["brief"])
    if out_msg and ctx.bot.objects["brief"]:
        await ctx.confirm_sent(reply="Rolemembers sent!")


@cmds.cmd("userinfo", category="Info", short_help="Shows the user's information", aliases=["uinfo", "ui"])
@cmds.require("in_server")
@cmds.execute("user_lookup", in_server=True, greedy=True)
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
    statusdict = {
        "offline": ("Offline/Invisible", ctx.bot.objects["emoji_offline"]),
        "dnd": ("Do Not Disturb", ctx.bot.objects["emoji_dnd"]),
        "online": ("Online", ctx.bot.objects["emoji_online"]),
        "idle": ("Idle/Away", ctx.bot.objects["emoji_idle"])
    }
    colour = (user.colour if user.colour.value else discord.Colour.light_grey())

    name = "{} {}".format(user, bot_emoji if user.bot else "")
    game = user.game if user.game else "Nothing"
    status = "{1}{0}".format(*statusdict[str(user.status)])
    shared = "{} servers".format(len(list(filter(lambda m: m.id == user.id, ctx.bot.get_all_members()))))
    joined_ago = "({} ago)".format(ctx.strfdelta(datetime.utcnow() - user.joined_at, minutes=False))
    joined = user.joined_at.strftime("%-I:%M %p, %d/%m/%Y")
    created_ago = "({} ago)".format(ctx.strfdelta(datetime.utcnow() - user.created_at, minutes=False))
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    usernames = await ctx.bot.data.users.get(user.id, "name_history")
    name_list = "{}{}".format("..., " if len(usernames) > 10 else "", ", ".join(
        usernames[-10:])) if usernames else "No recent past usernames."
    nicknames = await ctx.bot.data.members.get(ctx.server.id, user.id, "nickname_history")
    nickname_list = "{}{}".format("..., " if len(nicknames) > 10 else "", ", ".join(
        nicknames[-10:])) if nicknames else "No recent past nicknames."
    last_status = await ctx.bot.data.users.get(user.id, "old_status")
    if last_status:
        status_str = "(Was {})".format(statusdict[last_status[0]][0])
        last_seen = int(datetime.utcnow().strftime('%s')) - last_status[2]
        if last_seen > 60:
            seen_ago = "{} ago".format(ctx.strfdelta(timedelta(seconds=last_seen)))
        else:
            seen_ago = "Now"


#        last_seen =  "{}, {}".format(seen_ago, status_str)
    else:
        seen_ago = "No status changes seen!"
        status_str = ""

    prop_list = [
        "Full name", "Nickname", "Names", "Nicknames", "Status", "Playing", "Seen in", "Last seen", "", "Joined at", "",
        "Created at", ""
    ]
    value_list = [
        name, user.display_name, name_list, nickname_list, status, game, shared, seen_ago, status_str, joined,
        joined_ago, created, created_ago
    ]
    desc = ctx.prop_tabulate(prop_list, value_list)

    roles = [r.name for r in user.roles if r.name != "@everyone"]
    roles = ('`' + '`, `'.join(roles) + '`') if roles else "None"

    joined = sorted(ctx.server.members, key=lambda mem: mem.joined_at)
    pos = joined.index(user)
    positions = []
    for i in range(-3, 4):
        line_pos = pos + i
        if line_pos < 0:
            continue
        if line_pos >= len(joined):
            break
        positions.append("{0:<4}{1}{2:<20}".format(
            str(line_pos + 1) + ".", " " * 4 + (">" if joined[line_pos] == user else " "), str(joined[line_pos])))
    join_seq = "```markdown\n{}\n```".format("\n".join(positions))

    embed = discord.Embed(type="rich", color=colour, description=desc)
    embed.set_author(
        name="{user.name} (id: {user.id})".format(user=user), icon_url=user.avatar_url, url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)

    emb_fields = [("Roles", roles, 0), ("Join order", join_seq, 0)]
    await ctx.emb_add_fields(embed, emb_fields)

    out_msg = await ctx.reply(embed=embed, dm=ctx.bot.objects["brief"])
    if out_msg and ctx.bot.objects["brief"]:
        await ctx.confirm_sent(reply="Userinfo sent!")


@cmds.cmd("serverinfo", category="Info", short_help="Shows server info.", aliases=["sinfo", "si"])
@cmds.execute("flags", flags=["icon"])
@cmds.require("in_server")
async def cmd_serverinfo(ctx):
    """
    Usage:
        {prefix}serverinfo [--icon]
    Description:
        Shows information about the server you are in.
        With --icon, just displays the server icon.
    """
    if ctx.flags["icon"]:
        embed = discord.Embed(color=discord.Colour.light_grey())
        embed.set_image(url=ctx.server.icon_url)

        out_msg = await ctx.reply(embed=embed, dm=ctx.bot.objects["brief"])
        if out_msg and ctx.bot.objects["brief"]:
            await ctx.confirm_sent(reply="Icon sent!")
        return

    regions = ctx.bot.objects["regions"]
    ver = {
        "none": "None",
        "low": "Level 1 (Must have a verified email)",
        "medium": "Level 2 (Registered for more than 5 minutes)",
        "high": "Level 3 (Member for more than 10 minutes)",
        4: "Level 4 (Verified phone number)"
    }

    mfa = {0: "Disabled", 1: "Enabled"}

    text = len([c for c in ctx.server.channels if c.type == discord.ChannelType.text])
    voice = len([c for c in ctx.server.channels if c.type == discord.ChannelType.voice])
    total = text + voice

    online = 0
    idle = 0
    offline = 0
    dnd = 0
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

    server_owner = ctx.server.owner
    owner = "{} (id {})".format(server_owner, server_owner.id)
    members = "{} humans, {} bots | {} total".format(
        str(len([m for m in ctx.server.members if not m.bot])), str(len([m for m in ctx.server.members if m.bot])),
        ctx.server.member_count)
    created = ctx.server.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    created_ago = "({} ago)".format(ctx.strfdelta(datetime.utcnow() - ctx.server.created_at, minutes=False))
    channels = "{} text, {} voice | {} total".format(text, voice, total)
    status = "{} - **{}**\n{} - **{}**\n{} - **{}**\n{} - **{}**".format(Online, online, Idle, idle, Dnd, dnd, Offline,
                                                                         offline)
    avatar_url = ctx.server.icon_url
    icon = "[Icon Link]({})".format(avatar_url)
    is_large = "More than 200 members" if ctx.server.large else "Less than 200 members"

    prop_list = [
        "Owner", "Region", "Icon", "Large server", "Verification", "2FA", "Roles", "Members", "Channels", "Created at",
        ""
    ]
    value_list = [
        owner, regions[str(ctx.server.region)], icon, is_large, ver[str(ctx.server.verification_level)],
        mfa[ctx.server.mfa_level],
        len(ctx.server.roles), members, channels, created, created_ago
    ]
    desc = ctx.prop_tabulate(prop_list, value_list)

    embed = discord.Embed(
        color=server_owner.colour if server_owner.colour.value else discord.Colour.teal(), description=desc)
    embed.set_author(name="{} (id: {})".format(ctx.server, ctx.server.id))
    embed.set_thumbnail(url=avatar_url)

    emb_fields = [("Member Status", status, 0)]

    await ctx.emb_add_fields(embed, emb_fields)
    out_msg = await ctx.reply(embed=embed, dm=ctx.bot.objects["brief"])
    if out_msg and ctx.bot.objects["brief"]:
        await ctx.confirm_sent(reply="Serverinfo sent!")


@cmds.cmd("avatar", category="Info", short_help="Obtains the mentioned user's avatar, or your own.", aliases=["av"])
@cmds.execute("user_lookup", in_server=True)
async def cmd_avatar(ctx):
    user = ctx.author
    if ctx.arg_str != "":
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("I couldn't find any matching users in this server sorry!")
            return
    avatar = user.avatar_url if user.avatar_url else user.default_avatar_url
    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(name="{}'s Avatar".format(user))
    embed.set_image(url=avatar)

    out_msg = await ctx.reply(embed=embed, dm=ctx.bot.objects["brief"])
    if out_msg and ctx.bot.objects["brief"]:
        await ctx.confirm_sent(reply="Avatar sent!")
