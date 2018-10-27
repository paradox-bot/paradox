import asyncio
import subprocess
import datetime
import discord
import re


def load_into(bot):

    @bot.util
    def strfdelta(ctx, delta, sec=False):
        output = [[delta.days, 'day'],
                  [delta.seconds // 3600, 'hour'],
                  [delta.seconds // 60 % 60, 'minute']]
        if sec:
            output.append([delta.seconds % 60, 'second'])
        for i in range(len(output)):
            if output[i][0] != 1:
                output[i][1] += 's'
        reply_msg = ''
        if output[0][0] != 0:
            reply_msg += "{} {} ".format(output[0][0], output[0][1])
        for i in range(1, len(output)-1):
            reply_msg += "{} {} ".format(output[i][0], output[i][1])
        reply_msg += "and {} {}".format(output[len(output)-1][0], output[len(output)-1][1])
        return reply_msg

    @bot.util
    async def run_sh(ctx, to_run):
        """
        Runs a command asynchronously in a subproccess shell.
        """
        process = await asyncio.create_subprocess_shell(to_run, stdout=asyncio.subprocess.PIPE)
        if ctx.bot.DEBUG > 1:
            await ctx.log("Running the shell command:\n{}\nwith pid {}".format(to_run, str(process.pid)))
        stdout, stderr = await process.communicate()
        if ctx.bot.DEBUG > 1:
            await ctx.log("Completed the shell command:\n{}\n{}".format(to_run, "with errors." if process.returncode != 0 else ""))
        return stdout.decode().strip()

    @bot.util
    async def tail(ctx, filename, n):
        p1 = subprocess.Popen('tail -n ' + str(n) + ' ' + filename,
                              shell=True, stdin=None, stdout=subprocess.PIPE)
        out, err = p1.communicate()
        p1.stdout.close()
        return out.decode('utf-8')

    @bot.util
    def convdatestring(datestring):
        datestring = datestring.strip(' ,')
        datearray = []
        funcs = {'d': lambda x: x * 24 * 60 * 60,
                 'h': lambda x: x * 60 * 60,
                 'm': lambda x: x * 60,
                 's': lambda x: x}
        currentnumber = ''
        for char in datestring:
            if char.isdigit():
                currentnumber += char
            else:
                if currentnumber == '':
                    continue
                datearray.append((int(currentnumber), char))
                currentnumber = ''
        seconds = 0
        if currentnumber:
            seconds += int(currentnumber)
        for i in datearray:
            if i[1] in funcs:
                seconds += funcs[i[1]](i[0])
        return datetime.timedelta(seconds=seconds)


    @bot.util
    async def parse_flags(ctx, args, flags=[]):
        """
        Parses flags in args from the flags given in flags.
        Flag formats:
            'a': boolean flag, checks if present.
            'a=': Eats one "word", which may be in quotes
            'a==': Eats all words up until next flag
        Returns a tuple (params, args, flags_present).
        flags_present is a dictionary {flag: value} with value being:
            False if a flag isn't present,
            the value of the flag for a long flag,
        If -- is present in the input as a word, all flags afterwards are ignored.
        TODO: Make this more efficient
        """
        params = args.split(' ')
        final_params = []
        final_flags = {}
        indexes = []
        end_params = []
        if "--" in params:
            end_params = params[params.index("--") + 1:]
            params = params[:params.index("--")]
        for flag in flags:
            clean_flag = flag.strip("=")
            index = None
            if (("-" + clean_flag) in params):
                index = params.index("-" + clean_flag)
            elif (("--" + clean_flag) in params):
                index = params.index("--" + clean_flag)

            if index is None:
                final_flags[clean_flag] = False
                continue
            indexes.append((index, flag))
        indexes = sorted(indexes)
        if len(indexes) > 0:
            final_params = params[0:indexes[0][0]]
        else:
            final_params = params
        for (i, index) in enumerate(indexes):
            if i == len(indexes) - 1:
                flag_arg = " ".join(params[index[0]+1:])
            else:
                flag_arg = " ".join(params[index[0]+1:indexes[i+1][0]])
            flag_arg = flag_arg.strip()
            if index[1].endswith("=="):
                final_flags[index[1][:-2]] = flag_arg
            elif index[1].endswith("="):
                flag_split_arg = flag_arg.split(" ")
                final_flags[index[1][:-1]] = flag_split_arg[0]
                if len(flag_split_arg) > 1:
                    final_params += flag_split_arg[1:]
            else:
                final_flags[index[1]] = True
                final_params += flag_arg.split(" ")
        final_params += end_params
        final_args = " ".join(final_params).strip()
        final_params = final_args.split(" ")
        return (final_params, " ".join(final_params), final_flags)

    @bot.util
    async def emb_add_fields(ctx, embed, emb_fields):
        for field in emb_fields:
            embed.add_field(name=str(field[0]), value=str(field[1]), inline=bool(field[2]))

    @bot.util
    async def get_raw_cmds(ctx):
        handlers = ctx.bot.handlers
        cmds = {}
        for CH in handlers:
            cmds = dict(cmds, **(CH.raw_cmds))
        return cmds

    @bot.util
    async def pager(ctx, pages, embed=False):
        """
        Replies with the first page and provides reactions to page back and forth.
        Reaction timeout is five minutes.
        On timeout, returns the message (for easy deletion).
        pages is either a list of messages or a list of embeds, depending on the embed flag.
        """
        arg = "embed" if embed else "message"
        args = {}
        args[arg] = pages[0]
        out_msg = await ctx.reply(**args)
        if len(pages) == 1:
            return out_msg
        args = {}
        arg = "embed" if embed else "new_content"
        emo_next = ctx.bot.objects["emoji_next"]
        emo_prev = ctx.bot.objects["emoji_prev"]
        page = 0

        def check(reaction, user):
            return (reaction.emoji in [emo_next, emo_prev]) and (not (user == ctx.me))
        try:
            await ctx.bot.add_reaction(out_msg, emo_prev)
            await ctx.bot.add_reaction(out_msg, emo_next)
        except discord.Forbidden:
            await ctx.reply("Cannot page results because I do not have permissions to add emojis!")
            return
        while True:
            res = await ctx.bot.wait_for_reaction(message=out_msg,
                                                  timeout=300,
                                                  check=check)
            if res is None:
                break
            try:
                await ctx.bot.remove_reaction(out_msg, res.reaction.emoji, res.user)
            except discord.Forbidden:
                pass
            page += 1 if res.reaction.emoji == emo_next else -1
            if page == -1:
                page = len(pages) - 1
            if page == len(pages):
                page = 0
            args[arg] = pages[page]
            await ctx.bot.edit_message(out_msg, **args)
        try:
            await ctx.bot.remove_reaction(out_msg, emo_prev, ctx.me)
            await ctx.bot.remove_reaction(out_msg, emo_next, ctx.me)
            await ctx.bot.clear_reactions(out_msg)
        except discord.Forbidden:
            pass
        return out_msg

    @bot.util
    async def from_now(ctx, time_diff):
        now = datetime.datetime.utcnow().timestamp()
        return now + time_diff

    @bot.util
    async def to_tstamp(ctx, days=0, hours=0, minutes=0, seconds=0):
        return seconds + (minutes + (hours + days * 24) * 60) * 60

    @bot.util
    def parse_dur(ctx, time_str):
        funcs = {'d': lambda x: x * 24 * 60 * 60,
                 'h': lambda x: x * 60 * 60,
                 'm': lambda x: x * 60,
                 's': lambda x: x}
        time_str = time_str.strip(" ,")
        found = re.findall(r'(\d+)\s?(\w+?)', time_str)
        seconds = 0
        for bit in found:
            if bit[1] in funcs:
                seconds += funcs[bit[1]](int(bit[0]))
        return datetime.timedelta(seconds=seconds)

