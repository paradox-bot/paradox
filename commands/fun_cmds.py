from ParaCH import ParaCH

cmds = ParaCH()

@cmds.cmd("lenny",
          category="Fun stuff",
          short_help="( ͡° ͜ʖ ͡°)")
         # "Usage: lenny\n\nSends lenny ( ͡° ͜ʖ ͡°)")
async def cmd_lenny(ctx):
    await ctx.client.delete_message(ctx.message)
    await ctx.reply('( ͡° ͜ʖ ͡°)')
