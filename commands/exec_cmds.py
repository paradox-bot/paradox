import sys
from io import StringIO
import traceback

from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("async",
          category="Bot Admin",
          short_help="Executes async code and displays the output")
@cmds.require("exec_perm")
async def cmd_async(ctx):
    """
    Usage: {prefix}async <code>

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
        traceback.print_exc()
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
        traceback.print_exc()
        result = (str(traceback.format_exc()), 1)
    finally:
        sys.stdout = old_stdout
    return result
