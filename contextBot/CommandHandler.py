from contextBot.Command import Command

from functools import wraps

import traceback
import discord


class CommandHandler:
    name = "global"
    snippets = {}
    checks = {}
    priority = 0
    CmdCls = Command

    def __init__(self):
        self.cmds = {}

    def __repr__(self):
        return "\"{}\" command handler with {} commands".format(self.name, len(self.cmds))
    # Command loading

    def load_into(self, bot):
        """
        Loads the commands associated to this command handler object into bot.

        bot (BotContext): The global bot context to load the commands into.
        """
        if bot.DEBUG > 0:
            bot.sync_log(bot.loading_leader+"Loading {1} commands into command handler \"{0}\"".format(self.name,
                                                                                                       len(list(self.cmds.keys()))))
        elif bot.DEBUG > 2:
            bot.sync_log(bot.loading_leader+"Loading command handler \"{}\" with commands {}".format(self.name,
                                                                                                     str(list(self.cmds.keys()))))
        bot.cmd_cache = [*(bot.cmd_cache), *(self.cmds.keys())]

        for CH in bot.handlers:
            if CH.name == self.name:
                CH.append(self)
                bot.handlers.sort(key=lambda CH: CH.priority)
                return bot
        bot.handlers.append(self)
        bot.handlers.sort(key=lambda CH: CH.priority)
        return bot

    def append(self, CH):
        """
        Appends the commands from another CH object into this one.

        CH (CommandHandler): The command handler object to load in.
        """
        for cmd in CH.cmds:
            CH.cmds[cmd].handler = self
            self.cmds[cmd] = CH.cmds[cmd]

    async def get_cmds(self, ctx):
        return self.cmds

    async def is_cmd(self, ctx, cmd_name):
        return cmd_name in self.cmds

    async def get_cmd(self, ctx, cmd_name):
        return self.cmds[cmd_name] if cmd_name in self.cmds else None
    # Global rules for building command

    async def before_exec(self, ctx):
        """
        Code to run before any command is executed.

        ctx (messagecontext): context to read and modify.
        """
        pass

    async def _after(self, ctx):
        """
        Code to run after any command is executed.

        ctx (MessageContext): Context to read and modify.
        """
        pass

    async def after_exec(self, ctx):
        """
        Executes after command completes, before any on_* methods.

        ctx (MessageContext): Context to read and modify.
        """
        pass

    async def on_error(self, ctx):
        """
        Runs if the ctx.cmd_err context flag is set.

        ctx (MessageContext): Context to read and modify.
        """
        await ctx.log("Caught a command error with code {0[0]} and message \"{0[1]}\"".format(ctx.cmd_err))
        if ctx.cmd_err[1] != "":
            await ctx.reply(ctx.cmd_err[1])

    async def on_fail(self, ctx):
        """
        Runs if the command fails (i.e. we catch an exception)

        ctx (MessageContext): Context to read and modify.
        Expects ctx.cmd_err to be set.
        """
        if isinstance(ctx.err[1], discord.Forbidden):
            if ctx.cmd_err[0] != 1:
                try:
                    await ctx.reply("I just attempted to do something I don't have permissions for in this server! Aborting!")
                except discord.Forbidden:
                    pass
            else:
                await ctx.log("There was a permission error running the command \n{}".format(ctx.cmd.name, ctx.err[2]))
        else:
            await ctx.reply("Something went wrong while running your command. The error has been logged and will be fixed soon!")
            await ctx.log("There was an exception while running the command \n{}\nStack trace:{}".format(ctx.cmd.name, ctx.err[2]))
            if ctx.bot.DEBUG > 0:
                await ctx.reply("Stack trace:\n```{}```".format(ctx.err[2]))

    async def on_complete(self, ctx):
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
        @wraps(func)
        async def cmd(ctx, **kwargs):
            await self.before_exec(ctx)
            if ctx.cmd_err[0] != 0:
                await self.on_error(ctx)
                await self._after(ctx)
                return
            try:
                await func(ctx, **kwargs)
            except Exception as e:
                trace = traceback.format_exc()
                ctx.err = (1, e, trace)
                await self.on_fail(ctx)
                return
            finally:
                await self.after_exec(ctx)
                await self._after(ctx)
            if ctx.cmd_err[0]:
                await self.on_error(ctx)
            await self.on_complete(ctx)

        return self.CmdCls(name, cmd, self, **kwargs)

    def help_fmt(self, help_str):
        """
        Holds the rules for building a help format string.

        help_str (Str): Naked user-written help stirng.
        """
        return "```"+help_str+"```"

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
            self.cmds[name] = cmd
            return func
        return decorator

    def require(self, req_str, **checkargs):
        """
        Decorator to add a required "check" to a command function from checks.

        req_str (String): Name of the check function in the check dict.
        """
        def decorator(func):
            if req_str not in self.checks:
                async def unknown_check(ctx, **checkargs):
                    await ctx.log("Attempted to run the check {} which does not exist".format(req_str))
                    return ("3", "There was an internal error: ERR_BAD_CHECK")
                check = unknown_check
            else:
                check = self.checks[req_str]

            @wraps(func)
            async def wrapper(ctx, **kwargs):
                (err_code, err_msg) = await check(ctx, **checkargs)
                if not err_code:
                    await func(ctx, **kwargs)
                else:
                    ctx.cmd_err = (err_code, err_msg)
            return wrapper
        return decorator

    def execute(self, snip, **snipargs):
        """
        Decorator to run a snippet before a command function executes.

        snip (String): name of the snippet to execute.
        """
        def decorator(func):
            if snip not in self.snippets:
                async def unknown_snip(ctx, **kwargs):
                    await ctx.log("Attempted to run the snippet {} which does not exist".format(snip))
                    ctx.cmd_err = ("3", "There was an internal error: ERR_BAD_SNIP")
                    return
                snippet = unknown_snip
            else:
                snippet = self.snippets[snip]

            @wraps(func)
            async def wrapper(ctx, **kwargs):
                await snippet(ctx, **snipargs)
                if not ctx.cmd_err[0]:
                    await func(ctx, **kwargs)
                else:
                    return
            return wrapper
        return decorator

    def after(self, snip, **kwargs):
        """
        Decorator to add a snippet to execute after function completes.
        Note that this is executed regardless of exit status.

        snip (String): name of the snippet to execute.
        """
        def decorator(func):
            if snip not in self.snippets:
                async def unknown_snip(ctx, **kwargs):
                    await ctx.log("Attempted to run the snippet {} which does not exist".format(snip))
                    ctx.cmd_err = ("3", "There was an internal error: ERR_BAD_SNIP")
                    return
                snippet = unknown_snip
            else:
                snippet = self.snippets[snip]
            snipargs = kwargs

            @wraps(func)
            async def wrapper(ctx, **kwargs):
                await func(ctx, **kwargs)
                await snippet(ctx, **snipargs)
            return wrapper
        return decorator
