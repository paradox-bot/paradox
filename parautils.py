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

async def tail(filename, n, offset=0):
    p1 = subprocess.Popen('tail -n '+n+offset+' '+filename, shell = True, stdin=None, stdout=subprocess.PIPE)
    lines = p1.communicate().readlines()
    p1.stdout.close()
    return lines[:,-offset]


async def reply(client, message, content):
    await client.send_message(message.channel, content)

#----End Helper functions----


