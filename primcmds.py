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

import datetime
from pytz import timezone
import iso8601

from parautils import para_format, reply, log, LOGFILE, tail
from serverconfig import serv_conf
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
                          .format(message.contentm, message.author.id, permName, error))
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

@prim_cmd("shutdown", "admin")
@require_perm("Master")
async def prim_cmd_shutdown(message, cargs, client, conf, botdata):
    await reply(client, message, "Shutting down, cya another day~")
    await client.logout()


@prim_cmd("restart", "admin",
          "Restart the bot without pulling from git first",
          "Usage: restart\n\nRestarts the bot without pulling from git first")
@require_perm("Manager")
async def prim_cmd_restart(message, cargs, client, conf, botdata):
    await reply(client, message, os.system('./Nanny/scripts/redeploy.sh'))


@prim_cmd("setgame", "admin",
          "Sets my playing status!",
          "Usage: setgame <status>\
          \n\nSets my playing status to <status>. The following keys may be used:\
          \n\t$users$: Number of users I can see.\
          \n\t$servers$: Number of servers I am in.\
          \n\t$channels$: Number of channels I am in.")
@require_perm("Master")
async def prim_cmd_setgame(message, cargs, client, conf, botdata):
    status = await para_format(client, cargs, message)
    await client.change_presence(game=discord.Game(name=status))
    await reply(client, message, "Game changed to: \'{}\'".format(status))


@prim_cmd("masters", "admin",
          "Modify or check the bot masters",
          "Usage: masters [list] | [+/add | -/remove] <userid/mention>\
          \n\nAdds or removes a bot master by id or mention, or lists all current masters.")
