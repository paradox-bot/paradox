from paraCH import paraCH
import discord

cmds = paraCH()


@cmds.cmd("config",
          category="Server setup",
          short_help="Server configuration")
async def cmd_config(ctx):
    """
    Usage: {prefix}config | config help | config <option> [value]

    Lists your current server configuration, shows option help, or sets an option.
    For example, "config join_ch #general" could be used to set your join message channel.
    """
    serv_conf = ctx.server_conf.settings
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
                cat_msg += "`​{}{}`:\t {}\n".format(" " * (12 - len(serv_conf[option].vis_name)),
                                                    serv_conf[option].vis_name, option_line)
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
            await serv_conf[ctx.params[0]].hr_set(' '.join(ctx.params[1:]))
            if not ctx.cmd_err:
                await ctx.reply("The setting was set successfully")
