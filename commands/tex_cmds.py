import shutil
import discord

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
    error = await texcomp(ctx)
    err_msg = ""
    if error != "":
        err_msg = "\nCompile error! Output:\n```\n{}\n```".format(error)

    await ctx.del_src()
    out_msg = await ctx.reply(file_name='tex/{}.png'.format(ctx.authid), message=ctx.author.name + ":" + err_msg)

    del_emoji = ctx.bot.objects["emoji_tex_del"]
    show_emoji = ctx.bot.objects["emoji_tex_show"]
    show = 0

    def check(reaction, user):
        return ((reaction.emoji == del_emoji) or (reaction.emoji == show_emoji)) and (not (user == ctx.me))
    try:
        await ctx.bot.add_reaction(out_msg, del_emoji)
        await ctx.bot.add_reaction(out_msg, show_emoji)
    except discord.Forbidden:
        return
    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                              timeout=300,
                                              check=check)
        if res is None:
            break
        if res.reaction.emoji == del_emoji and res.user == ctx.author:
            await ctx.bot.delete_message(out_msg)
            return
        if res.reaction.emoji == show_emoji and (res.user != ctx.me):
            try:
                await ctx.bot.remove_reaction(out_msg, show_emoji, res.user)
            except discord.Forbidden:
                pass
            show = 1 - show
            await ctx.bot.edit_message(out_msg, ctx.author.name + ":\n" +
                                       ("```tex\n{}\n```".format(ctx.arg_str) if show else ""))
    try:
        await ctx.bot.remove_reaction(out_msg, del_emoji, ctx.me)
        await ctx.bot.remove_reaction(out_msg, show_emoji, ctx.me)
        await ctx.bot.clear_reactions(out_msg)
    except discord.Forbidden:
        pass


async def texcomp(ctx):
    fn = "tex/{}.tex".format(ctx.authid)
    shutil.copy('tex/preamble.tex', fn)
    with open(fn, 'a') as work:
        work.write(ctx.arg_str)
        work.write('\n' + '\\end{document}' + '\n')
        work.close()
    return await ctx.run_sh("tex/texcompile.sh "+ctx.authid)
