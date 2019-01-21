from paraCH import paraCH
import discord
import string


cmds = paraCH()


class TimedOutError(Exception):
    pass


class UserCancelled(Exception):
    pass


discordColours = {"teal": discord.Colour.teal(),
                  "dark teal": discord.Colour.dark_teal(),
                  "green": discord.Colour.green(),
                  "dark green": discord.Colour.dark_green(),
                  "blue": discord.Colour.dark_purple(),
                  "dark blue": discord.Colour.dark_blue(),
                  "purple": discord.Colour.purple(),
                  "dark purple": discord.Colour.dark_purple(),
                  "magenta": discord.Colour.magenta(),
                  "dark magenta": discord.Colour.dark_magenta(),
                  "gold": discord.Colour.gold(),
                  "dark gold": discord.Colour.dark_gold(),
                  "orange": discord.Colour.orange(),
                  "dark orange": discord.Colour.dark_orange(),
                  "red": discord.Colour.red(),
                  "dark red": discord.Colour.dark_red(),
                  "lighter grey": discord.Colour.lighter_grey(),
                  "dark grey": discord.Colour.dark_grey(),
                  "light grey": discord.Colour.light_grey(),
                  "darker grey": discord.Colour.darker_grey()}


async def print_menu(ctx, items, title=None):
    item_names = [item[0] for item in items]
    nice_list = ctx.paginate_list(item_names, title=title)[0]

    message = ctx.objs["menu_msg"] if "menu_msg" in ctx.objs else None
    if message is None:
        message = await ctx.reply(nice_list)
    else:
        await ctx.bot.edit_message(message, nice_list)
    return message


async def run_menu(ctx, items, title=None, message=None, on_redraw=None):
    ctx.objs["menu_msg"] = message
    ctx.objs["menu_items"] = items
    ctx.objs["menu_title"] = title
    ctx.objs["menu_done"] = False

    while True:
        ctx.objs["menu_msg"] = await print_menu(ctx, ctx.objs["menu_items"], title=ctx.objs["menu_title"])
        listening = [str(i + 1) for i in range(0, len(items))]
        listening.append("c")
        result = await ctx.listen_for(listening, timeout=60)

        if result is None:
            await ctx.bot.edit_message(ctx.objs["menu_msg"], "Menu timed out, aborting.")
            return False

        try:
            await ctx.bot.delete_message(result)
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass

        result = result.content

        if result == "c":
            await ctx.bot.edit_message(ctx.objs["menu_msg"], "User cancelled, aborting.")
            return False

        try:
            await ctx.objs["menu_items"][int(result) - 1][1](ctx)
        except TimedOutError:
            await ctx.bot.edit_message(ctx.objs["menu_msg"], "Menu timed out, aborting.")
            return False

        if ctx.objs["menu_done"]:
            return True

        if on_redraw:
            await on_redraw(ctx)


async def update_preview(ctx):
    try:
        await ctx.bot.edit_message(ctx.objs["embed_preview_msg"], embed=ctx.objs["embed_embed"])
    except discord.HTTPException:
        await ctx.reply("The embed contains errors and cannot be updated!")


async def wait_for_string(ctx, max_len, check=None):
    invalid = True
    to_delete = []
    to_return = None

    while invalid:
        output = await ctx.bot.wait_for_message(author=ctx.author, timeout=600, channel=ctx.ch)
        to_delete.append(output)
        if output is None:
            break

        if output.content != "c":
            if check is not None:
                err = check(ctx, output.content)
                if err:
                    to_delete.append(await ctx.reply(err))
                    continue
            if len(output.content) > max_len:
                to_delete.append(await ctx.reply("This is too long! Please try again."))
                continue
            else:
                invalid = False
                to_return = output.content
        else:
            invalid = False

    for msg in to_delete:
        try:
            await ctx.bot.delete_message(msg)
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass

    if invalid:
        raise TimedOutError()
    return to_return


async def set_title(ctx):
    new_msg = "Please enter the title! (Max 256 characters, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu_msg"], new_msg)

    output = await wait_for_string(ctx, 256)

    if output is not None:
        ctx.objs["embed_embed"].title = output


