import re
import discord
from paraSetting import paraSetting


class BOOL(paraSetting):
    """
    A sort of boolean type, more like a wrapper for a boolean.
    """
    accept = "Yes/No, On/Off, True/False, Enabled/Disabled"
    inputexps = {"^yes$": True,
                 "^true$": True,
                 "^on$": True,
                 "^enabled?$": True,
                 "^no$": False,
                 "^false$": False,
                 "^off$": False,
                 "^disabled?$": False}
    outputs = {True: "",
               False: ""}

    @classmethod
    async def humanise(cls, ctx, raw):
        return cls.outputs[raw]

    @classmethod
    async def understand(cls, ctx, userstr):
        for pattern in cls.inputexps:
            if re.match(pattern, userstr, re.I):
                return cls.inputexps[pattern]
        ctx.cmd_err = (1, "I don't understand this value. Acceptable values are: {}".format(cls.accept))
        return None


class STR(paraSetting):
    """
    Just a plain string, nothing special
    """
    accept = "Any text"

    @classmethod
    async def humanise(cls, ctx, raw):
        return "\"{}\"".format(str(raw))

    @classmethod
    async def understand(cls, ctx, userstr):
        if userstr.startswith("\"") and userstr.endswith("\""):
            return userstr[1:-1]
        if userstr.startswith("'") and userstr.endswith("'"):
            return userstr[1:-1]
        return userstr


class FMTSTR(STR):
    """
    Formatable string
    TODO: accepted keys in variable from somewhere
    """
    accept = "Formatted string, accepted keys are:\n"
    accept += "\t $username$, $mention$, $id$, $tag$, $displayname$, $server$"


class ROLE(paraSetting):
    """
    ROLE type.
    """
    accept = "Role mention/id/name, or 'none' to unset"

    @classmethod
    async def humanise(self, ctx, raw):
        """
        Expect raw to be role id or 0, an empty.
        """
        if (not raw) or raw == "0":
            return "None"
        role = discord.utils.get(ctx.server.roles, id=raw)
        if role:
            return "{}".format(role.name)
        return "{} (Role not found!)".format(raw)

    @classmethod
    async def understand(self, ctx, userstr):
        """
        User can enter a role mention or an id, or even a partial name.
        """
        if userstr.lower() in ["0", "none"]:
            return "0"
        role = await ctx.find_role(userstr, create=True, interactive=True)
        return role.id if role else None


class CHANNEL(paraSetting):
    """
    Channel type.
    """
    accept = "Channel mention/id/name. Use 0 to clear the setting."

    @classmethod
    async def humanise(self, ctx, raw):
        """
        Expect raw to be channel id or 0, an empty.
        """
        if not raw:
            return "None"
        channel = ctx.server.get_channel(raw)
        if channel:
            return "{}".format(channel.name)
        return "<#{}>".format(raw)

    @classmethod
    async def understand(self, ctx, userstr):
        """
        User can enter a channel mention or an id, or even a partial name.
        """
        if not ctx.server:
            ctx.cmd_err = (1, "This is not valid outside of a server!")
            return None
        userstr = str(userstr)
        if userstr.lower() in ["none", "0"]:
            return None
        chid = userstr.strip('<#@!>')
        if chid.isdigit():
            def is_ch(ch):
                return ch.id == chid
        else:
            def is_ch(ch):
                return userstr.lower() in ch.name.lower()
        ch = discord.utils.find(is_ch, ctx.server.channels)
        if ch:
            return ch.id
        else:
            ctx.cmd_err = (1, "I can't find the channel `{}` in this server!".format(userstr))
            return None


class SETTING_LIST(paraSetting):
    """
    List of a particular type of setting
    """
    setting_type = paraSetting

    @classmethod
    async def humanise(self, ctx, raw):
        """
        Expect a list of the raw type of the setting.
        """
        if not raw:
            return "None"
        humanised = []
        for raw_item in raw:
            humanised.append(await self.setting_type.humanise(ctx, raw_item))
        return ", ".join(humanised)

    @classmethod
    async def understand(self, ctx, userstr):
        """
        User can enter a list of the userstrs accepted by the setting.
        """
        userstr = str(userstr)
        userstrs = [us.strip() for us in userstr.split(",")]
        items = []
        for us in userstrs:
            item = await self.setting_type.understand(ctx, us)
            if item is None:
                return None
            items.append(item)
        return items


class CHANNELLIST(SETTING_LIST):
    """
    List of channels
    """
    accept = "Comma separated list of channel mentions/ids/names. Use 0 or None to clear the setting."
    setting_type = CHANNEL


class ROLELIST(SETTING_LIST):
    """
    List of channels
    """
    accept = "Comma separated list of rolw mentions/ids/names. Use 0 or None to clear the setting."
    setting_type = ROLE


"""
class YES_BOOL(BOOL):
    name = "Yes/No"
    outputs = {True: "Yes",
               False: "No"}


class ENABLED_BOOL(BOOL):
    name = "Enabled/Disabled"
    outputs = {True: "Enabled",
               False: "Disabled"}
"""
'''
class userList(paraSetting):
    name = "List of users"
    accept = "[+/add | -/remove] <userid/mention>"
    str_already_in_list = ""
    str_not_in_list = ""
    str_removed_from_list = ""
    str_added_to_list = ""

    def humanise(self, raw):
        """
        Expect raw to be a list, possibly of strings, possible of integers, containing userids.
        """
        if self.client is None:
            return ', '.join([str(user) for user in raw if str(user).isdigit()])
        users = [str(user) for user in raw]
        user_tags = [discord.utils.get(self.client.get_all_members(), id=user) for user in users]
        userlist = [str(user) for user in user_tags if user]
        return '`{}`'.format('`, `'.join(userlist))

    def understand(self, userstr):
        params = userstr.split(' ')
        action = params[0]
        if (action in ['+', 'add']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
            userid = int(params[1].strip('<!@>'))
            if userid in self.raw:
                (self.error, self.errmsg) = (3, self.str_already_in_list)
                return self.raw
            else:
                self.raw.append(userid)
                (self.error, self.errmsg) = (0, self.str_added_to_list)
                return self.raw
        elif (action in ['-', 'remove']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
            userid = int(params[1].strip('<!@>'))
            if userid not in self.raw:
                (self.error, self.errmsg) = (3, self.str_not_in_list)
                return self.raw
            else:
                self.raw.remove(userid)
                (self.error, self.errmsg) = (0, self.str_removed_from_list)
                return self.raw
        else:
            (self.error, self.errmsg) = (1, "I don't understand your input. Valid input is: `{}`".format(self.accept))
            return self.raw
'''


"""
class userBlackList(userList):
    name = "List of users"
    accept = "[+/add | -/remove] <userid/mention>"
    str_already_in_list = "I have already blacklisted this user!"
    str_not_in_list = "This user hasn't been blacklisted."
    str_removed_from_list = "Let's hope they stay out of trouble. That user is no longer blacklisted."
    str_added_to_list = "I never liked them anyway, that user is now blacklisted."


class userMasterList(userList):
    name = "List of users"
    accept = "[+/add | -/remove] <userid/mention>"
    str_already_in_list = "This user is already one of my masters!"
    str_not_in_list = "This user is not one of my masters!"
    str_removed_from_list = "I have rejected this master."
    str_added_to_list = "I accept this user as a new master."
"""


'''
class SERVER(_settingType):
    """
    Server type.
    Incomplete.
    """
    name = "server"
    accept = "Server name/ server id"
'''
