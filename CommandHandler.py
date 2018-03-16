from Command import Command


class CommandHandler:
    name = "global"
    snippets = {}
    checks = {}
    cmds = {}
    priority = 0

    def __init__():
        pass

    # Command loading

    def load_into(self, bot):
        """
        Loads the commands associated to this command handler object into bot.

        bot (BotContext): The global bot context to load the commands into.
        """
        bot.cmd_cache = bot.cmd_cache + self.cmds
        if self.name in bot.handler_list:
            bot.handlers[self.name].append(self)
            bot.handlers.sort(key=lambda CH: CH.priority)
        return bot

    def append(self, CH):
        """
        Appends the commands from another CH object into this one.

        CH (CommandHandler): The command handler object to load in.
        """
        for cmd in CH.cmds:
            cmd.handler = self
            self.cmds.append(cmd)

    # Global rules for building command

    def before_exec(ctx):
        """
        code to run befoe any command is executed.

        ctx (messagecontext): context to read and modify.
        """
        pass

    def _after(ctx):
        """
        Code to run after any command is executed.

        ctx (MessageContext): Context to read and modify.
        """
        pass

    def after_exec(ctx):
        """
        Executes after command completes, before any on_* methods.

        ctx (MessageContext): Context to read and modify.
        """
        pass

    def on_error(ctx):
        """
        Runs if the ctx.cmd_err context flag is set.

        ctx (MessageContext): Context to read and modify.
        """
        pass

    def on_fail(ctx):
        """
        Runs if the command fails (i.e. we catch an exception)

        ctx (MessageContext): Context to read and modify.
        Expects ctx.cmd_exception to be set.
        """
        pass

    def on_complete(ctx):
        """
        Runs if the command completes (regardless of error status).
        Executes after "after_exec" and "on_error".

        ctx (MessageContext): Context to read and modify.
        """
        pass

    # Building command object

    def build_cmd(self, name, func, **kwargs):
        """
        Builds a command from a command function.
        Builds using the rules defined in the class, no local rules.
        All local rules should be specified by the decorators.

        func (async Function): function to build into a command object.
        """
        def cmd(ctx, **kwargs):
            self.before(ctx)
            try:
                func(ctx, **kwargs)
            except Exception:


        return Command(name, func, self, **kwargs)
        pass

    def help_fmt(help_str):
        """
        Holds the rules for building a help format string.

        help_str (Str): Naked user-written help stirng.
        """
        pass

    # Decorators for command specification

    def cmd(self, name, **kwargs):
        """
        Decorator for a command function.
        Defines command data, builds the command object, adds it to cmds.

        name (Str): Name of the command.
        short_help (Str): Short help or description. Not set.
            (Define the default for this in the help command, or globally).
        aliases (strlist): List of global aliases.
        category (str): command category name.
        """
        def decorator(func):
            cmd = self.build_cmd(name, func, **kwargs)
            self.cmds.append(cmd)
            return func

        pass

    def require(req_str):
        """
        Decorator to add a required "check" to a command function from checks.

        req_str (String): Name of the check function in the check dict.
        """
        def decorator(func):
            def wrapper(**kwargs):

        pass

    def execute(snip):
        """
        Decorator to run a snippet before a command function executes.

        snip (String): name of the snippet to execute.
        """

    def after(snip):
        """
        Decorator to add a snippet to execute after function completes.
        Note that this is executed regardless of exit status.

        snip (String): name of the snippet to execute.
        """
        pass
