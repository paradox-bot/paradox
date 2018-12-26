import sys
from io import StringIO
import traceback
import asyncio
import discord

from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("async",
          category="Bot admin",
          short_help="Executes async code and displays the output")
@cmds.require("exec_perm")
async def cmd_async(ctx):
    """
    Usage:
        {prefix}async <code>
    Description:
        Runs <code> as an asynchronous coroutine and prints the output or error.
    """
    if ctx.arg_str == "":
        await ctx.reply("You must give me something to run!")
        return
    output, error = await _async(ctx)
    await ctx.reply("**Async input:**\
                    \n```py\n{}\n```\
                    \n**Output {}:** \
                    \n```py\n{}\n```".format(ctx.arg_str,
                                             "error" if error else "",
                                             output))


@cmds.cmd("exec",
          category="Bot admin",
          short_help="Executes python code using exec and displays the output",
          aliases=["ex"])
@cmds.require("exec_perm")
async def cmd_exec(ctx):
    """
    Usage:
        {prefix}exec <code>
    Description:
    Runs <code> in current environment using exec() and prints the output or error.
    """
    if ctx.arg_str == "":
        await ctx.reply("You must give me something to run!")
        return
    output, error = await _exec(ctx)
    await ctx.reply("**Exec input:**\
                    \n```py\n{}\n```\
                    \n**Output {}:** \
                    \n```py\n{}\n```".format(ctx.arg_str,
                                             "error" if error else "",
                                             output))


@cmds.cmd("eval",
          category="Bot admin",
          short_help="Executes python code using eval and displays the output",
          aliases=["ev"])
@cmds.require("exec_perm")
async def cmd_eval(ctx):
    """
    Usage:
        {prefix}eval <code>
    Description:
        Runs <code> in current environment using eval() and prints the output or error.
    """
    if ctx.arg_str == "":
        await ctx.reply("You must give me something to run!")
        return
    output, error = await _eval(ctx)
    await ctx.reply("**Eval input:**\
                    \n```py\n{}\n```\
                    \n**Output {}:** \
                    \n```py\n{}\n```".format(ctx.arg_str,
                                             "error" if error else "",
                                             output))


@cmds.cmd("seval",
          category="Bot admin",
          short_help="Silent version of eval.")
@cmds.require("exec_perm")
async def cmd_seval(ctx):
    """
    Usage:
        {prefix}seval <code>
    Description:
        Runs <code> silently in current environment using eval().
    """
    if ctx.arg_str == "":
        await ctx.reply("You must give me something to run!")
        return
    output, error = await _eval(ctx)
    if error:
        await ctx.reply("**Eval input:**\
                        \n```py\n{}\n```\
                        \n**Output (error):** \
                        \n```py\n{}\n```".format(ctx.arg_str,
                                                 output))


@cmds.cmd("shell",
          category="Bot admin",
          short_help="Runs a command in the operating environment.")
@cmds.require("exec_perm")
async def cmd_shell(ctx):
    """
    Usage:
        {prefix}shell <command>
    Description:
        Runs <command> in the operating environment and returns the output in a codeblock.
    """
    if ctx.arg_str == "":
        await ctx.reply("You must give me something to run!")
        return
    output = await ctx.run_sh(ctx.arg_str)
    if len(output) < 1800:
        await ctx.reply("**Command:**\
                        \n```sh\n{}\n```\
                        \n**Output:** \
                        \n```\n{}\n```".format(ctx.arg_str,
                                               output))
    else:
        await ctx.reply("**Command:**\
                        \n```sh\n{}\n```\
                        \n**Output:**".format(ctx.arg_str))
        await ctx.reply("{}".format(output), code=True, split=True)


async def _eval(ctx):
    output = None
    try:
        output = eval(ctx.arg_str)
    except Exception:
        await ctx.bot.log(str(traceback.format_exc()))
        return (str(traceback.format_exc()), 1)
    if asyncio.iscoroutine(output):
        output = await output
    return (output, 0)


async def _exec(ctx):
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    try:
        exec(ctx.arg_str)
        result = (redirected_output.getvalue(), 0)
    except Exception:
        await ctx.bot.log(str(traceback.format_exc()))
        result = (str(traceback.format_exc()), 1)
    finally:
        sys.stdout = old_stdout
    return result


async def _async(ctx):
    env = {'ctx': ctx}
    env.update(globals())
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    exec_string = "async def _temp_exec():\n"
    exec_string += '\n'.join(' ' * 4 + line for line in ctx.arg_str.split('\n'))
    try:
        exec(exec_string, env)
        result = (redirected_output.getvalue(), 0)
    except Exception:
        await ctx.bot.log(str(traceback.format_exc()))
        result = (str(traceback.format_exc()), 1)
    _temp_exec = env['_temp_exec']
    try:
        returnval = await _temp_exec()
        value = redirected_output.getvalue()
        if returnval is None:
            result = (value, 0)
        else:
            result = (value + '\n' + str(returnval), 0)
    except Exception:
        await ctx.bot.log(str(traceback.format_exc()))
        result = (str(traceback.format_exc()), 1)
    finally:
        sys.stdout = old_stdout
    return result
