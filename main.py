import discord
import asyncio
import json
import configparser as cfgp

CONF_FILE = "paradox.conf"
USER_CONF_FILE = "paradox_userdata.conf"

class Conf(cfgp.ConfigParser):
    section = "General"

    def __init__(self, conffile):
        super().__init__()
        self.read(conffile)

    def kget(self, option):
        return self.get(self.section, option)

    def kgetint(self, option):
        return self.getint(self.section, option)

    def kgetfloat(self, option):
        return self.getfloat(self.section, option)

    def kgetboolean(self, option):
        return self.getboolean(self.section, option)

    def kgetintlist(self, option):
        return json.loads(self.kget(option))



class UserConf:
    userSection = 'USERS'
    def __init__(self, conffile):
        self.conffile = conffile
        if not os.path.isfile(conffile):
            with open(conffile, 'a+') as configfile:
                configfile.write('')
        config = cfgp.ConfigParser()
        config.read(conffile)
        if self.userSection not in config.sections():
            config[self.userSection] = {}
        self.users = config[self.userSection]
        self.config = config
    def get(self, userid, prop):
        if str(userid) not in self.users:
            self.users[str(userid)] = '{}'
        user = json.loads(self.users[str(userid)])
        return user.get(prop, None)
    def getintlist(self, userid, prop):
        value = self.get(userid, prop)
        return value if value is not None else []
    def getStr(self, userid, prop):
        value = self.get(userid, prop)
        return value if value is not None else ""
    def set(self, userid, prop, value):
        if str(userid) not in self.users:
            self.users[str(userid)] = "{}"
        user = json.loads(self.users[str(userid)])
        user[prop] = value
        self.users[str(userid)] = json.dumps(user)
        self.write()
    def write(self):
        with open(self.conffile, 'w') as configfile:
            self.config.write(configfile)



conf = Conf(CONF_FILE)
userdata = UserConf(USER_CONF_FILE)
TOKEN = conf.kget("TOKEN")
PREFIX = conf.kget("PREFIX")


client = discord.Client()


#----Primitive Commands setup----
'''
This is for adding basic commands as a proof of concept.
Not intended to be used in production.
'''

#Initialise command dict
##Entries are indexed by cmdName and contain data described in prim_cmd
primCmds = {}

#Command decorator
def prim_cmd(cmdName, category, desc, helpDesc):
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




#----Discord event handling----

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("Logged into", len(client.servers), "servers")
    


'''
#Old on_message versions
@client.event
async def on_message(message):
        if message.content.startswith('~about'):
                await reply(message, 'This is a bot created via the collaborative efforts of Retro, Pue, and Loomy.')
        elif message.content.startswith('~ping'):
                sentMessage = await client.send_message(message.channel, 'Beep')
                mainMsg = sentMessage.timestamp
                editedMessage = await client.edit_message(sentMessage,'Boop')
                editMsg = editedMessage.edited_timestamp
                latency = editMsg - mainMsg
                latency = latency.microseconds // 1000
                latency = str(latency)
                await client.edit_message(sentMessage, 'Ping: '+latency+'ms')	
@client.event
async def on_message(message):
        if message.content.startswith('~about'):
                await reply(message, 'This is a bot created via the collaborative efforts of Retro, Pue, and Loomy.')
        elif message.content.startswith('~ping'):
                sentMessage = await client.send_message(message.channel, 'Beep')
                mainMsg = sentMessage.timestamp
                editedMessage = await client.edit_message(sentMessage,'Boop')
                editMsg = editedMessage.edited_timestamp
                latency = editMsg - mainMsg
                latency = latency.microseconds // 1000
                latency = str(latency)
                await client.edit_message(sentMessage, 'Ping: '+latency+'ms')
       elif message.content.startsWith('~help'):
               await client.send_message(message.channel, 'Available commands: `about`, `ping`')
                
'''

#We saw a message!
@client.event
async def on_message(message):
    '''
    Have a look at the message and decide if it is appropriate to do something with.
    If it looks like a message for us, and it's not from anyone bad,
    pass it on to the command parser.
    '''
    PREFIX = conf.kget("PREFIX") #In case someone changed it while we weren't looking
    if not message.content.startswith(PREFIX):
        #Okay, it probably wasn't meant for us, or they can't type
        #Either way, let's ignore them
        return
    if message.content == (PREFIX): 
        #Some ass just typed the prefix to try and trigger us.
        #Not even going to try parsing, just quit.
        return
    #TODO: Put something here about checking blacklisted users.
    #Okay, we have decided it was meant for us. Let's log it
    await log("Got the command \n{}\nfrom \"{}\" with id \"{}\" ".format(
        message.content, message.author, message.author.id)
        )
    #Now strip the prefix, we don't need that anymore, and extract command
    cmd_message = message.content[len(PREFIX):]
    cmd = cmd_message.strip().split(' ')[0].lower()
    args = ' '.join(cmd_message.strip().split(' ')[1:])
    await cmd_parser(message, cmd, args)
    return

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
    if cmd in primCmds:
        try:
            #Try running the command using the associated function,
            ##we don't trust this will actually work though.
            await primCmds[cmd][0](message, args)
            return
        except:
            #If it didn't work, print the stacktrace, and try to inform the user.
            #TODO: Log the stacktrace using log()
            traceback.print_exc()
            #Note something unexpected happened so we may not be able to inform the user.
            ##Maybe discord broke!
            ##Or more likely there's a permission error
            try:
                await reply(message, "Something went wrong. The error has been logged")
            except:
                await log("Something unexpected happened and I can't print the error. Dying now.")
            #Either way, we are done here.
            return
    else:
        #At this point we have tried all our command types. 
        ##The user probably made a spelling mistake.
        return

#----End Meta stuff----


#----Helper functions and routines----
async def log(logMessage):
    '''
    Logs logMessage in some nice way.
    '''
    #TODO: Log to file, or something nice.
    #For now just print it.
    print(logMessage)
    return



async def reply(message, content):
    await client.send_message(message.channel, content)

#----End Helper functions----



#------COMMANDS------

#Primitive Commands

@prim_cmd("about", "general", "No description", "No help")
async def prim_cmd_about(message, args):
    await reply(message, 'This is a bot created via the collaborative efforts of Retro, Pue, and Loomy.')

@prim_cmd("ping", "general", "No description", "No help")
async def prim_cmd_ping(message, args):
    sentMessage = await client.send_message(message.channel, 'Beep')
    mainMsg = sentMessage.timestamp
    editedMessage = await client.edit_message(sentMessage,'Boop')
    editMsg = editedMessage.edited_timestamp
    latency = editMsg - mainMsg
    latency = latency.microseconds // 1000
    latency = str(latency)
    await client.edit_message(sentMessage, 'Ping: '+latency+'ms')

@prim_cmd("help", "general", "No description", "No help")
async def prim_cmd_help(message, args):
   await client.send_message(message.channel, 'Available commands: `about`, `ping`')


#------END COMMANDS------

#----Event loops----
#----End event loops----


#----Everything is defined, start the client!----
client.run(conf.kget("TOKEN"))
