import discord
import asyncio

class Context:
    def __init__(self, **kwargs):
        self.cmd_err = (0, "")
        self.bot_err = (0, "")
        self.err = (0, None, "")
        self.objs = {}

        self.bot = kwargs["bot"] if ("bot" in kwargs) else None
        self.ch = kwargs["channel"] if ("channel" in kwargs) else None
        self.server = kwargs["server"] if ("server" in kwargs) else None
        self.client = kwargs["client"] if ("client" in kwargs) else None
        self.data = kwargs["data"] if ("data" in kwargs) else None
        self.user = kwargs["user"] if ("user" in kwargs) else None
        self.member = kwargs["member"] if ("member" in kwargs) else None

        self.serv_conf = kwargs["serv_conf"] if ("serv_conf" in kwargs) else None

        if self.bot and not self.data:
            self.data = self.bot.data
        if self.ch and not self.server:
            self.server = self.ch.server
        if self.member and not self.user:
            self.user = self.member

        if self.bot:
            self.log = self.bot.log
            self.client = self.bot.client
            self.serv_conf = self.bot.serv_conf

    async def para_format(self, string):
        client = self.client
        user = self.user
        server = self.server
        keydict = {"$servers$": str(len(client.servers)),
                   "$users$": str(len(list(client.get_all_members()))),
                   "$channels$": str(len(list(client.get_all_channels()))),
                   "$username$": user.name if user else "",
                   "$mention$": user.mention if user else "",
                   "$id$": user.id if user else "",
                   "$tag$": str(user) if user else "",
                   "$displayname$": user.display_name if user else "",
                   "$server$": server.name if server else ""}
        for key in keydict:
            string = string.replace(key, keydict[key])
        return string

    def get_prefix(conf, serv_conf, botdata, server):
        prefix_conf = serv_conf["prefix"]
        prefix = conf.get("PREFIX")
        if server:
            prefix = prefix_conf.get(botdata, server)
            prefix = prefix if prefix != prefix_conf.default else conf.get("PREFIX")
        return prefix

    async def find_user(self, user_str, in_server=False):
        if user_str == "":
            return None
        maybe_user_id = user_str.strip('<@!> ')
        if maybe_user_id.isdigit():
            def is_user(member):
                return member.id == maybe_user_id
        else:
            def is_user(member):
                return ((user_str.lower() in member.display_name.lower()) or (user_str.lower() in member.name.lower()))
        if self.server:
            member = discord.utils.find(is_user, self.server.members)
        if not (member or in_server):
            member = discord.utils.find(is_user, self.client.get_all_members)
        return member

    async def get_cmds(self):
        handlers = self.bot.handlers
        cmds = {}
        for CH in handlers:
            cmds = dict(cmds, **(await CH.get_cmds(self)))
        return cmds

    def get_prefixes(self):
        """
        Returns a list of valid prefixes in this context.

        TODO: Currently just grabs the default prefix and the server prefix.
        """
        prefix = 0
        prefix_conf = self.serv_conf["prefix"]
        if self.server:
            prefix = prefix_conf.get(self.data, self.server)
        prefix = prefix if prefix else self.bot.bot_conf.get("PREFIX")
        return [prefix]

    async def run_sh(self, to_run):
        """
        Runs a command asynchronously in a subproccess shell.
        """
        process = await asyncio.create_subprocess_shell(to_run, stdout=asyncio.subprocess.PIPE)
        if self.bot.DEBUG > 1:
            await self.log("Running the shell command:\n{}\nwith pid {}".format(to_run, str(process.pid)))
        stdout, stderr = await process.communicate()
        if self.bot.DEBUG > 1:
            await self.log("Completed the shell command:\n{}\n{}".format(to_run, "with errors." if process.returncode != 0 else ""))
        return stdout.decode().strip()



class MessageContext(Context):
    def __init__(self, **kwargs):
        if "msgctx" in kwargs:
            self = kwargs["msgctx"]
        super().__init__(**kwargs)
        self.author = None
        self.message = None

        if "author" in kwargs:
            self.author = kwargs["author"]
            self.member = self.author
            self.user = self.member

        if "message" in kwargs:
            self.msg = kwargs["message"]
            self.author = self.msg.author
            self.member = self.msg.author
            self.user = self.msg.author
            self.ch = self.msg.channel
            self.server = self.msg.server
            self.cntnt = self.msg.content
            self.id = self.msg.id
            self.authid = self.author.id

    async def reply(self, message=None, embed=None, dm=False):
        """
        Replies with message. If dm is False, replies in the channel. Otherwise, replies in dm.

        message (str): The message to reply with. Must be a string or castable to a string.
        """
        if not dm:
            if (message is None) and (embed is None):
                self.bot_err = (-1, "Tried to reply with a None message")
            if self.ch is None:
                self.bot_err = (2, "Require channel for reply")

        if message == "":
            self.bot_err = (-1, "Tried to reply with an empty message")
        if self.client is None:
            self.bot_err = (2, "Require client for reply")
        if self.bot_err[0] != 0:
            await self.log("Caught error in reply, code {0[0]} message \"{0[1]}\"".format(self.bot_err))
            return None
        if message:
            return await self.client.send_message(self.author if dm else self.ch, str(message), embed=embed)
        else:
            return await self.client.send_message(self.author if dm else self.ch, embed=embed)




class CommandContext(MessageContext):
    def __init__(self, **kwargs):
        if "cmdctx" in kwargs:
            self = kwargs["cmdctx"]
        super().__init__(**kwargs)

        self.cmd = None
        self.CH = None

        self.arg_str = kwargs["arg_str"] if ("arg_str" in kwargs) else None
        self.used_prefix = kwargs["used_prefix"] if ("used_prefix" in kwargs) else None

        if "cmd" in kwargs:
            self.cmd = kwargs["cmd"]
            self.CH = self.cmd.handler

        self.params = kwargs["params"] if ("params" in kwargs) else None
        if self.params is None:
            if self.arg_str is None:
                if self.msg is None:
                    self.cmd_err = (2, "Require message for initialising cmd context from message")
                    return
                if self.used_prefix is None:
                    self.cmd_err = (2, "Require used prefix for initialising cmd context from message")
                    return
                self.arg_str = self.cntnt[len(self.used_prefix):].strip()[len(self.cmd.name):]
            self.params = self.parse_args(self.arg_str)

    def parse_args(self, arg_str):
        """
        Takes in the arg_str and returns a list of params.
        If quotes are used, this is where they are understood.
        """
        return arg_str.strip().split(' ')

    async def check(self, check_str, **kwargs):
        if check_str not in self.CH.checks:
            self.cmd_err = ("3", "There was an internal error: ERR_BAD_CHECK")
            return self.cmd_err
        return await self.CH.checks[check_str]

    async def run(self, snip_str, **kwargs):
        if snip_str not in self.CH.snippets:
            self.cmd_err = ("3", "There was an internal error: ERR_BAD_SNIP")
            return self.cmd_err
        return await self.CH.snippets[snip_str](self, **kwargs)
