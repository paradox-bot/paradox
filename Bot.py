"""
Currently a weak implementation, aiming for a working prototype.
Needs to be completed ASAP.
"""
import importlib
import traceback
from Context import CommandContext, MessageContext


class Bot:
    def __init__(self, client, data, serv_conf, user_conf, bot_conf, log_file="bot.log", DEBUG=0):
        self.client = client
        self.data = data
        self.objects = {}
        self.serv_conf = serv_conf  # TODO: Why are these even here?
        self.user_conf = user_conf
        self.bot_conf = bot_conf
        self.log_file = log_file
        self.DEBUG = DEBUG

        self.global_cmd_list = {}
        self.user_cmd_list = {}
        self.server_cmd_list = {}
        # For lack of a better place to put it, define incoming event stuff here with the standard decorators

        # Not using the caching system for now, just straight up checking.
        @client.event
        async def on_message(message):
            """
            Do basic interp, check the message against the provided caches.
            TODO: Actually curently done with a raw check on the data.
            """
            prefix = 0
            msgctx = MessageContext(bot=self, message=message)
            for prfx in msgctx.get_prefixes():
                if message.content.startswith(prfx):
                    prefix = prfx
                    break
            if not prefix:
                if message.content.split('>')[0].strip(' <!@>') != client.user.id:
                    return
                else:
                    prefix = message.content.split('>')[0] + '>'
            self.parse_cmd(prefix, msgctx)

    async def parse_cmd(self, used_prefix, ctx):
        if self.DEBUG > 0:
            await self.log("Got the command \n{}\nfrom \"{}\" with id \"{}\""
                           .format(ctx.cntnt, ctx.author, ctx.authid))
        cmd_msg = ctx.cntnt[len(used_prefix):].strip()
        cmd_name = cmd_msg.split(' ')[0]
        arg_str = cmd_msg[len(cmd_name):].strip()
        cmd_name = cmd_name.strip().lower()
        cmd = 0
        if "user:{}:{}".format(ctx.authid, cmd_name) in self.user_cmd_list:
            cmd = self.user_cmd_list["user:{}:{}".format(ctx.authid, cmd_name)]
        elif "server:{}:{}".format(ctx.server.id, cmd_name) in self.server_cmd_list:
            cmd = self.server_cmd_list["server:{}:{}".format(ctx.server.id, cmd_name)]
        elif cmd_name in self.global_cmd_list:
            cmd = self.global_cmd_list[cmd_name]
        cmdCtx = CommandContext(ctx=ctx, cmd=cmd, arg_str=arg_str)
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

    def load_cmds(self, filepath):
        """
        Loads commands from a provided command file. Command loading logic is handled by the CH.
        Hopefully the CH is sane.
        TODO: Not really sure how to dynamically import, may need to redo this.
        Also want to be able to handle directories here
        """
        module = importlib.import_module(filepath)
        module.cmds.load_into(self)

    def load_events(self, filepath):
        """
        Loads an event handler from the provided file.
        Should loading logic be done by the files? Probably not.
        Maybe use a function to load a single event, and pass the files a bot instance
        """
        pass