async def set_description(ctx):
    new_msg = "Please enter the description! (Type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu_msg"], new_msg)

    output = await wait_for_string(ctx, 2048)

    if output is not None:
        ctx.objs["embed_embed"].description = output


async def set_url(ctx):
    new_msg = "Please enter the url! (Must be a valid url, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu_msg"], new_msg)

    output = await wait_for_string(ctx, 2000)

    if output is not None:
        ctx.objs["embed_embed"].url = output


async def set_footer(ctx):
    new_msg = "Please enter the footer text! (Type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu_msg"], new_msg)

    output = await wait_for_string(ctx, 2048)

    if output is not None:
        ctx.objs["embed_embed"].set_footer(text=output, icon_url=ctx.objs["embed_embed"].footer.icon_url)


async def set_image(ctx):
    new_msg = "Please enter the embed image url! (Must end with png/gif/jpg, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu_msg"], new_msg)

    new_image = await wait_for_string(ctx, 2048)

    if new_image is not None:
        ctx.objs["embed_embed"].set_image(url=new_image)


async def set_author(ctx):
    new_msg = "Please enter the author name! (Max 256 characters, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu_msg"], new_msg)

    new_author = await wait_for_string(ctx, 256)

    if new_author is not None:
        ctx.objs["embed_embed"].set_author(name=new_author, url=ctx.objs["embed_embed"].author.url, icon_url=ctx.objs["embed_embed"].author.icon_url)


def colour_check(ctx, user_str):
    if user_str.lower() in discordColours:
        return None
    user_str = user_str.strip("#")
    if not len(user_str) == 6 or not all(c in string.hexdigits for c in user_str):
        return "Colour not recognised!"


async def set_colour(ctx):
    new_msg = "Please enter a colour! (Either a valid hex code or a named colour, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu_msg"], new_msg)

    output = await wait_for_string(ctx, 20, check=colour_check)

    if output is not None:
        if output.lower() in discordColours:
            colour = discordColours[output.lower()]
        else:
            colour = discord.Colour(int(output.strip("#"), 16))

        ctx.objs["embed_embed"].colour = colour


async def close_menu(ctx):
    await ctx.bot.delete_message(ctx.objs["menu_msg"])
    ctx.objs["menu_done"] = True


async def go_up(ctx):
    ctx.objs["menu_done"] = True


async def init_embed(ctx):
    embed = discord.Embed()
    embed.colour = discord.Colour(int("33353c", 16))
    ctx.objs["embed_preview_msg"] = await ctx.reply("Preview:", embed=embed)
    ctx.objs["embed_embed"] = embed


async def add_field(ctx):
    pass


async def remove_field(ctx):
    pass


async def edit_field(ctx):
    pass


def submenu(func):
    async def wrapper(ctx):
        items = ctx.objs["menu_items"]
        title = ctx.objs["menu_title"]
        await func(ctx)
        ctx.objs["menu_items"] = items
        ctx.objs["menu_title"] = title
        ctx.objs["menu_done"] = False
    return wrapper


menu_title = "Please select an action, or type cancel"

field_menu = [("Add Field", add_field),
              ("Remove Field", remove_field),
              ("Edit Field", edit_field),
              ("Back to main menu", go_up)]


@submenu
async def field_edit(ctx):
    await run_menu(ctx, field_menu, message=ctx.objs["menu_msg"], title=menu_title, on_redraw=update_preview)

base_menu = [("Set Title", set_title),
             ("Set Description", set_description),
             ("Set URL", set_url),
             ("Set Colour", set_colour),
             ("Set Footer", set_footer),
             ("Set Image", set_image),
#                 "Set Thumbnail",
             ("Set Author", set_author),
             ("Modify fields", field_edit),
             ("Save and exit", close_menu)
             ]


@cmds.cmd("buildembed",
          category="Utility",
          short_help="Interactively build an embed to be retrieved later",
          aliases=["newembed"])
@cmds.require("in_server")
async def cmd_buildembed(ctx):
    """
    Usage:
        {prefix}buildembed
    Description:
        Interactively creates an embed which may be used elsewhere in the server.
    """
    ctx.objs["embed_preview"] = await init_embed(ctx)

    await run_menu(ctx, base_menu, title=menu_title, on_redraw=update_preview)