@require_perm("Master")
async def prim_cmd_masters(message, cargs, client, conf, botdata):
    masters = conf.getintlist("masters")
    # TODO: Make this a human readable list of names
    masterNames = ', '.join([str(get_member(master)) for master in masters])
    params = cargs.split(' ')
    action = params[0]
    if action in ['', 'list']:
        await reply(client, message, "My masters are:\n{}".format(masterNames))
    elif (action in ['+', 'add']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
        userid = int(params[1].strip('<!@>'))
        if userid in masters:
            await reply(client, message, "This user is already one of my masters!")
        else:
            masters.append(userid)
            conf.set("masters", masters)
            await reply(client, message, "I accept this user as a new master.")
    elif (action in ['-', 'remove']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
        userid = int(params[1].strip('<!@>'))
        if userid not in masters:
            await reply(client, message, "This user is not one of my masters!")
        else:
            masters.remove(userid)
            conf.set("masters", masters)
            await reply(client, message, "I have rejected this master.")
    else:
        await reply(client, message, primCmds["masters"][3])


@prim_cmd("blacklist", "admin",
          "Modify or check the bot blacklist",
          "Usage: blacklist [list] | [+/add | -/remove] <userid/mention>\
          \n\nAdds or removes a blacklisted user by id or mention, or lists all current blacklisted users.")
@require_perm("Master")
async def prim_cmd_blacklist(message, cargs, client, conf, botdata):
    blist = conf.getintlist("blacklisted_users")
    # TODO: Make this a human readable list of names
    blistNames = ', '.join([str(black) for black in blist])
    params = cargs.split(' ')
    action = params[0]
    if action in ['', 'list']:
        await reply(client, message, "I have blacklisted:\n{}".format(blistNames))
    elif (action in ['+', 'add']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
        userid = int(params[1].strip('<!@>'))
        if userid in blist:
            await reply(client, message, "I have already blacklisted this user!")
        else:
            blist.append(userid)
            conf.set("blacklisted_users", blist)
            await reply(client, message,
                        "I call this user a foul wretch and will not deal with them again. Blacklisted the user.")
    elif (action in ['-', 'remove']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
        userid = int(params[1].strip('<!@>'))
        if userid not in blist:
            await reply(client, message, "This user isn't on my blacklist!")
        else:
            blist.remove(userid)
            conf.set("blacklisted_users", blist)
            await reply(client, message, "Give them another chance? If you say so. Unblacklisted the user.")
    else:
        await reply(client, message, primCmds["blacklist"][3])

# TODO: refactor masters to a general list add/check/remove function, add exec config or join commands


@prim_cmd("logs", "admin",
          "Reads and returns the logs",
          "Usage: logs [number]\n\nSends the logfile or the last <number> lines of the log.")
@require_perm("Master")
async def prim_cmd_logs(message, cargs, client, conf, botdata):
    logfile = LOGFILE  # Getting this from utils at the moment
    params = cargs.split(' ')
    if cargs == '':
        await client.send_file(message.channel, logfile)
    elif params[0].isdigit():
        logs = await tail(logfile, params[0])
        await reply(client, message, "Here are your logs:\n```{}```".format(logs))


# Bot exec commands

async def _async(message, cargs, client, conf, botdata):
    if cargs == '':
        return (primCmds['async'][3], 1)
    env = {'message': message,
           'args': cargs,
           'client': client,
           'conf': conf,
           'botdata': botdata,
           'channel': message.channel,
           'author': message.author,
           'server': message.server}
    env.update(globals())
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    exec_string = "async def _temp_exec():\n"
    exec_string += '\n'.join(' ' * 4 + line for line in cargs.split('\n'))
    try:
        exec(exec_string, env)
        result = (redirected_output.getvalue(), 0)
    except Exception:
        traceback.print_exc()
        result = (str(traceback.format_exc()), 2)
    _temp_exec = env['_temp_exec']
    try:
        returnval = await _temp_exec()
        value = redirected_output.getvalue()
        if returnval is None:
            result = (value, 0)
        else:
            result = (value + '\n' + str(returnval), 0)
    except Exception:
        traceback.print_exc()
        result = (str(traceback.format_exc()), 2)
    finally:
        sys.stdout = old_stdout
    return result


@prim_cmd("async", "exec",
          "Executes async code and shows the output",
          "Usage: async <code>\
          \n\nRuns <code> as an asyncronous coroutine and prints the output or error.")
@require_perm("Exec")
async def prim_cmd_async(message, cargs, client, conf, botdata):
    output, error = await _async(message, cargs, client, conf, botdata)
    if error == 1:
        await reply(client, message, output)
    elif error == 2:
        await reply(client, message,
                    "**Async input:**```py\
                    \n{}\n```\
                    \n**Output (error):**```py\
                    \n{}\n```".format(cargs, output))
    else:
        await reply(client, message,
                    "**Async input:**```py\
                    \n{}\n```\
                    \n**Output:**```py\
                    \n{}\n```".format(cargs, output))


async def _exec(message, cargs, client, conf, botdata):
    if cargs == '':
        return (primCmds['exec'][3], 1)
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    try:
        exec(cargs)
        result = (redirected_output.getvalue(), 0)
    except Exception:
        traceback.print_exc()
        result = (str(traceback.format_exc()), 2)
    finally:
        sys.stdout = old_stdout
    return result


@prim_cmd("exec", "exec",
          "Executes code and shows the output",
          "Usage: exec <code>\
          \n\nRuns <code> in current environment using exec() and prints the output or error.")
@require_perm("Exec")
async def prim_cmd_exec(message, cargs, client, conf, botdata):
    output, error = await _exec(message, cargs, client, conf, botdata)
    if error == 1:
        await reply(client, message, output)
    elif error == 2:
        await reply(client, message, "**Exec input:**```py\
                    \n{}\n```\
                    \n**Output (error):**```py\
                    \n{}\n```".format(cargs, output))
    else:
        await reply(client, message, "**Exec input:**```py\
                    \n{}\n```\
                    \n**Output:**```py\
                    \n{}\n```".format(cargs, output))

# -----End Bot manager commands-----


# Config commands

"""
TODO: Make the help look nicer, in fact nicen up all the related strings.
humanise the default value
"""


@prim_cmd("serverconfig", "config",
          "Server configuration",
          "Usage: serverconfig [<category> <option> [value]] | [help <category> <option>] | [show]\
          \n\nIf no arguments are given, lists the available server configuration options.\
          \nIf an option is given, shows the value of the option, and sets it given a <value>.\
          \nserverconfig help <category> <option> shows the description and valid values for that option.\
          \nserverconfig show shows all the server configuration options and their current values.")
async def prim_cmd_serverconfig(message, cargs, client, conf, botdata):
    params = cargs.split(' ')

    if params[0] in ["", "show"]:
        """
        Print all config categories, their options, and descriptions or values in a pretty way.
        """
        msg = "Configuration options:\n```\n"
        for category in sorted(serv_conf):
            msg += "{}:\n".format(category)
            for option in sorted(serv_conf[category]):
                if option == "desc":
                    continue
                msg += "\t{}: {}\n".format(option, serv_conf[category][option].desc if params[0] == ""
                                           else (await serv_conf[category][option].read(botdata, message.server)))
            msg += "\n"
        msg += "```"
        await reply(client, message, msg)
        return
    elif params[0] in ["help"]:
        """
        Prints the description and possible values for the given option.
        """
        if len(params) < 3:
            await reply(client, message,
                        "What option do you want help with? Usage: serverconfig help <category> <option>")
            return
        if params[1] not in serv_conf:
            await reply(client, message,
                        "I don't know this category! Use `serverconfig` to see all categories and options.")
            return
        if params[2] not in serv_conf[params[1]] or params[2] == "desc":
            await reply(client, message,
                        "I can't find this option in the given category! Use `serverconfig` to see all categories and options.")
            return
        cat = params[1]
        op = params[2]
        op_conf = serv_conf[cat][op]
        msg = "Option help: ```\n{}.\nAcceptable input: {}.\nDefault value: {}```"\
            .format(op_conf.desc, op_conf.ctype.accept, op_conf.default)
        await reply(client, message, msg)
    else:
        if len(params) < 2:
            await reply(client, message,
                        "What option do you want to see? See `help serverconfig` for usage.")
            return
        if params[0] not in serv_conf:
            await reply(client, message,
                        "I don't know this category! Use `serverconfig` to see all categories and options.")
            return
        if params[1] not in serv_conf[params[0]] or params[1] == "desc":
            await reply(client, message,
                        "I can't find this option in the given category! Use `serverconfig` to see all categories and options.")
            return
        if len(params) == 2:
            msg = "Current setting is:\n{}".format(await serv_conf[params[0]][params[1]].read(botdata, message.server))
            await reply(client, message, msg)
        else:
            errmsg = await serv_conf[params[0]][params[1]].write(botdata,
                                                                 message.server,
                                                                 ' '.join(params[2:]),
                                                                 message, client)
            if errmsg:
                await reply(client, message, errmsg)
            else:
                await reply(client, message, "The setting was set successfully")


# User config commands
"""
TODO: This is a hacky usersettings, *must* be replaced with something akin to serverconfg.
TODO: Timezone setting type
"""


@prim_cmd("set", "user config",
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
                msg = "You don't appear to have a set timezone! Do `set timezone <timezone>` to set it!"
            await reply(client, message, msg)
            return
        tz = ' '.join(params[1:])
        try:
            timezone(tz)
        except Exception:
            await reply(client, message, "I don't understand this timezone, sorry. More timzeone options will be coming soon!")
            return
        botdata.users.set(message.author.id, "tz", tz)
        await reply(client, message, "Your timezone has been set to `{}`".format(tz))

# User info commands


@prim_cmd("time", "user info",
          "Shows the current time for a user",
          "Usage: time [mention | id | partial name]\
          \n\nGives the time for the mentioned user or yourself\
          \nRequires the user to have set the usersetting \"timezone\".")
async def prim_cmd_time(message, cargs, client, conf, botdata):
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
            await reply(client, message, "You don't have a set timezone! Set it using \"set timezone\"!")
        else:
            await reply(client, message, "This user doesn't have a set timezone. Ask them to set it using \"set timezone\"!")
        return
    try:
        TZ = timezone(tz)
    except Exception:
        await reply(client, message, "Didn't understand the timezone, aborting")
        return
    timestr = 'The current time for {} is `%-I:%M %p (%Z(%z))` on `%a, %d/%m/%Y`'\
        .format(message.server.get_member(user).display_name)
    timestr = iso8601.parse_date(datetime.datetime.now().isoformat()).astimezone(TZ).strftime()
    await reply(client, message, timestr)


@prim_cmd("profile", "user info",
          "Displays a user profile",
          "Usage: profile [mention]\n\nDisplays the mentioned user's profile, or your own.")
@require_perm("master")
async def prim_cmd_profile(message, cargs, client, conf, botdata):
    embed = discord.Embed(type="rich", color=discord.Colour.teal()) \
        .set_author(name="{} ({}) <:testemote:412478719853330432>".format(message.author, message.author.id),
                    icon_url=message.author.avatar_url) \
        .add_field(name="Level",
                   value="()", inline=True) \
        .add_field(name="XP",
                   value="()", inline=True) \
        .add_field(name="Rep",
                   value="()", inline=True) \
        .add_field(name="Premium",
                   value="Yes/No", inline=True) \
        .add_field(name="Created at",
                   value="{}".format(message.author.created_at), inline=False)
    await client.send_message(message.channel, embed=embed)


# General utility commands


@prim_cmd("echo", "general",
          "Sends what you tell me to!",
          "Usage: echo <text>\n\nReplies to the message with <text>")
async def prim_cmd_echo(message, cargs, client, conf, botdata):
    if cargs == "":
        await reply(client, message, "I can't send an empty message!")
    else:
        await reply(client, message, cargs)


@prim_cmd("about", "general",
          "Provides information about the bot",
          "Usage: about\n\nSends a message containing information about the bot.")
async def prim_cmd_about(message, cargs, client, conf, botdata):
    await reply(client, message, 'This is a bot created via the collaborative efforts of Retro, Pue, and Loomy.')


@prim_cmd("invite", "general",
          "Sends the bot's invite link",
          "Usage: invite\
          \n\nSends the link to invite the bot to your server.")
async def prim_cmd_invite(message, cargs, client, conf, userdata):
    await reply(client, message, 'Here\'s my invite link! \n <https://discordapp.com/api/oauth2/authorize?client_id=401613224694251538&permissions=8&scope=bot>')


@prim_cmd("ping", "general",
          "Checks the bot's latency",
          "Usage: ping\
          \n\nChecks the response delay of the bot. Usually used to test whether the bot is responsive or not.")
async def prim_cmd_ping(message, cargs, client, conf, botdata):
    sentMessage = await client.send_message(message.channel, 'Beep')
    mainMsg = sentMessage.timestamp
    editedMessage = await client.edit_message(sentMessage, 'Boop')
    editMsg = editedMessage.edited_timestamp
    latency = editMsg - mainMsg
    latency = latency.microseconds // 1000
    latency = str(latency)
    await client.edit_message(sentMessage, 'Ping: ' + latency + 'ms')


@prim_cmd("support", "general",
          "Sends the link to the bot guild",
          "Usage: support\
          \n\nSends the invite link to the Paradøx support guild.")
async def prim_cmd_support(message, cargs, client, conf, botdata):
    await reply(client, message, 'Join my server here!\n\n<https://discord.gg/ECbUu8u>')


@prim_cmd("help", "general",
          "Provides some detailed help on a command",
          "Usage: help [command name]\
          \n\nShows detailed help on the requested command, or lists all the commands.")
async def prim_cmd_help(message, cargs, client, conf, botdata):
    msg = ""
    if cargs == "":
        msg = "```ini\n [ Available Commands: ]\n"
        for cmd in sorted(primCmds):
            msg += "; {}{}:\t{}\n".format(" " * (12 - len(cmd)), cmd, primCmds[cmd][2])
        msg += "; This bot is a work in progress. If you have any questions, please ask a developer.\n"
        msg += "```"
    else:
        params = cargs.split(' ')
        for cmd in params:
            if cmd in primCmds:
                msg += "```{}```\n".format(primCmds[cmd][3])
            else:
                msg += "I couldn't find a command named `{}`. Please make sure you have spelled the command correctly. \n".format(cmd)
    await reply(client, message, msg)


@prim_cmd("testembed", "testing",
          "Sends a test embed.",
          "Usage: testembed\
          \n\nSends a test embed, what more do you want?")
@require_perm("Exec")
async def prim_cmd_testembed(message, cargs, client, conf, botdata):
    embed = discord.Embed(title="This is a title", color=discord.Colour.teal()) \
        .set_author(name="I am an Author") \
        .add_field(name="This is a field1 title", value="This is field1 content", inline=True) \
        .add_field(name="This is a field2 title", value="This is field2 content", inline=True) \
        .add_field(name="This is a field3 title", value="This is field3 content", inline=False) \
        .set_footer(text="This is a footer")
    await client.send_message(message.channel, embed=embed)


# Misc
"""
TODO: make this threadsafe
"""


@prim_cmd("tex", "Misc",
          "Renders LaTeX code",
          "Usage: tex <code\
          \n\nRenders and displays LaTeX code. Use the reactions to show your code/ edit your code/ delete the message respectively.")
async def prim_cmd_tex(message, cargs, client, conf, botdata):
    texcomp(cargs)
    try:
        await client.delete_message(message)
    except Exception:
        pass
    out_msg = await client.send_file(message.channel, 'tex/out.png', content=message.author.name + ":")
#    edit_emoj = discord.utils.get(client.get_all_emojis(), name='edit')
    del_emoji = discord.utils.get(client.get_all_emojis(), name='delete')
    show_emoji = discord.utils.get(client.get_all_emojis(), name='showtex')
    await client.add_reaction(out_msg, del_emoji)
    await client.add_reaction(out_msg, show_emoji)
    show = False
    while True:
        res = await client.wait_for_reaction(message=out_msg,
                                             timeout=120,
                                             emoji=[del_emoji, show_emoji])
        if res is None:
            break
        res.reaction
        if res.reaction.emoji == del_emoji and res.user == message.author:
            await client.delete_message(out_msg)
            break
        if res.reaction.emoji == show_emoji and (res.user != client.user):
            show = 1 - show
            await client.edit_message(out_msg, message.author.name + ":\n" +
                                      ("```tex\n{}\n```".format(cargs) if show else ""))


def texcomp(tex):
    shutil.copy('tex/preamble.tex', 'tex/out.tex')
    work = open('tex/out.tex', 'a')
    work.write(tex)
    work.write('\n' + '\\end{document}' + '\n')
    work.close()
    os.system('tex/texcompile.sh out')


# ------END COMMANDS------
