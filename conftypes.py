
"""
Able to initialise from user given string or from raw data.
Main job is to transform between raw data, user string input, visible output, and to give sensible error messages (optional, the configSetting class can have a default) when stuff doesn't look right.
values:
    readable option list/string
    raw
"""
import re
import discord


class _settingType:
    name = ""
    accept = ""

    def __init__(self, userstr=None, raw=None, message=None, server=None, botdata=None, client=None):
        """
        Initialise either empty (then must use constructors), or with userstr or raw.
        Keyword args are available if a type requires them
        """
        self.message = message
        self.server = server
        self.botdata = botdata
        self.client = client
        if message is not None:
            self.server = message.server

        self.error = 0
        self.hr = ""
        self.errmsg = ""
        self.raw = raw
        if userstr is not None:
            self.fromUser(userstr)
            return
        elif raw is not None:
            self.fromRaw(raw)
            return

    def fromRaw(self, raw):
        """
        Initialise from raw data. Probably want to get the human readable version.
        Define both raw value and human readable value
        """
        if not self.error:
            self.raw = raw
            self.hr = self.humanise(raw)
        return self

    def fromUser(self, userstr):
        """
        Initialise from human input. Complicated interpretation involved.
        Probably want to get raw, and possibly human readable.
        """
        if not self.error:
            raw = self.understand(userstr)
            self.fromRaw(raw)
        return self

    def understand(self, userstr):
        """
        This is where the complicated interpretation happens.
        Takes in a user entered string, attempts to turn it into raw data.
        Returns raw data
        Writes the error string if it can't
        """
        pass

    def humanise(self, raw):
        """
        Take in raw data and humanise it to be user readable.
        Can be an alternative to initialising and getting the raw data.
        """
        pass


class BOOL(_settingType):
    """
    A sort of boolean type, more like a wrapper for a boolean.
    """
    name = ""
    accept = "Yes/No, True/False, Enabled/Disabled"
    inputexps = {"^yes$": True,
                 "^true$": True,
                 "^enable[d]$": True,
                 "^no$": False,
                 "^false$": False,
                 "^disable[d]$": False}
    outputs = {True: "",
               False: ""}

    def humanise(self, raw):
        return self.outputs[raw]

    def understand(self, userstr):
        for pattern in self.inputexps:
            if re.match(pattern, userstr, re.I):
                return self.inputexps[pattern]
        self.errmsg = "I don't understand this value. Acceptable values are: {}".format(self.accept)
        self.error = 1
        return None

class YES_BOOL(BOOL):
    name = "Yes/No"
    outputs = {True: "Yes",
               False: "No"}


class ENABLED_BOOL(BOOL):
    name = "Enabled/Disabled"
    outputs = {True: "Enabled",
               False: "Disabled"}


class CHANNEL(_settingType):
    """
    Channel type.
    """
    name = "Channel"
    accept = "Channel mention/id/name"

    def humanise(self, raw):
        """
        Expect raw to be channel id or 0, an empty.
        """
        if raw == 0:
            return "None"
        return "<#{}>".format(raw)

    def understand(self, userstr):
        """
        User can enter a channel mention or an id, or even a name.
        TODO: Check if the channel actually exists given an id.
        """
        userstr = str(userstr)
        chid = userstr.strip('<#!>')
        if chid.isdigit():
            return chid
        if not self.server:
            self.error = 2
            self.errmsg = "No server context, please provide channel id or mention."
            return None
        for ch in self.server.channels:
            if ch.name.lower() == userstr.lower():
                return ch.id
        self.error = 1
        self.errmsg = "I can't find this channel, please provide an id or mention."
        return None


class userList(_settingType):
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


class userBlackList(userList):
    name = "List of users"
    accept = "[+/add | -/remove] <userid/mention>"
    str_already_in_list = "I have already blacklisted this user!"
    str_not_in_list = "I haven't blacklisted this user!"
    str_removed_from_list = "Give them another chance? If you say so. Unblacklisted the user."
    str_added_to_list = "I call this user a foul wretch and will not deal with them again. Blacklisted the user."


class userMasterList(userList):
    name = "List of users"
    accept = "[+/add | -/remove] <userid/mention>"
    str_already_in_list = "This user is already one of my masters!"
    str_not_in_list = "This user is not one of my masters!"
    str_removed_from_list = "I have rejected this master."
    str_added_to_list = "I accept this user as a new master."


class STR(_settingType):
    """
    Just a plain string, nothing special
    """
    name = "string"
    accept = "Any text"

    def humanise(self, raw):
        return "\"{}\"".format(str(raw))

    def understand(self, userstr):
        return userstr


class FMTSTR(STR):
    """
    Formatable string
    TODO: accepted keys in variable from somewhere
    """
    name = "Formatted string"
    accept = "Formatted string, accepted keys are:\n"
    accept += "\t $username$, $mention$, $id$, $tag$, $displayname$, $server$"


class SERVER(_settingType):
    """
    Server type.
    Incomplete.
    """
    name = "server"
    accept = "Server name/ server id"
