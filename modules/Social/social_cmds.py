from paraCH import paraCH
import discord
from datetime import datetime, timedelta
from pytz import timezone
import iso8601

cmds = paraCH()


@cmds.cmd("profile",
          category="Social",
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
    tempid = ctx.authid
    ctx.authid = user.id
    # TODO: VERY BAD, quick hack so badges work.
    for badge in badge_dict:
        (code, msg) = await cmds.checks[badge](ctx)
        if code == 0:
            badge_emoj = ctx.bot.objects["emoji_" + badge_dict[badge]]
            if badge_emoj is not None:
                badges += str(badge_emoj) + " "
    ctx.authid = tempid

    created_ago = ctx.strfdelta(datetime.utcnow() - user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    rep = await ctx.data.users.get(user.id, "rep")
    given_rep = await ctx.data.users.get(user.id, "given_rep")

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
                   value="{} Received | {} Given".format(rep, given_rep), inline=True) \
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


@cmds.cmd("rep",
          category="Social",
          short_help="Give reputation to a user")
async def cmd_rep(ctx):
    """
    Usage:
        {prefix}rep [mention]
        {prefix}rep stats
    Description:
        Gives a reputation point to the mentioned user or shows your current reputation cooldown timer.

        With stats, shows how many times you have repped and your last rep time.
    """
    cooldown = 24 * 60 * 60
    now = datetime.utcnow()
    now_timestamp = int(now.strftime('%s'))
    last_rep = await ctx.data.users.get(ctx.authid, "last_rep_time")

    if ctx.arg_str == "" or ctx.arg_str.strip() == "stats":
        if last_rep is None:
            await ctx.reply("You have not yet given any reputation!\nStart giving reputation using `rep <user>`!")
            return
        last_rep = int(last_rep)
        given_ago = now_timestamp - last_rep
        if ctx.arg_str == "":
            can_give_in = cooldown - given_ago
            if can_give_in > 0:
                can_give_str = ctx.strfdelta(timedelta(seconds=can_give_in), sec=True)
                msg = "You may give reputation in {}.".format(can_give_str)
            else:
                msg = "You may now give reputation!"
        else:
            given_rep = await ctx.data.users.get(ctx.authid, "given_rep")
            last_rep_str = ctx.strfdelta(timedelta(seconds=given_ago))
            msg = "You have given **{}** reputation point{}! You last gave a reputation point **{}** ago.".format(given_rep, "s" if int(given_rep) > 1 else "", last_rep_str)
        await ctx.reply(msg)
        return
    else:
        user = await ctx.find_user(ctx.arg_str, in_server=True, interactive=True)
        if ctx.cmd_err[0] == -1:
            return
        if not user:
            await ctx.reply("I couldn't find that user in this server sorry.")
            return
        if user == ctx.author:
            await ctx.reply("You can't give yourself reputation!")
            return
        if user == ctx.me:
            await ctx.reply("Aww thanks!")
        elif user.bot:
            await ctx.reply("Bots don't need reputation points!")
            return
        if last_rep is not None:
            given_ago = now_timestamp - int(last_rep)
            if given_ago < cooldown:
                msg = "Cool down! You may give reputation in {}.".format(ctx.strfdelta(timedelta(seconds=(cooldown - given_ago)), sec=True))
                await ctx.reply(msg)
                return
        rep = await ctx.data.users.get(user.id, "rep")
        rep = int(rep) + 1 if rep else 1
        await ctx.data.users.set(user.id, "rep", str(rep))
        given_rep = await ctx.data.users.get(ctx.authid, "given_rep")
        given_rep = int(given_rep) + 1 if given_rep else 1
        await ctx.data.users.set(ctx.authid, "given_rep", str(given_rep))
        await ctx.data.users.set(ctx.authid, "last_rep_time", str(now.strftime('%s')))
        await ctx.reply("You have given a reputation point to {}".format(user.mention))
