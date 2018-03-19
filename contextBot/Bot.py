"""
Currently a weak implementation, aiming for a working prototype.
Needs to be completed ASAP.
"""
import imp
import traceback
from discord import client
from contextBot.Context import CommandContext, MessageContext


class Bot(Client):
    def __init__(self, data, serv_conf, user_conf, bot_conf, log_file="bot.log", DEBUG=0):
        super().__init__()
        self.client = self
        self.data = data
        self.objects = {}
        self.serv_conf = serv_conf  # TODO: Why are these even here?
        self.user_conf = user_conf
        self.bot_conf = bot_conf
        self.log_file = log_file
        self.DEBUG = DEBUG
        self.LOGFILE = log_file

        self.cmd_cache = []
        self.cmds = []
        self.handlers = []

    # Not using the caching system for now, just straight up checking.
    async def on_message(self, message):
        """
        Do basic interp, check the message against the provided caches.
        TODO: Actually curently done with a raw check on the data.
        """
        prefix = 0
        msgctx = MessageContext(bot=self, message=message, serv_conf=self.serv_conf)
        if self.DEBUG > 2:
            await self.log("Available prefixes are:" + str(msgctx.get_prefixes()))
        for prfx in msgctx.get_prefixes():
            if message.content.startswith(prfx):
                prefix = prfx
                break
        if not prefix:
            if message.content.split('>')[0].strip(' <!@>') != self.user.id:
                return
            else:
                prefix = message.content.split('>')[0] + '>'
        await self.parse_cmd(prefix, msgctx)

    async def parse_cmd(self, used_prefix, ctx):
        if self.DEBUG > 0:
            await self.log("Got the command \n{}\nfrom \"{}\" with id \"{}\""
                           .format(ctx.cntnt, ctx.author, ctx.authid))
        cmd_msg = ctx.cntnt[len(used_prefix):].strip()
        cmd_name = cmd_msg.split(' ')[0]
        arg_str = cmd_msg[len(cmd_name):].strip()
        cmd_name = cmd_name.strip().lower()
        if cmd_name not in self.cmd_cache:
            return
        cmds = await ctx.get_cmds()
        if cmd_name not in cmds:
            return
        cmd = cmds[cmd_name]
        # Very ugly, want a way to instantiate commandContext using Message context
        cmdCtx = CommandContext(bot=self,
                                message=ctx.msg,
                                serv_conf=self.serv_conf,
                                cmd=cmd,
                                arg_str=arg_str,
                                used_prefix=used_prefix)
        try:
            await cmd.run(cmdCtx)
        except Exception:
            traceback.print_exc()
            try:
                await cmdCtx.reply("Something went wrong internally.. The error has been logged and should be fixed soon!")
            except Exception:
                await self.log("Something unexpected happened and I can't print the error. Dying now.")

    async def log(self, logMessage):
        '''
        Logs logMessage in some nice way.
        '''
        # TODO: Some nicer logging, timestamps, a little bit of context
        # For now just print it.
        print(logMessage)
        with open(self.LOGFILE, 'a+') as logfile:
            logfile.write("\n" + logMessage + "\n")
        return

    def sync_log(self, logMessage):
        '''
        Logs logMessage synchronously
        '''
        print(logMessage)
        with open(self.LOGFILE, 'a+') as logfile:
            logfile.write("\n" + logMessage + "\n")
        return

    def load_cmds(self, filepath):
        """
        Loads commands from a provided command file. Command loading logic is handled by the CH.
        Hopefully the CH is sane.
        TODO: Not really sure how to dynamically import, may need to redo this.
        Also want to be able to handle directories here
        """
        if self.DEBUG > 0:
            self.sync_log("Loading command file from path: " + filepath)
        module = imp.load_source("cmds", filepath)
        module.cmds.load_into(self)

    def load_module(self, filepath):
        """
        Loads a module from the provided file path.
        (E.g. for loading event handlers)

        Expects the module to have a method load_into(bot).
        """
        if self.DEBUG > 0:
            self.sync_log("Loading module from path: " + filepath)
        module = imp.load_source("load_into", filepath)
        module.load_into(self)
