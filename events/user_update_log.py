import discord
from datetime import datetime

async def log_member_update(bot, before, after):
    userlog = await bot.data.servers.get(before.server.id, "userlog_ch")
    if not userlog:
        return
    userlog = before.server.get_channel(userlog)
    if not userlog:
        return

    log_ignore = await bot.data.servers.get(before.server.id, "userlog_ignore")
    if before.id in log_ignore:
        return

    events = await bot.data.servers.get(before.server.id, "userlog_events")

    desc_lines = []
    image_url = None
    if (events is None or "username" in events) and before.name != after.name:
        desc_lines.append("**Username Changed** for {}".format(after.mention))
        desc_lines.append("`Before:` {}".format(before.name))
        desc_lines.append("`After:` {}".format(after.name))

    if (events is None or "nickname" in events) and before.nick != after.nick:
        desc_lines.append("**Nickname Changed** for {}".format(after.mention))
        desc_lines.append("`Before:` {}".format(before.nick))
        desc_lines.append("`After:` {}".format(after.nick))

    if (events is None or "avatar" in events) and before.avatar_url != after.avatar_url:
        desc_lines.append("**Avatar Changed** for {}".format(after.mention))
        old_av = "[Old Avatar]({})".format(before.avatar_url) if before.avatar_url else "None"
        new_av = "[New Avatar]({})".format(after.avatar_url) if after.avatar_url else "None"
        desc_lines.append("`Before:` {}".format(old_av))
        desc_lines.append("`After:` {}".format(new_av))
        image_url = after.avatar_url if after.avatar_url else None

    if (events is None or "roles" in events) and before.roles != after.roles:
        before_roles = [role.name for role in before.roles]
        after_roles = [role.name for role in after.roles]
        added_roles = [role for role in after_roles if role not in before_roles]
        removed_roles = [role for role in before_roles if role not in after_roles]
        desc_lines.append("**Roles Updated** for {}".format(after.mention))
        if added_roles:
            desc_lines.append("Added roles `{}`".format("`, `".join(added_roles)))
        if removed_roles:
            desc_lines.append("Removed roles `{}`".format("`, `".join(removed_roles)))

    if not desc_lines:
        return

    description = "\n".join(desc_lines)
    colour = (after.colour if after.colour.value else discord.Colour.light_grey())

    embed = discord.Embed(color=colour, description = description)
    if image_url:
        embed.set_thumbnail(url=image_url)
    embed.set_footer(text=datetime.utcnow().strftime("Sent at %-I:%M %p, %d/%m/%Y"))
    await bot.send_message(userlog, embed=embed)



def load_into(bot):
    bot.add_after_event("member_update", log_member_update, priority=9)
