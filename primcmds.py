'''
    Provides primitive commands.
    Effectively a way of adding functionality while building the full framework.
'''

import discord
import asyncio
import json
import os

from parautils import *

#----Primitive Commands setup----
'''
This is for adding basic commands as a proof of concept.
Not intended to be used in production.
'''

#Define permission dictionary
permFuncs = {}

async def perm_default(message, args, client, conf, userdata):
    await reply(client, message, "Sorry, you don't have the required permission. In fact, the required permission isn't defined yet!")
    return 1

def require_perm(permName):
    permFunc = permFuncs[permName] if permName in permFuncs else perm_default
    def perm_decorator(func):
        async def permed_func(message, args, client, conf, userdata, *args, **kwargs):
            error = await permFunc(message, args, client, conf, userdata)
            if error == 0:
                func(args, kwargs)
            else:
                log("Permission failure running command in message \n{}\nFrom user \n{}\nRequired permission \"{}\" which returned error code \"{}\"".format(message.content, message.author.id, permName, error))
            return
        return permed_func
    return perm_decorator

def perm_func(permName):
    def decorator(func):
        permFuncs[permName] = [func]
        return func
    return decorator

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
#------PERMISSION FUNCTIONS------

@perm_func("Exec perms")
async def perm_exec(message, args, client, conf, userdata):
    if int(message.author.id) not in conf.kgetintlist("execWhiteList"):
        await reply(message, "You don't have the require Exec perms to use this command.")
        return 1
    return 0

#----End permission functions----


#------COMMANDS------

#Primitive Commands

@prim_cmd("restart", "general")
@require_perm("Exec perms")
async def prim_cmd_restart(message, args, client, conf, userdata):
    await reply(client, message, os.system('./run.sh'))

@prim_cmd("prestart", "general")
@require_perm("Exec perms")
async def prim_cmd_prestart(message, args, client, conf, userdata):
    await reply(client, message, os.system('./pullrun.sh'))

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
        msg = "```prolog\nAvailable Commands:\n"
        for cmd in sorted(primCmds):
            msg += "{}{}:\t{}\n".format(" "*(12-len(cmd)), cmd, primCmds[cmd][2])
        msg += "This bot is a work in progress. If you have any questions, please ask a developer.\n"
        msg += "```"
    else:
        params = args.split(' ')
        for cmd in params:
            if cmd in primCmds:
                msg += "```{}```\n".format(primCmds[cmd][3])
            else:
                msg += "I couldn't find a command named `{}`. Please make sure you have spelled the command correctly. \n".format(cmd)
    await reply(client, message, msg)

@prim_cmd("testembed", "testing", "Sends a test embed.", "Usage: testembed\n\nSends a test embed, what more do you want?")
@require_perm("Exec perms")
async def prim_cmd_testembed(message,args, client, conf, userdata):
    embed = discord.Embed(title = "This is a title", color = discord.Colour.teal()) \
        .set_author(name = "I am an Author") \
        .add_field(name = "This is a field1 title", value = "This is field1 content", inline = True) \
        .add_field(name = "This is a field2 title", value = "This is field2 content", inline = True) \
        .add_field(name = "This is a field3 title", value = "This is field3 content", inline = False) \
        .set_footer(text = "This is a footer")
    await client.send_message(message.channel, embed=embed)


#------END COMMANDS------

