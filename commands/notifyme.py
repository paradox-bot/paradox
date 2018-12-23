from paraCH import paraCH
from commands.mod_cmds import request_reason as rrequest
import discord
from datetime import datetime

cmds = paraCH()


@cmds.cmd("notifyme",
          category="Utility",
          short_help="Sends a DM when a message matching certain criteria are detected.",
          aliases=["pounce"])
@cmds.execute("flags", flags=[])
async def cmd_notifyme(ctx):
    """
    Usage:
        {prefix}notifyme
        {prefix}notifyme [conditions]
        {prefix}notifyme --remove
    Description:
        Notifyme sends you a direct message whenever messages matching your criteria are detected.
        On its own, displays a list of current conditions.
        See Examples for examples of conditions.
        (WIP command, more soon)
    Flags:3
        --remove:: Displays a menu where you can select a check to remove.
        --delay:: Adds a smart delay to 
    """

async def register_notifyme_listeners(bot):
    bot.objects["notifyme_listeners"] = {}

