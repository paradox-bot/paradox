from paraperms import permFuncs

"""
We will be wanting to do this for user settings as well at some point.
Might not be able to stick with humanise as class method. Or maybe split it up.
What if the setting is a USER? How to humanise the id?
TODO: A help string for configSettings and a human readable description. Also categories.
TODO: Permission to view a setting
"""


class _configSetting:
    def __init__(self, name, desc, perm_view, perm_write, ctype, default):
        self.name = name
        self.desc = desc
        self.perm_view = perm_view
        self.perm_write = perm_write
        self.ctype = ctype
        self.default = default

    def set(self, data, obj, value):
        """
        Sets the setting for obj to value and writes to data
        """
        pass

    def get(self, data, obj):
        """
        Gets the setting for obj from data.
        """
        pass

    async def read(self, data, obj, message=None, client=None):
        """
        Gets the value of the setting and returns it in a human readable fashion
        """
        setting = self.get(data, obj)
        if setting is None:
            setting = self.default
        value = self.ctype(raw=setting, client=client, message=message)
        return value.hr

    async def write(self, data, obj, userstr, conf=None, message=None, client=None, server=None, botdata=None):
        """
        Takes a human written string and attempts to decipher it and write it.
        """
        if self.perm_write:
            if (client is None) or (message is None):
                return "Something went wrong while checking whether you have perms to set this setting!"
            (errcode, errmsg) = await permFuncs[self.perm_write][0](client, data, message=message, conf=conf)
            if errcode != 0:
                return errmsg
        default_errmsg = "I didn't understand your input or something went wrong!"
        value = self.ctype(raw=self.get(data, obj), userstr=userstr, message=message, server=server, botdata=botdata, client=client)
        errmsg = value.errmsg
        if value.error:
            errmsg = value.errmsg if value.errmsg else default_errmsg
            return errmsg
        self.set(data, obj, value.raw)
        return errmsg


class serverConfigSetting(_configSetting):
    def __init__(self, name, category, desc, perm_view, perm_write, ctype, default):
        super().__init__(name, desc, perm_view, perm_write, ctype, default)
        self.cat = category

    def set(self, botdata, server, value):
        """
        Sets setting in botdata
        """
        botdata.servers.set(server.id, self.name, value)

    def get(self, botdata, server):
        """
        Returns value of setting from botdata
        """
        setting = botdata.servers.get(server.id, self.name)
        return setting if (setting is not None) else self.default

    async def write(self, data, obj, userstr, message=None, client=None, server=None, botdata=None, conf=None):
        server = obj
        botdata = data
        return (await super().write(data, obj, userstr, message=message, client=client, server=server, botdata=botdata, conf=conf))


class botConfigSetting(_configSetting):
    def set(self, botconf, cat=None, value=""):
        """
        Sets setting in botconf, cat is a placeholder
        """
        botconf.set(self.name, value)

    def get(self, botconf, cat=None):
        """
        Returns value of setting from botconf, cat is again a placeholder
        """
        setting = botconf.get(self.name)
        return setting if (setting is not None) else self.default

    async def write(self, data, obj, userstr, message=None, client=None, server=None, botdata=None, conf=None):
        conf = data
        return (await super().write(data, obj, userstr, message=message, client=client, server=server, botdata=botdata, conf=conf))
