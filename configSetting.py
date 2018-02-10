import conftypes

"""
We will be wanting to do this for user settings as well at some point.
Might not be able to stick with humanise as class method. Or maybe split it up.
What if the setting is a USER? How to humanise the id?
TODO: A help string for configSettings and a human readable description. Also categories.
"""


class configSetting:
    def __init__(self, name, perm_view, perm_write, ctype, default):
        self.name = name
        self.perm_view = perm_view
        self.ctype = ctype
        self.default = default

    def set(self, botdata, server, value):
        """
        Sets setting in botdata
        """
        botdata.servers.set(server.id, self.name, value)
    def get(self, botdata, server):
        """
        Returns value of setting from botdata
        """
        return botdata.servers.get(server.id, self.name)

    def read(self, botdata, server):
        """
        Gets the value of the setting and returns it in a human readable fashion
        """
        setting = self.get(botdata, server)
        if setting == None:
            setting = self.default
        return self.ctype.humanise(setting)

    def write(self, botdata, server, userstr, message = None, client = None):
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

