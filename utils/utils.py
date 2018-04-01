import asyncio
import subprocess
import datetime
import discord


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
    def convdatestring(ctx, datestring):
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
