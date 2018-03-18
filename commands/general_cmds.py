import discord
from ParaCH import ParaCH

cmds = ParaCH()

@cmds.cmd("about",
          category="General",
          short_help="Provides information about the bot")
         # "Usage: about\n\nSends a message containing information about the bot.")
async def cmd_about(ctx):
    devs = ["298706728856453121", "299175087389802496", "225773687037493258"]
    devnames = ', '.join([str(discord.utils.get(ctx.client.get_all_members(), id = str(devs))) for devs in devs])
#    await reply(client, message, 'Paradøx was coded in Discord.py by Pue, Retro, and nockia.')
    embed = discord.Embed(title="About Paradøx", color=discord.Colour.red()) \
        .add_field(name="Info", value="Paradøx is a Discord.py bot coded by {}.".format(devnames), inline=True) \
        .add_field(name="Stats", value="(Soon)", inline=True) \
        .add_field(name="Thanks to", value="(Soon)", inline=False) \
        .add_field(name="Links", value="[Support Server](https://discord.gg/ECbUu8u)", inline=False)
    await ctx.reply(embed=embed)
