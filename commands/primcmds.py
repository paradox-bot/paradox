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

@prim_cmd("restart", "Bot admin",
          "Restart the bot without pulling from git first",
          "Usage: restart\n\nRestarts the bot without pulling from git first")
@require_perm("Manager")
async def prim_cmd_restart(message, cargs, client, conf, botdata):
    await reply(client, message, os.system('./Nanny/scripts/redeploy.sh'))


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


@prim_cmd("rep", "Fun stuff",
          "Give reputation to a user",
          "Usage: rep [mention] | rep stats\
          \n\nGives a reputation point to the mentioned user or shows your current reputation cooldown timer.")
async def prim_cmd_rep(message, cargs, client, conf, botdata):
    cooldown = 24*60*60
    now = datetime.datetime.utcnow()
    now_timestamp = int(now.strftime('%s'))
    last_rep = botdata.users.get(message.author.id, "last_rep_time")

    if cargs == "" or cargs.strip() == "stats":
        if last_rep is None:
            await reply(client, message, "You have not yet given any reputation!\nStart giving reputation using `rep <user>`!")
            return
        last_rep = int(last_rep)
        given_ago = now_timestamp - last_rep
        if cargs == "":
            can_give_in = cooldown - given_ago
            if can_give_in > 0:
                can_give_str = strfdelta(datetime.timedelta(seconds=can_give_in), sec=True)
                msg = "You may give reputation in {}.".format(can_give_str)
            else:
                msg = "You may now give reputation!"
        else:
            given_rep = botdata.users.get(message.author.id, "given_rep")
            last_rep_str = strfdelta(datetime.timedelta(seconds=given_ago))
            msg = "You have given **{}** reputation point{}! You last gave a reputation point **{}** ago.".format(given_rep, "s" if int(given_rep)>1 else "", last_rep_str)
        await reply(client, message, msg)
        return
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
            given_ago = now_timestamp - int(last_rep)
            if given_ago < cooldown:
                msg = "Cool down! You may give reputation in {}.".format(strfdelta(datetime.timedelta(seconds=(cooldown - given_ago)), sec = True))
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


@prim_cmd("cheatreport", "General",
          "Reports a user for cheating with rep/level/xp",
          "Usage: report [user] [cheat] [evidence]\
          \n\nReports a user for cheating on a social system. Please provide the user you wish to report, the form of cheat, and your evidence.")
async def prim_cmd_cr(message, cargs, client, conf, botdata):
    await reply(client, message, 'WIP. Pue pls write')
    embed = discord.Embed(title="Cheat Report", color=discord.Colour.red()) \
        .set_author(name="{} ({})".format(message.author, message.author.id),
                    icon_url=message.author.avatar_url) \
        .add_field(name="User", value=".", inline=True) \
        .add_field(name="Cheat", value="Alt Repping|Chatbot|Spamming", inline=True) \
        .add_field(name="Evidence", value="(Evidence from args)", inline=False) \
        .set_footer(text="Guild name|Timestamp")
    await client.send_message(message.channel, embed=embed)

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
