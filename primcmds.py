'''
    Provides primitive commands.
    Effectively a way of adding functionality while building the full framework.
'''

import discord
import asyncio
import json

from parautils import *

#----Primitive Commands setup----
'''
This is for adding basic commands as a proof of concept.
Not intended to be used in production.
'''

#Initialise command dict
##Entries are indexed by cmdName and contain data described in prim_cmd
primCmds = {}

#Command decorator
def prim_cmd(cmdName, category, desc = "No description", helpDesc = "No help has yet been written for this command."):
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


#----End primitive commands setup---



#------COMMANDS------

#Primitive Commands

@prim_cmd("about", "general")
async def prim_cmd_about(message, args, client, conf, userdata):
    await reply(client, message, 'This is a bot created via the collaborative efforts of Retro, Pue, and Loomy.')

@prim_cmd("ping", "general")
async def prim_cmd_ping(message, args, client, conf, userdata):
    sentMessage = await client.send_message(message.channel, 'Beep')
    mainMsg = sentMessage.timestamp
    editedMessage = await client.edit_message(sentMessage,'Boop')
    editMsg = editedMessage.edited_timestamp
    latency = editMsg - mainMsg
    latency = latency.microseconds // 1000
    latency = str(latency)
    await client.edit_message(sentMessage, 'Ping: '+latency+'ms')

@prim_cmd("list", "general")
async def prim_cmd_list(message, args, client, conf, userdata):
   await client.send_message(message.channel, 'Available commands: `about`, `ping`')

@prim_cmd("help", "general", "Provides some detailed help on a command", "Usage: help [command name]\n\nShows detailed help on the requested command, or lists all the commands.")
async def prim_cmd_help(message, args, client, conf, userdata):
    msg = ""
    if args == "":
        msg = "```Available Commands:\n"
        for cmd in sorted(primCmds):
            msg += "\t{}:\t {}\n".format(cmd, primCmds[cmd][2])
        msg += "This bot is a work in progress. If you have any questions, please ask a developer.\n"
        msg += "```"
    else:
        params = args.split(' ')
        for cmd in params:
            if cmd in primCmds:
                msg += "```{}```\n".format(primCmds[cmd][3])
            else:
                msg += "```Command '{}' not found. Use help or list to see available commands.```\n".format(cmd)
    await reply(client, message, msg)

#------END COMMANDS------

