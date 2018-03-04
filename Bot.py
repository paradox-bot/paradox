"""
Currently a weak implementation, aiming for a working prototype.
Needs to be completed ASAP.
"""
import importlib
import traceback
from Context import CommandContext


class Bot:
    def __init__(self, client, data, serv_conf, user_conf, bot_conf, log_file="bot.log", DEBUG=0):
        self.client = client
        self.data = data
        self.objects = {}
        self.cmds = {}
        self.serv_conf = serv_conf  # TODO: Why are these even here?
        self.user_conf = user_conf
        self.bot_conf = bot_conf
        self.log_file = log_file
        self.DEBUG = DEBUG

        self.prefix_cache = {}
        self.command_cache = {}
        # For lack of a better place to put it, define incoming event stuff here with the standard decorators

        # Not using the caching system for now, just straight up checking.
        @client.event
        async def on_message(message):
            """
            Do basic interp, check the message against the provided caches.
            TODO: Actually curently done with a raw check on the data.
            """
            prefix_conf = self.serv_conf["prefix"]
            if message.server:
                prefix = prefix_conf.get(data, message.server)
                prefix = prefix if prefix else self.bot_conf.get("PREFIX")
            else:
                prefix = self.bot_conf.get("PREFIX")

            if not (message.content.startswith(prefix)):
                if message.content.split(' ')[0].strip('<!@>') != client.user.id:
                    return
                else:
                    prefix = message.content.split(' ')[0]
            if message.author.bot:
                return
            if int(message.author.id) in bot_conf.getintlist("blacklisted_users"):
                return
            self.parse_cmd(prefix, message)

    async def parse_cmd(self, used_prefix, message):
        if self.DEBUG > 0:
            await self.log("Got the command \n{}\nfrom \"{}\" with id \"{}\""
                           .format(message.content, message.author, message.author.id))
        cmd_msg = message.content[len(used_prefix):]
        cmd_name = cmd_msg.strip().split(' ')[0]
        arg_str = cmd_msg[len(cmd_name):].strip()
        cmd_name = cmd_name.strip.lower()
        if cmd_name not in self.cmds:
            return
        cmd = self.cmds[cmd_name]
        cmdCtx = CommandContext(bot=self,
                                message=message,
                                cmd=cmd,
                                arg_str=arg_str)
        try:
            await cmd.run(cmdCtx)
        except Exception:
            traceback.print_exc()
            try:
                await self.client.send_message(
                    "Something went wrong internally.. The error has been logged and should be fixed soon!")
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
