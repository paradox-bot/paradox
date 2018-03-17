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
    texcomp(cargs)
    await ctx.del_src()
    out_msg = await ctx.reply(file_name='tex/out.png', content=ctx.author.name + ":")

    del_emoji = ctx.bot.objects["emoji_tex_del"]
    show_emoji = ctx.bot.objects["emoji_tex_show"]
    await client.add_reaction(out_msg, del_emoji)
    await client.add_reaction(out_msg, show_emoji)
    show = False
    while True:
        res = await ctx.client.wait_for_reaction(message=out_msg,
                                             timeout=300,
                                             emoji=[del_emoji, show_emoji])
        if res is None:
            break
        if res.reaction.emoji == del_emoji and res.user == ctx.author:
            await ctx.client.delete_message(out_msg)
            break
        if res.reaction.emoji == show_emoji and (res.user != client.user):
            show = 1 - show
            await client.edit_message(out_msg, ctx.author.name + ":\n" +
                                      ("```tex\n{}\n```".format(ctx.arg_str) if show else ""))
    await client.remove_reaction(out_msg, del_emoji)
    await client.remove_reaction(out_msg, show_emoji)


def texcomp(tex):
    shutil.copy('tex/preamble.tex', 'tex/out.tex')
    work = open('tex/out.tex', 'a')
    work.write(tex)
    work.write('\n' + '\\end{document}' + '\n')
    work.close()
    os.system('tex/texcompile.sh out')
