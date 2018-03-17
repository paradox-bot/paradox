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
    try:
        await client.delete_message(message)
    except Exception:
        pass
    out_msg = await client.send_file(message.channel, 'tex/out.png', content=message.author.name + ":")
#    edit_emoj = discord.utils.get(client.get_all_emojis(), name='edit')
    del_emoji = ctx.bot.objects["emoji_tex_del"]
    show_emoji = ctx.bot.objects["emoji_tex_show"]
    await client.add_reaction(out_msg, del_emoji)
    await client.add_reaction(out_msg, show_emoji)
    show = False
    while True:
        res = await client.wait_for_reaction(message=out_msg,
                                             timeout=120,
                                             emoji=[del_emoji, show_emoji])
        if res is None:
            break
        res.reaction
        if res.reaction.emoji == del_emoji and res.user == message.author:
            await client.delete_message(out_msg)
            break
        if res.reaction.emoji == show_emoji and (res.user != client.user):
            show = 1 - show
            await client.edit_message(out_msg, message.author.name + ":\n" +
                                      ("```tex\n{}\n```".format(cargs) if show else ""))


def texcomp(tex):
    shutil.copy('tex/preamble.tex', 'tex/out.tex')
    work = open('tex/out.tex', 'a')
    work.write(tex)
    work.write('\n' + '\\end{document}' + '\n')
    work.close()
    os.system('tex/texcompile.sh out')
