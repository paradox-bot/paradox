import shutil

from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("tex",
          category="Misc",
          short_help="Renders LaTeX code")
async def cmd_tex(ctx):
    """
    Usage: {prefix}tex <code>

    Renders and displays LaTeX code.
    Use the reactions to show your code/ edit your code/ delete the message respectively.
    """
    await texcomp(ctx)
    await ctx.del_src()
    out_msg = await ctx.reply(file_name='tex/{}.png'.format(ctx.authid), message=ctx.author.name + ":")

    del_emoji = ctx.bot.objects["emoji_tex_del"]
    show_emoji = ctx.bot.objects["emoji_tex_show"]
    await ctx.bot.add_reaction(out_msg, del_emoji)
    await ctx.bot.add_reaction(out_msg, show_emoji)
    show = False
    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                        timeout=300,
                                        emoji=[del_emoji, show_emoji])
        if res is None:
            break
        if res.reaction.emoji == del_emoji and res.user == ctx.author:
            await ctx.bot.delete_message(out_msg)
            break
        if res.reaction.emoji == show_emoji and (res.user != ctx.me):
            show = 1 - show
            await ctx.bot.edit_message(out_msg, ctx.author.name + ":\n" +
                                          ("```tex\n{}\n```".format(ctx.arg_str) if show else ""))
    try:
        await ctx.bot.clear_reactions(out_msg)
    except Exception:
        try:
            await ctx.bot.remove_reaction(out_msg, del_emoji, ctx.me)
            await ctx.bot.remove_reaction(out_msg, show_emoji, ctx.me)
        except Exception:
            pass


async def texcomp(ctx):
    fn = "tex/{}.tex".format(ctx.authid)
    shutil.copy('tex/preamble.tex', fn)
    with open(fn, 'a') as work:
        work.write(ctx.arg_str)
        work.write('\n' + '\\end{document}' + '\n')
        work.close()
    await ctx.run_sh("tex/texcompile.sh "+ctx.authid)
