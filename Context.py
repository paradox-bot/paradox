import discord


class Context:
    async def __init__(self, **kwargs):
        self.cmd_err = (0, "")
        self.err = (0, "")

        self.bot = kwargs["bot"] if ("bot" in kwargs) else None
        self.ch = kwargs["channel"] if ("channel" in kwargs) else None
        self.server = kwargs["server"] if ("server" in kwargs) else None
        self.client = kwargs["client"] if ("client" in kwargs) else None
        self.data = kwargs["data"] if ("data" in kwargs) else None
        self.user = kwargs["user"] if ("user" in kwargs) else None
        self.member = kwargs["member"] if ("member" in kwargs) else None

        if self.bot and not self.data:
            self.data = self.bot.data
        if self.ch and not self.server:
            self.server = self.ch.server
        if self.member and not self.user:
            self.user = self.member

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


class MessageContext(Context):
    async def __init__(self, **kwargs):
        await super.__init__(**kwargs)
        self.author, self.message = None

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

    async def reply(self, message):
        """
        Replies to self.ch with message.

        message (str): The message to reply with. Must be a string or castable to a string.
        """
        if message is None:
            self.err = (-1, "Tried to reply with a None message")
        if message == "":
            self.err = (-1, "Tried to reply with an empty message")
        if self.ch is None:
            self.err = (-2, "Require channel for reply")
        if self.client is None:
            self.err = (-2, "Require client for reply")
        if self.err[0] != 0:
            return
        message = str(message)
        await self.client.send_message(self.ch, message)


class CommandContext(MessageContext):
    async def __init__(self, **kwargs):
        if "ctx" in kwargs:
            self = kwargs["ctx"]
        else:
            await super.__init(**kwargs)
        self.cmd, self.CH = None

        self.arg_str = kwargs["arg_str"] if ("arg_str" in kwargs) else None
        self.used_prefix = kwargs["arg_str"] if ("arg_str" in kwargs) else None

        if "cmd" in kwargs:
            self.cmd = kwargs["cmd"]
            self.CH = self.cmd.CH

        self.params = kwargs["params"] if ("params" in kwargs) else None
        if self.params is None:
            if self.arg_str is None:
                if self.msg is None:
                    self.err = (-2, "Require message for initialising cmd context from message")
                    return
                if self.used_prefix is None:
                    self.err = (-2, "Require used prefix for initialising cmd context from message")
                    return
                self.arg_str = self.cntnt[len(self.used_prefix):].strip()[len(self.cmd.name):]
            self.params = await self.parse_args(self.arg_str)

    async def parse_args(self, arg_str):
        """
        Takes in the arg_str and returns a list of params.
        If quotes are used, this is where they are understood.
        """
        return arg_str.strip().split(' ')
