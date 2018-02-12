import discord
import asyncio
import json
import traceback

from botdata import BotData
from botconf import Conf
from parautils import *
from serverconfig import serv_conf

import primcmds

#Global constants/ environment variables

CONF_FILE = "paradox.conf"
#USER_CONF_FILE = "paradox_userdata.conf"
BOT_DATA_FILE = "paradox_botdata.conf"


#Initialise

conf = Conf(CONF_FILE)
#userdata = UserConf(USER_CONF_FILE)
botdata = BotData(BOT_DATA_FILE)

TOKEN = conf.get("TOKEN")
PREFIX = conf.get("PREFIX")

client = discord.Client()





#----Discord event handling----

@client.event
async def on_ready():
    GAME = conf.getStr("GAME")
    if GAME == "":
        GAME = "in $servers$ servers!"
    GAME = await para_format(client, GAME)
    await client.change_presence(status=discord.Status.online, game=discord.Game(name=GAME))
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("Logged into", len(client.servers), "servers")



#We saw a message!
@client.event
async def on_message(message):
    '''
    Have a look at the message and decide if it is appropriate to do something with.
    If it looks like a message for us, and it's not from anyone bad,
    pass it on to the command parser.
    '''
    PREFIX = conf.get("PREFIX") #In case someone changed it while we weren't looking
    if not (message.content.startswith(PREFIX) or (message.content.split(' ')[0].strip('<!@>') == client.user.id)):
        #Okay, it probably wasn't meant for us, or they can't type
        #Either way, let's ignore them
        return
    if message.content == (PREFIX):
        #Some ass just typed the prefix to try and trigger us.
        #Not even going to try parsing, just quit.
        return
    if message.author.bot:
        return
    if int(message.author.id) in conf.getintlist("blacklisted_users"):
        return

    #Okay, we have decided it was meant for us. Let's log it
    await log("Got the command \n{}\nfrom \"{}\" with id \"{}\" ".format(
        message.content, message.author, message.author.id)
        )
    #Now strip the prefix, we don't need that anymore, and extract command
    if message.content.startswith(PREFIX):
        cmd_message = message.content[len(PREFIX):]
    else:
        cmd_message = message.content[len(message.content.split(' ')[0]):]
    cmd = cmd_message.strip().split(' ')[0].lower()
    args = ' '.join(cmd_message.strip().split(' ')[1:])
    await cmd_parser(message, cmd, args)
    return

@client.event
async def on_member_join(member):
    server = member.server
    if not serv_conf["join"]["enabled"].get(botdata, server):
        return
    join_channel = serv_conf["join"]["channel"].get(botdata, server)
    join_message = serv_conf["join"]["msg"].get(botdata, server)
    if join_channel == 0:
        return
    channel = server.get_channel(join_channel)
    if not channel:
        return
    msg = await para_format(client, join_message, member=member)
    await client.send_message(channel, msg)



@client.event
async def on_member_remove(member):
    server = member.server
    if not serv_conf["leave"]["enabled"].get(botdata, server):
        return
    channel = serv_conf["leave"]["channel"].get(botdata, server)
    message = serv_conf["leave"]["msg"].get(botdata, server)
    if channel == 0:
        return
    channel = server.get_channel(channel)
    if not channel:
        return
    msg = await para_format(client, message, member=member)
    await client.send_message(channel, msg)

@client.event
async def on_server_join(server):
    pass




#----End Discord event handling----


#----Meta stuff to handle stuff----

#The command parser, where we activate the appropriate command
async def cmd_parser(message, cmd, args):
    '''
    Parses the command and does the right stuff
        message: The original message with the command. Here mostly for context.
        cmd: The extracted command, that's what we want to look at
        args: The arguments given to the command by the user
    '''
    #For now just have primitive command parsing, see above
    if cmd in primcmds.primCmds:
        try:
            #Try running the command using the associated function,
            ##we don't trust this will actually work though.
            await primcmds.primCmds[cmd][0](message, args, client, conf, botdata)
            return
        except:
            #If it didn't work, print the stacktrace, and try to inform the user.
            #TODO: Log the stacktrace using log()
            traceback.print_exc()
            #Note something unexpected happened so we may not be able to inform the user.
            ##Maybe discord broke!
            ##Or more likely there's a permission error
            try:
                await reply(client, message, "Something went wrong. The error has been logged")

            except:
                await log("Something unexpected happened and I can't print the error. Dying now.")
            #Either way, we are done here.
            return
    else:
        #At this point we have tried all our command types.
        ##The user probably made a spelling mistake.
        return

#----End Meta stuff----




#----Event loops----
#----End event loops----


#----Everything is defined, start the client!----
client.run(conf.get("TOKEN"))
