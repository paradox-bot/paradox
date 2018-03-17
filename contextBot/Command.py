import textwrap


class Command:
    def __init__(self, name, func, CH, **kwargs):
        self.name = name
        self.func = func
        self.handler = CH
        self.short_help = kwargs["short_help"] if "short_help" in kwargs else None
        self.long_help = kwargs["long_help"] if "long_help" in kwargs else textwrap.dedent(str(func.__doc__))
        self.category = kwargs["category"] if "category" in kwargs else None
        self.aliases = kwargs["aliases"] if "aliases" in kwargs else None

    def __repr__(self):
        return "Command object for command \"{}\"".format(self.name)

    async def run(self, cmd_ctx):
        await self.func(cmd_ctx)
