import conftypes

"""
We will be wanting to do this for user settings as well at some point.
Might not be able to stick with humanise as class method. Or maybe split it up.
What if the setting is a USER? How to humanise the id?
"""


class configSetting:
    def __init__(self, name, perm_view, perm_write, ctype, default):
        self.name = name
        self.perm_view = perm_view
        self.ctype = ctype
        self.default = default

    def set(botdata, server, value):
        """
        Sets setting in botdata
        """
        botdata.servers.set(server, self.name, value)
    def get(botdata, server):
        """
        Returns value of setting from botdata
        """
        return botdata.servers.get(server, self.name)

    def read(botdata, server):
        """
        Gets the value of the setting and returns it in a human readable fashion
        """
        setting = self.get(botdata, server)
        if not setting:
            setting = self.default
        return self.ctype.humanise(setting)

    def write(botdata, server, userstr, message = None, client = None):
        """
        Takes a human written string and attempts to decipher it and write it.
        """
        default_errmsg = "I didn't understand your input or something went wrong!"
        value = self.ctype(userstr=userstr, message=message, server=server, botdata=botdata, client=client)
        if value.error:
            errmsg = value.errmsg if value.errmsg else default_errmsg
            return errmsg
        self.set(botdata, server, value.raw)
        return ""

