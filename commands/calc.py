import json

import aiohttp
from paraCH import paraCH

cmds = paraCH()


@cmds.cmd(
    "calc",
    category="Maths",
    short_help="Calculate short mathematical expressions.")
async def cmd_rotate(ctx):
    """
    Usage:
        {prefix}calc <expr1>
        <expr2>
        <expr3>...
    Description:
        Calculates the provided expressions and returns the result.
        Use newlines to separate distinct expressions. Variables defined in one expression will be remembered in the expressions below.
        Currently uses http://api.mathjs.org/ . See this site for detailed examples of usage.
    Examples:
        {prefix}calc sin(45 deg)
        {prefix}calc det([1, 1; 2, 3])
        {prefix}calc 5 inches to cm
        {prefix}calc a=1
        a/2
    """
    API_ADDR = 'http://api.mathjs.org/v4/'
    if not ctx.arg_str:
        await ctx.reply(
            "Please give me something to evaluate. See help for usage details."
        )
        return
    exprs = ctx.arg_str.split('\n')
    request = {"expr": exprs, "precision": 14}
    async with aiohttp.ClientSession() as session:
        async with session.post(API_ADDR, data=json.dumps(request)) as resp:
            answer = await resp.json()
    if "error" not in answer or "result" not in answer:
        await ctx.reply(
            "Something unknown went wrong, sorry! Could not complete your request."
        )
        return
    if answer["error"]:
        await ctx.reply(
            "The following error occured while calculating:\n`{}`".format(
                answer["error"]))
        return
    await ctx.reply("Result{}:\n```\n{}\n```".format(
        "s" if len(exprs) > 1 else "", "\n".join(answer["result"])))
