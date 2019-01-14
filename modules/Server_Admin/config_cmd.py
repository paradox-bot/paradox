from paraCH import paraCH
import discord

cmds = paraCH()
# Provides config


async def _config_pages(ctx, serv_conf, value=True):
    """
    Builds the server configuration pages.
    """
    cats = {}
    pages = []
    sorted_pages = ctx.bot.objects["sorted_conf_pages"]

    for option in sorted(serv_conf):
        cat = serv_conf[option].category
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(option)
    for page in sorted_pages:
        page_name = page[0]
        page_cats = page[1]
        page_embed = discord.Embed(title="{} options:".format(page_name), color=discord.Colour.teal())
        for cat in page_cats:
            if cat not in cats:
                continue
            value_list = []
            for option in cats[cat]:
                value_list.append(await serv_conf[option].hr_get(ctx) if value else serv_conf[option].desc)
            cat_msg = ctx.prop_tabulate(cats[cat], value_list)

            page_embed.add_field(name=cat, value=cat_msg, inline=False)
        page_embed.set_footer(text="Use {}config <option> [value] to see or set an option.".format(ctx.used_prefix))
        pages.append(page_embed)
    return pages


@cmds.cmd("config",
          category="Server Admin",
          short_help="Server configuration")
@cmds.require("in_server")
async def cmd_config(ctx):
    """
    Usage:
        {prefix}config | config help | config <option> [value]
    Description:
        Lists your current server configuration, shows option help, or sets an option.
        For example, "config join_ch #general" could be used to set your join message channel.
    """
    server_conf = ctx.server_conf.settings
    serv_conf = {}
    for setting in server_conf:
        serv_conf[server_conf[setting].vis_name] = server_conf[setting]
    if (ctx.params[0] in ["", "help"]) and len(ctx.params) == 1:
        pages = await _config_pages(ctx, serv_conf, value=True if ctx.params[0] == "" else False)
        await ctx.pager(pages, embed=True)
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
            await ctx.reply("Unrecognised option! See `{0.used_prefix}config help` for all options.".format(ctx))
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
