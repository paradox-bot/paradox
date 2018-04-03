"""
Currently a weak implementation, aiming for a working prototype.
Needs to be completed ASAP.
"""
import imp
import traceback
import os
from discord import Client
from contextBot.Context import Context, CommandContext, MessageContext


class Bot(Client):
    def __init__(self, data, bot_conf, log_file="bot.log", DEBUG=0, prefix="", prefix_func=None):
        super().__init__()
        self.data = data
        self.objects = {}
        self.bot_conf = bot_conf
        self.log_file = log_file
        self.DEBUG = DEBUG
        self.LOGFILE = log_file
        self.prefix = prefix
        self.get_prefixes = prefix_func
        self.loading_leader = ""

        if prefix_func is not None:
            self.add_to_ctx(prefix_func, "get_prefixes")

        self.cmd_cache = []
        self.cmds = []
        self.handlers = []

        self.modules_loaded = 0

    # Not using the caching system for now, just straight up checking.
    async def on_message(self, message):
        """
        Do basic interp, check the message against the provided caches.
        TODO: Actually curently done with a raw check on the data.
        """
        prefix = 0
        msgctx = MessageContext(bot=self, message=message)
        if self.DEBUG > 2:
            await self.log("Available prefixes are:" + str(await msgctx.get_prefixes()))
        for prfx in (await msgctx.get_prefixes()):
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
        cmd_msg = ctx.cntnt[len(used_prefix):].strip()
        cmd_name = cmd_msg.split(' ')[0]
        arg_str = cmd_msg[len(cmd_name):].strip()
        cmd_name = cmd_name.strip().lower()
        if cmd_name not in self.cmd_cache:
            return
        cmds = await ctx.get_cmds()
        if cmd_name not in cmds:
            return
        if self.DEBUG > 0:
            await self.log("Got the command \n{}\nfrom \"{}\" with id \"{}\""
                           .format(ctx.cntnt, ctx.author, ctx.authid))
        cmd = cmds[cmd_name]
        # Very ugly, want a way to instantiate commandContext using Message context
        cmdCtx = CommandContext(bot=self,
                                message=ctx.msg,
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
            logfile.write(logMessage + "\n")
        return

    def sync_log(self, logMessage):
        '''
        Logs logMessage synchronously
        '''
        print(logMessage)
        with open(self.LOGFILE, 'a+') as logfile:
            logfile.write(logMessage + '\n')
        return

    def load(self, *argv, depth=0, ignore=[]):
        """
        Intelligently loads modules from the given filepath(s).
        If given a directory, iterates over each file.
        Looks for cmds and load_into, treats them as expected.
        """
        leader = ">.."
        if len(argv) > 1:
            for fp in argv:
                self.load(fp, depth=depth, ignore=ignore)
            return

        fp = argv[0]
        if self.DEBUG > 0:
            self.sync_log("\n"+self.loading_leader+"Loading modules from path: " + fp)
        for ignored in ignore:
            if fp.endswith("/"+ignored):
                self.sync_log(self.loading_leader+"-Path was in ignored list, skipping")
                return

        if os.path.isdir(fp):
            self.sync_log(self.loading_leader+">Path appears to be a directory, going in")
            for fn in os.listdir(fp):
                old_leader = self.loading_leader
                self.loading_leader += leader
                self.load(os.path.join(fp,fn), depth=depth+1, ignore=ignore)
                self.loading_leader = old_leader
            self.sync_log(leader*depth+">Going out of {}\n".format(fp))
            return
        if os.path.isfile(fp):
            if fp.endswith(".py"):
                self.modules_loaded += 1
                module = imp.load_source("bot_module_" + str(self.modules_loaded), fp)
                attrs = dir(module)
                is_module = 0
                old_leader = self.loading_leader
                if "cmds" in attrs:
                    is_module += 1
                    self.loading_leader += "++"
                    self.sync_log(self.loading_leader+" Found \"cmds\" object in file, loading as commands.")
                    self.loading_leader += "+ "
                    module.cmds.load_into(self)
                if "load_into" in attrs:
                    is_module += 1
                    self.loading_leader += "++"
                    self.sync_log(self.loading_leader+" Found \"load_into\" method in file, loading as a module.")
                    self.loading_leader += "+ "
                    module.load_into(self)
                if not is_module:
                    self.loading_leader += "--"
                    self.sync_log(self.loading_leader+" File does not appear to be a valid module. Moving on.")
                self.loading_loader = old_leader



            else:
                self.sync_log(leader*depth+">File was not a python file, skipping")
            return
        else:
            self.sync_log(leader*depth+">File could not be found, skipping")


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

    def util(self, func):
        """
        Decorator to make a util method available as a method of Context.
        """
        self.add_to_ctx(func)
        return func

    def add_to_ctx(self, attr, name=None):
        if self.DEBUG:
            self.sync_log(self.loading_leader+"Adding context attribute: {}".format(name if name else attr.__name__))
        setattr(Context, name if name else attr.__name__, attr)

