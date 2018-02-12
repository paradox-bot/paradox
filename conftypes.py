
"""
Able to initialise from user given string or from raw data.
Main job is to transform between raw data, user string input, visible output, and to give sensible error messages (optional, the configSetting class can have a default) when stuff doesn't look right.
values:
    readable option list/string
    raw
"""
import re

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
        if message:
            self.server = message.server

        self.error = 0
        self.errmsg = ""
        if userstr and raw:
            """
            Someone wants to give us both userstr and raw? We don't handle that.
            """
            self.error = 1
            self.errmsg = "Something is broken inside me."
        elif userstr:
            self.fromUser(userstr)
        elif raw:
            self.fromraw(raw)

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

    @classmethod
    def humanise(cls, raw):
        """
        Take in raw data and humanise it to be user readable.
        Can be an alternative to initialising and getting the raw data.
        """
        pass

"""
A sort of boolean type, more like a wrapper for a boolean.
"""
class BOOL(_settingType):
    name = "Yes/No"
    accept = "Yes/No or True/False"
    inputexps = {
            "^yes$" : True,
            "^true$": True,
            "^no$" : False,
            "^false$" : False
            }
    outputs = {
            True : "Yes",
            False : "No"
            }
    
    @classmethod
    def humanise(cls, raw):
        return cls.outputs[raw]
    
    def understand(self, userstr):
        for pattern in self.inputexps:
            if re.match(pattern, userstr, re.I):
                return self.inputexps[pattern]
        self.errmsg = "I don't understand this value. Acceptable values are: {}".format(self.accept)
        self.error = 1
        return None




"""
Channel type.
"""
class CHANNEL(_settingType):
    name = "Channel"
    accept = "Channel mention/id/name"

    @classmethod
    def humanise(cls, raw):
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


"""
Formatable string
TODO: accepted keys in variable from somewhere
"""
class FMTSTR(_settingType):
    name = "Formatted string"
    accept = "Formatted string, accepted keys are *blah*"
    @classmethod
    def humanise(cls, raw):
        return "\"{}\"".format(str(raw))
    def understand(self, userstr):
        return userstr


"""
Server type.
Incomplete.
"""
class SERVER(_settingType):
    name = "server"
    accept = "Server name/ server id"


