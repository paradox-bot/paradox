'''
    Various helper utility functions for commands
'''

import asyncio
import subprocess
import discord
import datetime

LOGFILE = "paralog.log"
# Logfile should really not be defined here. Logging should probably be done in a class or something.
# Discord.py v1 will have its own logging anyway.

# ----Helper functions and routines----


async def log(logMessage):
    '''
    Logs logMessage in some nice way.
    '''
    # TODO: Some nicer logging, timestamps, a little bit of context
    # For now just print it.
    print(logMessage)
    with open(LOGFILE, 'a+') as logfile:
        logfile.write("\n" + logMessage + "\n")
    return


async def tail(filename, n):
    p1 = subprocess.Popen('tail -n ' + str(n) + ' ' + filename,
                          shell=True, stdin=None, stdout=subprocess.PIPE)
    out, err = p1.communicate()
    p1.stdout.close()
    return out.decode('utf-8')


async def reply(client, message, content):
    if content == "":
        await client.send_message(message.channel, "Attempted to send an empty message!")
    else:
        await client.send_message(message.channel, content)

async def find_user(client, userstr, server=None, in_server=False):
    if userstr == "":
        return None
    maybe_user_id = userstr.strip('<@!> ')
    if maybe_user_id.isdigit():
        def is_user(member):
            return member.id == maybe_user_id
    else:
        def is_user(member):
            return ((userstr.lower() in member.display_name.lower()) or (userstr.lower() in member.name.lower()))
    if server:
        member = discord.utils.find(is_user, server.members)
    if not (member or in_server):
        member = discord.utils.find(is_user, client.get_all_members)
    return member

def get_prefix(conf, serv_conf, botdata, server):
    prefix_conf = serv_conf["prefix"]
    prefix = conf.get("PREFIX")
    if server:
        prefix = prefix_conf.get(botdata, server)
        prefix = prefix if prefix != prefix_conf.default else conf.get("PREFIX")
    return prefix

async def para_format(client, string, message=None, server=None, member=None, user=None):
    if member:
        user = member
    keydict = {"$servers$": str(len(client.servers)),
               "$users$": str(len(list(client.get_all_members()))),
               "$channels$": str(len(list(client.get_all_channels()))),
               "$username$": user.name if user else "",
               "$mention$": user.mention if user else "",
               "$id$": user.id if user else "",
               "$tag$": str(user) if user else "",
               "$displayname$": user.display_name if user else "",
               "$server$": server.name if server else ""
               }
    for key in keydict:
        string = string.replace(key, keydict[key])
    return string


def strfdelta(delta, sec = False):
    output = [[delta.days, 'day'],
              [delta.seconds // 3600, 'hour'],
              [delta.seconds // 60 % 60, 'minute']]
    if sec:
        output.append([delta.seconds % 60, 'second'])
    for i in range(len(output)):
        if output[i][0] != 1:
            output[i][1] += 's'
    reply_msg = ''
    if output[0][0] != 0:
        reply_msg += "{} {} ".format(output[0][0], output[0][1])
    for i in range(1, len(output)):
        reply_msg += "{} {} ".format(output[i][0], output[i][1])
    reply_msg = reply_msg[:-1]
    return reply_msg

def convdatestring(datestring):
    datestring = datestring.strip(' ,')
    datearray = []
    funcs = {'d' : lambda x: x * 24 * 60 * 60,
             'h' : lambda x: x * 60 * 60,
             'm' : lambda x: x * 60,
             's' : lambda x: x}
    currentnumber = ''
    for char in datestring:
        if char.isdigit():
            currentnumber += char
        else:
            if currentnumber == '':
                continue
            datearray.append((int(currentnumber), char))
            currentnumber = ''
    seconds = 0
    if currentnumber:
        seconds += int(currentnumber)
    for i in datearray:
        if i[1] in funcs:
            seconds += funcs[i[1]](i[0])
    return datetime.timedelta(seconds=seconds)


# ----End Helper functions----
