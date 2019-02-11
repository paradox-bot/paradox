import discord
from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("tag", category="Utility", short_help="Remember pieces of text", aliases=["tags"])
@cmds.require("in_server")
@cmds.execute("flags", flags=["create", "info", "update", "from=", "delete"])
async def cmd_tag(ctx):
    """
    Usage:
        {prefix}tag <tagname> [--create | --info | --from <msgid> | --delete]
    Description:
        View or create a server "tag", a message which can later be recalled using the tag name.
    Flags:2
        --create:: Starts the interactive creation process for the tag.
        --info:: Displays some basic info about that tag.
        --from:: Creates a tag using the content of a message as the tag content.
        --delete:: Deletes a tag.
    """

    if ctx.flags["create"] or ctx.flags["from"]:
        tag_info = await create_tag(ctx)
        if tag_info is None:
            return

        current_tags = await ctx.bot.data.servers.get(ctx.server.id, "tags")
        current_tags = current_tags if current_tags else {}
        current_tags[tag_info["name"]] = tag_info
        await ctx.bot.data.servers.set(ctx.server.id, "tags", current_tags)
        return
    current_tags = await ctx.bot.data.servers.get(ctx.server.id, "tags")
    current_tags = current_tags if current_tags else {}
    if ctx.arg_str == "":
        if current_tags:
            await ctx.reply("Available tags are `{}`.".format("`, `".join(current_tags.keys())))
        else:
            await ctx.reply("No tags have been created on this server.")
        return
    if ctx.arg_str not in current_tags:
        await ctx.reply("This tag does not exist.")
        (code, msg) = await ctx.CH.checks["in_server_has_mod"](ctx)
        if code != 0:
            return
        else:
            resp = await ctx.ask("Would you like to create this tag?")
            if resp:
                tag_info = await create_tag(ctx)
                if tag_info is None:
                    return

                current_tags = await ctx.bot.data.servers.get(ctx.server.id, "tags")
                current_tags = current_tags if current_tags else {}
                current_tags[tag_info["name"]] = tag_info
                await ctx.bot.data.servers.set(ctx.server.id, "tags", current_tags)
            return
    tag = current_tags[ctx.arg_str]

    if ctx.flags["delete"]:
        (code, msg) = await ctx.CH.checks["in_server_has_mod"](ctx)
        if code != 0:
            await ctx.reply("Sorry, you must be a moderator to delete tags")
            return None
        current_tags.pop(ctx.arg_str, None)
        await ctx.bot.data.servers.set(ctx.server.id, "tags", current_tags)
        await ctx.reply("The tag was successfully deleted.")
        return

    roleid = tag["role"]
    if roleid:
        role = discord.utils.get(ctx.server.roles, id=roleid)
    if ctx.flags["info"]:
        embed = discord.Embed(title="Tag Info")
        embed.add_field(name="Tag Name", value=tag["name"], inline=False)
        embed.add_field(name="Tag Content", value=tag["content"], inline=False)
        embed.add_field(
            name="Usable by",
            value=role.name if roleid and role else ("Everyone" if not roleid else "Noone"),
            inline=False)
        embed.set_footer(text="Created at {} by {} ({})".format(tag["time"], (
            await ctx.bot.get_user_info(tag["author"])).name, tag["author"]))
        await ctx.reply(embed=embed)
        return
    if roleid:
        if not role:
            await ctx.reply("The required role to use this tag no longer exists.")
            return
        if role not in ctx.member.roles:
            await ctx.reply("You don't have the required role to use this tag.")
            return
    await ctx.reply(current_tags[ctx.arg_str]["content"])


async def create_tag(ctx):
    """
        Interactive tag creation interface.
        Arguments:
            ctx -- Command context to create in.
    """
    (code, msg) = await ctx.CH.checks["in_server_has_mod"](ctx)
    if code != 0:
        await ctx.reply("Sorry, you must be a moderator to create tags")
        return None

    tag_name = ctx.arg_str if ctx.arg_str else None
    content = None
    created_time = ctx.msg.timestamp
    created_time_str = created_time.strftime("%-I:%M %p, %d/%m/%Y")

    if ctx.flags["from"]:
        try:
            message = await ctx.bot.get_message(ctx.ch, ctx.flags["from"])
            content = message.content
        except discord.NotFound:
            await ctx.reply("I couldn't find a message with this id in this channel!")
            return None

    create_embed = discord.Embed(title="Creating Tag", author=ctx.author.display_name)
    create_embed.add_field(name="Tag Name", value=tag_name if tag_name else "Not set", inline=False)
    create_embed.add_field(name="Tag Content", value=content if content else "Not set", inline=False)
    create_embed.add_field(name="Usable by", value="Everyone", inline=False)
    create_embed.set_footer(text="Created at {}".format(created_time_str))
    embed_msg = await ctx.reply(embed=create_embed)

    if not tag_name:
        tag_name = await ctx.input("Please enter the tag name (or `cancel` to abort)")
        if tag_name in ["cancel", "Cancel"]:
            await ctx.reply("User canceled, aborting")
            tag_name = None
        elif tag_name is None:
            await ctx.reply("Request timed out, aborting")
        if tag_name is None:
            try:
                await ctx.bot.delete_message(embed_msg)
            except discord.NotFound:
                pass
            return None
        create_embed.set_field_at(0, name="Tag Name", value=tag_name)
        await ctx.bot.edit_message(embed_msg, embed=create_embed)

    if not content:
        content = await ctx.input("Please enter the content you want for the tag (or `cancel` to abort)")
        if content in ["cancel", "Cancel"]:
            await ctx.reply("User canceled, aborting")
            content = None
        elif content is None:
            await ctx.reply("Request timed out, aborting")
        if content is None:
            try:
                await ctx.bot.delete_message(embed_msg)
            except discord.NotFound:
                pass
            return None
        create_embed.set_field_at(1, name="Tag Content", value=content)
        await ctx.bot.edit_message(embed_msg, embed=create_embed)

    role_name = await ctx.input(
        "Enter the role required to use this tag, or `everyone` or `.` if everyone can use it (or `cancel` to abort)")
    if role_name in ["cancel", "Cancel"]:
        await ctx.reply("User canceled, aborting")
        role_name = None
    elif role_name is None:
        await ctx.reply("Request timed out, aborting")
    elif role_name.lower() in ["everyone", "."]:
        role = None
    else:
        role = await ctx.find_role(role_name, create=True, interactive=True)
        if not role:
            return None
    if role_name is None:
        try:
            await ctx.bot.delete_message(embed_msg)
        except discord.NotFound:
            pass
        return None
    create_embed.set_field_at(2, name="Usable by", value=role.name if role else "Everyone")
    await ctx.bot.edit_message(embed_msg, embed=create_embed)
    await ctx.reply("Your tag `{}` has been created!".format(tag_name))
    return {
        "name": tag_name,
        "content": content,
        "role": role.id if role else None,
        "time": created_time_str,
        "author": ctx.authid,
        "server": ctx.server.id
    }


def load_into(bot):
    bot.data.servers.ensure_exists("tags")
