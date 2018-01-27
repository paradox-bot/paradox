'''
    Various helper utility functions for commands
'''

import discord
import asyncio
import json


#----Helper functions and routines----
async def log(logMessage):
    '''
    Logs logMessage in some nice way.
    '''
    #TODO: Log to file, or something nice.
    #For now just print it.
    print(logMessage)
    return



async def reply(client, message, content):
    await client.send_message(message.channel, content)

#----End Helper functions----


