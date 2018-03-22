'''
    Provides primitive commands.
    Effectively a way of adding functionality while building the full framework.
'''

import discord
import asyncio
import os
import shutil
import sys
import traceback
from io import StringIO
import aiohttp

import datetime
from pytz import timezone
import iso8601

from parautils import para_format, reply, log, LOGFILE, tail, find_user, strfdelta
from serverconfig import serv_conf
from botconfig import bot_conf
from paraperms import permFuncs


# ----Primitive Commands setup----
'''
This is for adding basic commands as a proof of concept.
Not intended to be used in production.
'''


async def perm_default(message, args, client, conf, botdata):
    """
    Perm decorator to require permissions on functions
    """
    await reply(client, message, "Sorry, you don't have the required permission. In fact, the required permission isn't defined yet!")
    return 1


def require_perm(permName):
    permName = permName.lower()
    permFunc = permFuncs[permName][0] if permName in permFuncs else perm_default

    def perm_decorator(func):
        async def permed_func(message, cargs, client, conf, botdata, *args, **kwargs):
            (error, errmsg) = await permFunc(client, botdata, conf=conf, message=message)
            if error == 0:
                await func(message, cargs, client, conf, botdata)
            else:
                await reply(client, message, errmsg)
                await log("Permission failure running command in message \
                          \n{}\nFrom user \n{}\
                          \nRequired permission \"{}\" which returned error code \"{}\""
                          .format(message.content, message.author.id, permName, error))
            return
        return permed_func
    return perm_decorator


# Initialise command dict
# Entries are indexed by cmdName and contain data described in prim_cmd
primCmds = {}


def prim_cmd(cmdName, category, desc="No description", helpDesc="No help has yet been written for this command."):
    '''
    Decorator wrapper which adds the command to the commands dict so it can be looked up and run.
        cmdName -- Name of the command
        category -- string representing the category, if categorised commands are created
            (e.g. for categorised help)
        desc -- user readable short description for the command
        helpDesc -- user readable help string for the command
    Returns the actual decorator below
    '''
    def decorator(func):
        '''
        Takes in the function, adds it to the cmd dictionary, spits it out again.
        '''
        primCmds[cmdName] = [func, category, desc, helpDesc]
        return func
    return decorator

# ----End primitive commands setup---
# ---Helper functions---


# ---End helper functions---


# ------COMMANDS------

# Primitive Commands

# Bot admin commands



# Bot exec commands

# -----End Bot manager commands-----


# Config commands

"""
TODO: Humanise the default value
"""

# User config commands
"""
TODO: This is a hacky usersettings, *must* be replaced with something akin to serverconfg.
TODO: Timezone setting type
"""




# General utility commands

# ------END COMMANDS------
