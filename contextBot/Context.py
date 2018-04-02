import discord

class Context:
    def __init__(self, **kwargs):
        self.cmd_err = (0, "")
        self.bot_err = (0, "")
        self.err = (0, None, "")
        self.objs = {}

        self.bot = kwargs["bot"] if ("bot" in kwargs) else None
        self.ch = kwargs["channel"] if ("channel" in kwargs) else None
        self.server = kwargs["server"] if ("server" in kwargs) else None
        self.data = kwargs["data"] if ("data" in kwargs) else None
        self.user = kwargs["user"] if ("user" in kwargs) else None
        self.member = kwargs["member"] if ("member" in kwargs) else None

        if self.bot and not self.data:
            self.data = self.bot.data
        if self.ch and not self.server:
            self.server = self.ch.server
        if self.member and not self.user:
            self.user = self.member
        if self.member and not self.server:
            self.server = self.member.server

        if self.bot:
            self.log = self.bot.log
        else:
            self.log = None

        if self.server:
            self.me = self.server.me
        elif self.bot:
            self.me = self.bot.user
        else:
            self.me = None

    async def ctx_format(self, string):
        bot = self.bot
        user = self.user
        server = self.server
        keydict = {"$servers$": str(len(bot.servers)),
                   "$users$": str(len(list(bot.get_all_members()))),
                   "$channels$": str(len(list(bot.get_all_channels()))),
                   "$username$": user.name if user else "",
                   "$mention$": user.mention if user else "",
                   "$id$": user.id if user else "",
                   "$tag$": str(user) if user else "",
                   "$displayname$": user.display_name if user else "",
                   "$server$": server.name if server else ""}
        for key in keydict:
            string = string.replace(key, keydict[key])
        return string

    async def get_cmds(self):
        handlers = self.bot.handlers
        cmds = {}
        for CH in handlers:
            cmds = dict(cmds, **(await CH.get_cmds(self)))
        return cmds

    async def get_prefixes(self):
        """
        Returns a list of valid prefixes in this context.
        Expect to be overriden from bot initialisation.
        """
        prefix = self.bot.prefix
        return [prefix]

    async def msg_split(self, msg, code=False, MAX_LEN = 1800):
        if code:
            msg = msg.strip("```")
        if len(msg) < MAX_LEN:
            return ["```"+msg+"```"] if code else [msg]
        lines = msg.strip().split('\n')

        split_len = 0
        splits = []
        split = ""
        for line in lines:
            if split_len + len(line) > MAX_LEN:
                splits.append(split)
                split_len = 0
                split = ""
            split = split + "\n" + line
            split_len = split_len + len(line) + 1
        splits.append(split)
        if code:
            splits = ["```\n"+split+"\n```" for split in splits]
        return splits

    async def send(self, destination, message=None, embed=None, file_name=None, split=False, code=False):
        """
        Sends a message with the specified paramaters to the specified channel.
        """
        if message == "":
            self.bot_err = (-1, "Tried to reply with an empty message")
        if self.bot is None:
            self.bot_err = (2, "Require bot for reply")
        if (not file_name) and (message is None) and (embed is None):
            self.bot_err = (-1, "Tried to reply without anything to reply with")

        if self.bot_err[0] != 0:
            await self.log("Caught error in reply, code {0[0]} message \"{0[1]}\"".format(self.bot_err))
            return None
        if file_name:
            return await self.bot.send_file(destination, file_name, content=message)
        if message:
            if split and (not embed):
                splits = await self.msg_split(str(message), code)
                out = []
                for split in splits:
                    out.append(await self.bot.send_message(destination, split))
                return out
            else:
                if len(message) >= 2000:
                    self.bot_err = (3, "Tried to send a message which was too long")
                    return
                return await self.bot.send_message(destination, str(message), embed=embed)
        elif embed:
            return await self.bot.send_message(destination, embed=embed)


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


    async def reply(self, message=None, embed=None, file_name=None, dm=False, **kwargs):
        """
        A wrapper for send used to reply to a message.
        If dm is true, replies in private message to the sending user.
        Otherwise reply in the same channel as the instantiating message.
        """
        if not (dm or self.ch):
            self.bot_err = (2, "Require channel for non dm reply")
            return None


        destination = self.author if dm else self.ch
        try:
            return await self.send(destination, message=message, embed=embed, file_name=file_name, **kwargs)
        except discord.Forbidden as e:
            """
            Handles each of the following errors:
                Can't DM user if dm is true
                Can't send embeds if embed exists
                Can't send messages at all.
            """
            if dm:
                await self.reply("I can't DM you! Do you have me blocked or direct messages turned off?")
                self.cmd_err = (1, "")
            else:
                perms = self.ch.permissions_for(self.me)
                if not perms.send_messages:
                    try:
                        await self.send(self.author, "I don't have permissions to reply in that channel! If you believe this is in error, please contact a server administrator.")
                        await self.reply(message, embed, file_name, dm=False)
                        return
                    except discord.Forbidden:
                        pass
                elif file_name and not perms.attach_files:
                    await self.reply("I don't have permission to send files here!")
            self.cmd_err = (1, "")
            raise e
            return


    async def del_src(self):
        """
        Attempts to delete the sending message.
        Fails silently if it can't delete.
        """
        try:
            return await self.bot.delete_message(self.msg)
        except Exception:
            pass


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
