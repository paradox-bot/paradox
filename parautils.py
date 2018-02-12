'''
    Various helper utility functions for commands
'''

import discord
import asyncio
import json
import os
import subprocess


LOGFILE = "paralog.log"
#Logfile should really not be defined here. Logging should probably be done in a class or something.
#Discord.py v1 will have its own logging anyway.

#----Helper functions and routines----
async def log(logMessage):
    '''
    Logs logMessage in some nice way.
    '''
    #TODO: Some nicer logging, timestamps, a little bit of context
    #For now just print it.
    print(logMessage)
    with open(LOGFILE, 'a+') as logfile:
        logfile.write("\n"+logMessage+"\n")
    return

async def tail(filename, n):
    p1 = subprocess.Popen('tail -n '+str(n)+' '+filename, shell = True, stdin=None, stdout=subprocess.PIPE)
    out,err = p1.communicate()
    p1.stdout.close()
    return out.decode('utf-8')


async def reply(client, message, content):
    await client.send_message(message.channel, content)


async def para_format(client, string, message=None, server=None, member=None, user=None):
    if member:
        user = member
    keydict = { "$servers$" : str(len(client.servers)),
                "$users$" : str(len(list(client.get_all_members()))),
                "$channels$" : str(len(list(client.get_all_channels()))),
                "$username$" : user.name if user else "",
                "$mention$" : user.mention if user else "",
                "$id$" : user.id if user else "",
                "$tag$" : str(user) if user else "",
                "$displayname$" : user.display_name if user else "",
                "$server$" : server.name if server else ""
               }
    for key in keydict:
        string = string.replace(key, keydict[key])
    return string


#----End Helper functions----


