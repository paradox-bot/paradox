class Command:
    def __init__(name, func, short_help=None, long_help=None, CH=CH):
        self.name = name
        self.func = func
        self.short_help = short_help
        self.long_help = long_help
        self.handler = CH

    def run(cmd_ctx):
        self.func(cmd_ctx)


