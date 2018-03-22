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


@prim_cmd("set", "User info",
          "Shows or sets a user setting",
          "Usage: set [settingname [value]] \
          \n\nSets <settingname> to <value>, shows the value of <settingname>, or lists your available settings.\
          \nTemporary implementation, more is coming soon!")
async def prim_cmd_set(message, cargs, client, conf, botdata):
    if cargs == '':
        await reply(client, message,
                    "```timezone: Country/City, some short-hands are accepted, use ETC/+10 etc to set to GMT-10.```")
        return
    params = cargs.split(' ')
    action = params[0]
    if action == "timezone":
        if len(params) == 1:
            tz = botdata.users.get(message.author.id, "tz")
            if tz:
                msg = "Your current timezone is `{}`".format(tz)
            else:
                msg = "You haven't set your timezone! Use `~set timezone <timezone>` to set it!"
            await reply(client, message, msg)
            return
        tz = ' '.join(params[1:])
        try:
            timezone(tz)
        except Exception:
            await reply(client, message, "Unfortunately, I don't understand this timezone. More options will be available soon.")
            return
        botdata.users.set(message.author.id, "tz", tz)
        await reply(client, message, "Your timezone has been set to `{}`".format(tz))

# User info commands


@prim_cmd("time", "User info",
          "Shows the current time for a user",
          "Usage: time [mention | id | partial name]\
          \n\nGives the time for the mentioned user or yourself\
          \nRequires the user to have set the usersetting \"timezone\".")
async def prim_cmd_time(message, cargs, client, conf, botdata):
    prefix = serv_conf["prefix"].get(botdata, message.server)
    prefix = prefix if prefix else conf.get("prefix")
    user = message.author.id
    if cargs != "":
        user = cargs.strip('<@!> ')
        if not user.isdigit():
            member = discord.utils.find(lambda mem: ((cargs.lower() in mem.display_name.lower()) or (cargs.lower() in mem.name.lower())), message.server.members)
            if member is None:
                await reply(client, message, "Couldn't find this user!")
                return
            user = member.id
    tz = botdata.users.get(user, "tz")
    if not tz:
        if user == message.author.id:
            await reply(client, message, "You haven't set your timezone! Set it using \"{}set timezone <timezone>\"!".format(prefix))
        else:
            await reply(client, message, "This user hasn't set their timezone. Ask them to set it using \"{}set timezone <timezone>\"!".format(prefix))
        return
    try:
        TZ = timezone(tz)
    except Exception:
        await reply(client, message, "An invalid timezone was provided in the JSON file. Aborting... \n **Error Code:** `ERR_OBSTRUCTED_JSON`")
        return
    timestr = 'The current time for **{}** is **%-I:%M %p (%Z(%z))** on **%a, %d/%m/%Y**'\
        .format(message.server.get_member(user).display_name)
    timestr = iso8601.parse_date(datetime.datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
    await reply(client, message, timestr)


@prim_cmd("profile", "User info",
          "Displays a user profile",
          "Usage: profile [mention]\n\nDisplays the mentioned user's profile, or your own.")
async def prim_cmd_profile(message, cargs, client, conf, botdata):
    if cargs != "":
        user = await find_user(client, cargs, message.server, in_server=True)
        if user is None:
            await reply(client, message, "Could not find this user in the server!")
            return
    else:
        user = message.author
    badge_dict = {"master": "botowner",
                  "manager": "botmanager"}
    badges = ""
    for badge in badge_dict:
        (code, msg)= await permFuncs[badge][0](client, botdata, user=user, conf=conf)
        if code == 0:
            badge_emoj = discord.utils.get(client.get_all_emojis(), name=badge_dict[badge])
            if badge_emoj is not None:
                badges += str(badge_emoj) + " "

    created_ago = strfdelta(datetime.datetime.utcnow()-user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    rep = botdata.users.get(user.id, "rep")
    embed = discord.Embed(type="rich", color=user.colour) \
        .set_author(name="{user} ({user.id})".format(user=user),
                    icon_url=user.avatar_url)
    if badges:
        embed.add_field(name="Badges", value=badges, inline=False)

    embed.add_field(name="Level",
                   value="(Coming Soon!)", inline=True) \
        .add_field(name="XP",
                   value="(Coming Soon!)", inline=True) \
        .add_field(name="Reputation",
                   value=rep, inline=True) \
        .add_field(name="Premium",
                   value="No", inline=True)
    tz = botdata.users.get(user.id, "tz")
    if tz:
        try:
            TZ = timezone(tz)
        except Exception:
            await reply(client, message, "An invalid timezone was provided in the database. Aborting... \n **Error Code:** `ERR_CORRUPTED_DB`")
            return
        timestr = '%-I:%M %p on %a, %d/%m/%Y'
        timestr = iso8601.parse_date(datetime.datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
        embed.add_field(name="Current Time", value="{}".format(timestr), inline=False)
    embed.add_field(name="Created at",
                   value="{} ({} ago)".format(created, created_ago), inline=False)
    await client.send_message(message.channel, embed=embed)


# General utility commands

# ------END COMMANDS------
