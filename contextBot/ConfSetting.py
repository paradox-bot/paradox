class ConfSetting:
    name = ""
    default = ""

    @classmethod
    async def get(cls, ctx):
        """
        Returns the value of the setting in a usable fashion.
        e.g. if the setting is a list, it runs json.loads.
        """
        pass

    @classmethod
    async def set(cls, ctx, value):
        """
        Takes the setting and munges it into a storable object.
        e.g. if the setting is a list, it runs json.dumps.
        """
        pass

    @classmethod
    async def read(cls, ctx):
        """
        Retrieves the raw value of the setting from the data object.
        This value should be in the same format that write takes.
        The type will almost always be an int or a sring.
        """
        pass

    @classmethod
    async def write(cls, ctx, value):
        """
        Writes a raw value of the seting to the data object.
        Again, the type will likely be an int or a string.
        """
        pass
