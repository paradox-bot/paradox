from paraCH import paraCH
import discord

cmds = paraCH()


@cmds.cmd("config",
          category="Server setup",
          short_help="Server configuration")
@cmds.require("in_server")
async def cmd_config(ctx):
    """
    Usage: {prefix}config | config help | config <option> [value]

    Lists your current server configuration, shows option help, or sets an option.
    For example, "config join_ch #general" could be used to set your join message channel.
    """
    server_conf = ctx.server_conf.settings
    serv_conf = {}
    for setting in server_conf:
        serv_conf[server_conf[setting].vis_name] = server_conf[setting]
    if (ctx.params[0] in ["", "help"]) and len(ctx.params) == 1:
        """
        Print all config categories, their options, and descriptions or values in a pretty way.
        """
        sorted_cats = ctx.bot.objects["sorted_conf_cats"]
        cats = {}
        for option in sorted(serv_conf):
            cat = serv_conf[option].category
            if cat not in cats:
                cats[cat] = []
            if (cat not in sorted_cats) and (cat != "Hidden"):
                sorted_cats.append(cat)
            cats[cat].append(option)
        embed = discord.Embed(title="Configuration options:", color=discord.Colour.teal())
        for cat in sorted_cats:
            cat_msg = ""
            for option in cats[cat]:
                if ctx.params[0] == "":
                    option_line = await serv_conf[option].hr_get(ctx)
                else:
                    option_line = serv_conf[option].desc
                cat_msg += "`​{}{}`:\t {}\n".format(" " * (12 - len(option)),
                                                    option, option_line)
            cat_msg += "\n"
            embed.add_field(name=cat, value=cat_msg, inline=False)
        embed.set_footer(text="Use config <option> [value] to see or set an option.")
        await ctx.reply(embed=embed)
        return
    elif (ctx.params[0] == "help") and len(ctx.params) > 1:
        """
        Prints the description and possible values for the given option.
        """
        if ctx.params[1] not in serv_conf:
            await ctx.reply("Unrecognised option! See `serverconfig help` for all options.")
            return
        op = ctx.params[1]
        op_conf = serv_conf[op]
        msg = "Option help: ```\n{}.\nAcceptable input: {}.\nDefault value: {}```"\
            .format(op_conf.desc, op_conf.accept, await op_conf.dyn_default(ctx))
        await ctx.reply(msg)
    else:
        if ctx.params[0] not in serv_conf:
            await ctx.reply("Unrecognised option! See `serverconfig help` for all options.")
            return
        if len(ctx.params) == 1:
            op = ctx.params[0]
            op_conf = serv_conf[op]
            msg = "Option help: ```\n{}.\nAcceptable input: {}.\nDefault value: {}```"\
                .format(op_conf.desc, op_conf.accept, await op_conf.dyn_default(ctx))
            msg += "Currently set to: {}".format(await op_conf.hr_get(ctx))
            await ctx.reply(msg)
        else:
            await serv_conf[ctx.params[0]].hr_set(ctx, ' '.join(ctx.params[1:]))
            if not ctx.cmd_err[0]:
                await ctx.reply("The setting was set successfully")


@cmds.cmd("rmrole",
          category="Server setup",
          short_help="Deletes a role")
@cmds.require("has_manage_server")
async def cmd_rmrole(ctx):
    """
    Usage: {prefix}rmrole <rolename>

    Deletes a role given by partial name or mention.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a role to delete!")
        return
    # TODO: Letting find_role handle all input and output for finding.
    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return
    result = await ctx.ask("Are you sure you want to delete the role `{}`?".format(role.name))
    if result is None:
        await ctx.reply("Question timed out, aborting")
        return
    if result == 0:
        await ctx.reply("Aborting!")
        return
    try:
        await ctx.bot.delete_role(ctx.server, role)
    except discord.Forbidden:
        await ctx.reply("Sorry, it seems I don't have permissions to delete that role!")
        return
    except Exception:
        await ctx.reply("Sorry, I am not able to delete that role!")
        return
    await ctx.reply("Successfully deleted the role!")
