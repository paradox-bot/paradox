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

@prim_cmd("shutdown", "Bot admin")
@require_perm("Master")
async def prim_cmd_shutdown(message, cargs, client, conf, botdata):
    await reply(client, message, "Shutting down, cya another day~")
    await client.logout()


@prim_cmd("restart", "Bot admin",
          "Restart the bot without pulling from git first",
          "Usage: restart\n\nRestarts the bot without pulling from git first")
@require_perm("Manager")
async def prim_cmd_restart(message, cargs, client, conf, botdata):
    await reply(client, message, os.system('./Nanny/scripts/redeploy.sh'))


@prim_cmd("setgame", "Bot admin",
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


@prim_cmd("masters", "Bot admin",
          "Modify or check the bot masters",
          "Usage: masters [list] | [+/add | -/remove] <userid/mention>\
          \n\nAdds or removes a bot master by id or mention, or lists all current masters.")
@require_perm("Master")
async def prim_cmd_masters(message, cargs, client, conf, botdata):
    masters = await bot_conf["masters"].read(conf, None, message, client)
    params = cargs.split(' ')
    action = params[0]
    if action in ['', 'list']:
        await reply(client, message, "My masters are:\n{}".format(masters))
    else:
        errmsg = await bot_conf["masters"].write(conf, None, cargs, message, client, message.server, botdata)
        await reply(client, message, errmsg)


@prim_cmd("blacklist", "Bot admin",
          "Modify or check the bot blacklist",
          "Usage: blacklist [list] | [+/add | -/remove] <userid/mention>\
          \n\nAdds or removes a blacklisted user by id or mention, or lists all current blacklisted users.")
@require_perm("Master")
async def prim_cmd_blacklist(message, cargs, client, conf, botdata):
    blist = await bot_conf["blacklist"].read(conf, None, message, client)
    params = cargs.split(' ')
    action = params[0]
    if action in ['', 'list']:
        await reply(client, message, "I have blacklisted:\n{}".format(blist))
    else:
        errmsg = await bot_conf["blacklist"].write(conf, None, cargs, message, client, message.server, botdata)
        await reply(client, message, errmsg)


@prim_cmd("logs", "Bot admin",
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


@prim_cmd("async", "Bot admin",
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
                    "**Async input:**\
                    \n```py\n{}\n```\
                    \n**Output (error):** \
                    \n```py\n{}\n```".format(cargs, output))
    else:
        await reply(client, message,
                    "**Async input:**\
                    \n```py\n{}\n```\
                    \n**Output:**\
                    \n```py\n{}\n```".format(cargs, output))


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


@prim_cmd("exec", "Bot admin",
          "Executes code and shows the output",
          "Usage: exec <code>\
          \n\nRuns <code> in current environment using exec() and prints the output or error.")
@require_perm("Exec")
async def prim_cmd_exec(message, cargs, client, conf, botdata):
    output, error = await _exec(message, cargs, client, conf, botdata)
    if error == 1:
        await reply(client, message, output)
    elif error == 2:
        await reply(client, message,
                    "**Exec input:** \
                    \n```py\n{}\n```\
                    \n**Output (error):** \
                    \n```py\n{}\n```".format(cargs, output))
    else:
        await reply(client, message,
                    "**Exec input:**\
                    \n```py\n{}\n```\
                    \n**Output:**\
                    \n```py\n{}\n```".format(cargs, output))

# -----End Bot manager commands-----


# Config commands

"""
TODO: Humanise the default value
"""

@prim_cmd("config", "Server setup",
          "Server configuration",
          "Usage: config | config help | config <option> [value]\
          \n\nLists your current server configuration, shows option help, or sets an option.\
          \nFor example, \"config join_ch #general\" could be used to set your join message channel.")
async def prim_cmd_config(message, cargs, client, conf, botdata):
    params = cargs.split(' ')

    if (params[0] in ["", "help"]) and len(params) == 1:
        """
        Print all config categories, their options, and descriptions or values in a pretty way.
        """
        sorted_cats = ["Guild settings", "Join message", "Leave message"]
        cats = {}
        for option in sorted(serv_conf):
            cat = serv_conf[option].cat
            if cat not in cats:
                cats[cat] = []
            if (cat not in sorted_cats) and (cat != "Hidden"):
                sorted_cats.append(cat)
            cats[cat].append(option)
        embed = discord.Embed(title="Configuration options:", color=discord.Colour.teal())
        for cat in sorted_cats:
            cat_msg = ""
            for option in cats[cat]:
#                if option == "desc":
#                    continue
                if params[0] == "":
                    option_line = await serv_conf[option].read(botdata,
                                                               message.server,
                                                               message=message,
                                                               client=client)
                else:
                    option_line = serv_conf[option].desc
                cat_msg += "`​{}{}`:\t {}\n".format(" " * (12 - len(option)), option, option_line)
            cat_msg += "\n"
            embed.add_field(name=cat, value=cat_msg, inline=False)
        embed.set_footer(text="Use config <option> [value] to see or set an option.")
        await client.send_message(message.channel, embed=embed)
        return
    elif (params[0] == "help") and len(params) > 1:
        """
        Prints the description and possible values for the given option.
        """
        if params[1] not in serv_conf:
            await reply(client, message, "Unrecognised option! See `serverconfig help` for all options.")
            return
        op = params[1]
        op_conf = serv_conf[op]
        msg = "Option help: ```\n{}.\nAcceptable input: {}.\nDefault value: {}```"\
            .format(op_conf.desc, op_conf.ctype.accept, op_conf.default)
        await reply(client, message, msg)
    else:
        if params[0] not in serv_conf:
            await reply(client, message, "Unrecognised option! See `serverconfig help` for all options.")
            return
        if len(params) == 1:
            op = params[0]
            op_conf = serv_conf[op]
            msg = "Option help: ```\n{}.\nAcceptable input: {}.\nDefault value: {}```"\
                .format(op_conf.desc, op_conf.ctype.accept, op_conf.default)
            msg += "Currently set to: {}".format(await op_conf.read(botdata, message.server, message=message, client=client))
            await reply(client, message, msg)
        else:
            errmsg = await serv_conf[params[0]].write(botdata, message.server, ' '.join(params[1:]), message, client)
            if errmsg:
                await reply(client, message, errmsg)
            else:
                await reply(client, message, "The setting was set successfully")


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
    timestr = 'The current time for {} is `%-I:%M %p (%Z(%z))` on `%a, %d/%m/%Y`'\
        .format(message.server.get_member(user).display_name)
    timestr = iso8601.parse_date(datetime.datetime.now().isoformat()).astimezone(TZ).strftime(timestr)
    await reply(client, message, timestr)


@prim_cmd("profile", "User info",
          "Displays a user profile",
          "Usage: profile [mention]\n\nDisplays the mentioned user's profile, or your own.")
@require_perm("master")
async def prim_cmd_profile(message, cargs, client, conf, botdata):
    rep = botdata.users.get(message.author.id, "rep")
    embed = discord.Embed(type="rich", color=discord.Colour.teal()) \
        .set_author(name="{} ({})".format(message.author, message.author.id),
                    icon_url=message.author.avatar_url) \
        .add_field(name="Level",
                   value="()", inline=True) \
        .add_field(name="XP",
                   value="()", inline=True) \
        .add_field(name="Rep",
                   value=rep, inline=True) \
        .add_field(name="Premium",
                   value="Yes/No", inline=True) \
        .add_field(name="Created at",
                   value="{}".format(message.author.created_at), inline=False)
    await client.send_message(message.channel, embed=embed)


# General utility commands


@prim_cmd("echo", "General",
          "Sends what you tell me to!",
          "Usage: echo <text>\n\nReplies to the message with <text>")
async def prim_cmd_echo(message, cargs, client, conf, botdata):
    if cargs == "":
        await reply(client, message, "I can't send an empty message!")
    else:
        await reply(client, message, cargs)


@prim_cmd("about", "General",
          "Provides information about the bot",
          "Usage: about\n\nSends a message containing information about the bot.")
async def prim_cmd_about(message, cargs, client, conf, botdata):
    await reply(client, message, 'Paradøx was coded in Discord.py by Pue, Retro, and nockia.')

@prim_cmd("discrim", "General",
              "Searches for users with a given discrim",
              "Usage: discrim [discriminator]\n\nSearches all guilds the bot is in for a user with the given discriminator.")
async def prim_cmd_discrim(message, cargs, client, conf, botdata):
     p = client.get_all_members()
     found_members = set(filter(lambda m: m.discriminator.endswith(cargs), p))
     if len(found_members) == 0:
         await reply(client, message, "No users with this discrim found!")
         return
     user_info = [ (str(m), "({})".format(m.id)) for m in found_members]
     max_len = len(max(list(zip(*user_info))[0],key=len))
     user_strs = [ "{0[0]:^{max_len}} {0[1]:^25}".format(user, max_len = max_len) for user in user_info]
     await reply(client, message, "```asciidoc\n= Users found =\n{}\n```".format('\n'.join(user_strs)))


@prim_cmd("invite", "General",
          "Sends the bot's invite link",
          "Usage: invite\
          \n\nSends the link to invite the bot to your server.")
async def prim_cmd_invite(message, cargs, client, conf, userdata):
    await reply(client, message, 'Here\'s my invite link! \n <https://discordapp.com/api/oauth2/authorize?client_id=401613224694251538&permissions=8&scope=bot>')

@prim_cmd("lenny", "Fun stuff",
          "( ͡° ͜ʖ ͡°)",
          "Usage: lenny\n\nSends lenny ( ͡° ͜ʖ ͡°)")
async def prim_cmd_lenny(message, cargs, client, conf, botdata):
    await client.delete_message(message)
    await reply(client, message, '( ͡° ͜ʖ ͡°)')

@prim_cmd("rep", "Fun stuff",
          "Give reputation to a user",
          "Usage: rep [mention]\
          \n\nGives a reputation point to the mentioned user or shows your current reputation cooldown timer.")
async def prim_cmd_rep(message, cargs, client, conf, botdata):
    now = datetime.datetime.utcnow()
    last_rep = botdata.users.get(message.author.id, "last_rep_time")
    if cargs == "":
        given_rep = botdata.users.get(message.author.id, "given_rep")
        if given_rep is None:
            given_msg = "You have not yet given any reputation!"
            rep_time_msg = "Start giving reputation using `rep <user>`!"
        if given_rep is not None and last_rep is not None:
            last_rep_time = datetime.datetime.fromtimestamp(int(last_rep))
            given_ago = strfdelta(now - last_rep_time)
            given_msg = "You have given **{}** reputation point{}! You last gave a reputation point {} ago.".format(given_rep, "s" if int(given_rep)>1 else "", given_ago)
            reptime = datetime.timedelta(days = 1) - (now - last_rep_time)
            if reptime.seconds > 0:
                rep_time_msg = "You may give reputation in {}.".format(strfdelta(reptime, sec = True))
            else:
                rep_time_msg = "You may now give reputation!"
        await reply(client, message, "{}\n{}".format(given_msg,rep_time_msg))
    else:
        user = await find_user(client, cargs, message.server, in_server=True)
        if not user:
            await reply(client, message, "I couldn't find that user in this server sorry.")
            return
        if user == message.author:
            await reply(client, message, "You can't give yourself reputation!")
            return
        if user == client.user:
            await reply(client, message, "Aww thanks!")
        elif user.bot:
            await reply(client, message, "Bots don't need reputation points!")
            return
        if last_rep is not None:
            last_rep_time = datetime.datetime.fromtimestamp(int(last_rep))
            reptime = datetime.timedelta(days = 1) - (now - last_rep_time)
            if reptime.seconds > 0:
                msg = "Cool down! You may give reputation in {}.".format(strfdelta(reptime, sec = True))
                await reply(client, message, msg)
                return
        rep = botdata.users.get(user.id, "rep")
        rep = int(rep) + 1 if rep else 1
        botdata.users.set(user.id, "rep", str(rep))
        given_rep = botdata.users.get(message.author.id, "given_rep")
        given_rep = int(given_rep) + 1 if given_rep else 1
        botdata.users.set(message.author.id, "given_rep", str(given_rep))
        botdata.users.set(message.author.id, "last_rep_time", str(now.strftime('%s')))
        await reply(client, message, "You have given a reputation point to {}".format(user.mention))






@prim_cmd("ping", "General",
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

@prim_cmd("userinfo", "User info",
          "Shows the user's information",
          "Usage: userinfo (mention)\n\nSends information on the mentioned user, or yourself if no one is provided.")
@require_perm("in server")
async def prim_cmd_userinfo(message, cargs, client, conf, botdata):
    user = await find_user(client, cargs, message.server, in_server=True)
    user = user if user else message.author
    bot_emoji = discord.utils.get(client.get_all_emojis(), name='parabot')

    embed = discord.Embed(type="rich", color=(user.colour if user.colour.value else discord.Colour.light_grey()))
    embed.set_author(name="{user.name} ({user.id})".format(user=user), icon_url=user.avatar_url, url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name="Full name", value=("{} ".format(bot_emoji) if user.bot else "")+str(user), inline=False)

    game = "Playing {}".format(user.game if user.game else "nothing")
    statusdict = {"offline": "Offline/Invisible",
                  "dnd": "Do Not Disturb",
                  "online": "Online",
                  "idle": "Idle/Away"}
    embed.add_field(name="Status", value="{}, {}".format(statusdict[str(user.status)], game), inline=False)

    embed.add_field(name="Nickname", value=str(user.display_name), inline=False)

    shared = len(list(filter(lambda m: m.id == user.id, client.get_all_members())))
    embed.add_field(name="Shared servers", value=str(shared), inline=False)

    joined_ago = strfdelta(datetime.datetime.utcnow()-user.joined_at)
    joined = user.joined_at.strftime("%-I:%M %p, %d/%m/%Y")
    created_ago = strfdelta(datetime.datetime.utcnow()-user.created_at)
    created = user.created_at.strftime("%-I:%M %p, %d/%m/%Y")
    embed.add_field(name="Joined at", value="{} ({} ago)".format(joined, joined_ago), inline=False)
    embed.add_field(name="Created at", value="{} ({} ago)".format(created, created_ago), inline=False)

    roles = [r.name for r in user.roles if r.name != "@everyone"]
    embed.add_field(name="Roles", value=('`'+ '`, `'.join(roles) + '`'), inline=False)
    await client.send_message(message.channel, embed=embed)

@prim_cmd("support", "General",
          "Sends the link to the bot guild",
          "Usage: support\
          \n\nSends the invite link to the Paradøx support guild.")
async def prim_cmd_support(message, cargs, client, conf, botdata):
    await reply(client, message, 'Join my server here!\n\n<https://discord.gg/ECbUu8u>')

@prim_cmd("list", "General",
          "Lists all my commands!",
          "Usage: list\
          \n\nReplies with an embed containing all my visible commands.")
async def prim_cmd_list(message, cargs, client, conf, botdata):
    sorted_cats = ["General", "Fun stuff", "User info", "Server setup", "Bot admin", "Misc"]
    if cargs == "":
        cats = {}
        for cmd in sorted(primCmds):
            cat = primCmds[cmd][1]
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(cmd)
    embed = discord.Embed(title="Paradøx's commands!", color=discord.Colour.green())
    for cat in sorted_cats:
        embed.add_field(name=cat, value="`{}`".format('`, `'.join(cats[cat])), inline=False)
    embed.set_footer(text="Use ~help or ~help <command> for detailed help or get support with ~support.")
    await client.send_message(message.channel, embed=embed)

@prim_cmd("help", "General",
          "Provides some detailed help on a command",
          "Usage: help [command name]\
          \n\nShows detailed help on the requested command, or lists all the commands.")
async def prim_cmd_help(message, cargs, client, conf, botdata):
    msg = ""
    sorted_cats = ["General", "Fun stuff", "User info", "Server setup", "Bot admin", "Misc"]
    if cargs == "":
        cat_msgs = {}
        for cmd in sorted(primCmds):
            cat = primCmds[cmd][1]
            if cat not in cat_msgs or not cat_msgs[cat]:
                cat_msgs[cat] = "```ini\n [ {}: ]\n".format(cat)
            cat_msgs[cat] += "; {}{}:\t{}\n".format(" " * (12 - len(cmd)), cmd, primCmds[cmd][2])
        for cat in sorted_cats:
            cat_msgs[cat] += "```"
            msg += cat_msgs[cat]
        await client.send_message(message.author, msg)
        await reply(client, message, "I have messaged you a detailed listing of my commands! Use `list` to obtain a more succinct listing.")
        return
    else:
        params = cargs.split(' ')
        for cmd in params:
            if cmd in primCmds:
                msg += "```{}```\n".format(primCmds[cmd][3])
            else:
                msg += "I couldn't find a command named `{}`. Please make sure you have spelled the command correctly. \n".format(cmd)
    await reply(client, message, msg)


@prim_cmd("binasc", "Fun stuff",
          "Converts binary to ascii",
          "Usage: binasc <binary string>")
async def prim_cmd_binasc(message, cargs, client, conf, botdata):
    bitstr = cargs.replace(' ', '')
    if (not bitstr.isdigit()) or (len(bitstr) % 8 != 0):
        await reply(client, message, "Not a valid binary string!")
        return
    bytelist = map(''.join, zip(*[iter(bitstr)] * 8))
    asciilist = [chr(sum([int(b) << 7 - n for (n, b) in enumerate(byte)])) for byte in bytelist]
    await reply(client, message, "Output: `{}`".format(''.join(asciilist)))


@prim_cmd("cat", "Fun stuff",
          "Sends a random cat image",
          "Usage cat\
          \n\nReplies with a random cat image!")
async def prim_cmd_cat(message, cargs, client, conf, botdata):
    async with aiohttp.get('http://random.cat/meow') as r:
        if r.status == 200:
            js = await r.json()
            embed = discord.Embed(title="Meow!", color=discord.Colour.light_grey())
            embed.set_image(url=js['file'])
            await client.send_message(message.channel, embed=embed)


@prim_cmd("dog", "Fun stuff",
          "Sends a random dog image",
          "Usage dog\
          \n\nReplies with a random dog image!")
async def prim_cmd_dog(message, cargs, client, conf, botdata):
    async with aiohttp.get('http://random.dog/woof') as r:
        if r.status == 200:
            dog = await r.text()
            embed = discord.Embed(title="Woof!", color=discord.Colour.light_grey())
            embed.set_image(url="https://random.dog/"+dog)
            await client.send_message(message.channel, embed=embed)

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
