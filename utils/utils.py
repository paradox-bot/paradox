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
    async def find_user(ctx, user_str, in_server=False, interactive=False, limit=20):
        if user_str == "":
            return None
        maybe_user_id = user_str.strip('<@!> ')

        def is_user(member):
            return ((member.id == maybe_user_id) or
                    (user_str.lower() in member.display_name.lower()) or
                    (user_str.lower() in member.name.lower()))

        collection = ctx.server.members if in_server else ctx.bot.get_all_members
        if interactive:
            users = list(filter(is_user, collection))
            if len(users) == 0:
                return None
            if len(users) > limit:
                await ctx.reply("Over {} users found matching `{}`! Please refine your search".format(limit, user_str))
                ctx.cmd_err = (-1, "")
                return None
            names = ["{} {}".format(user.display_name, ("({})".format(user.name)) if user.nick else "") for user in users]
            selected = await ctx.selector("Multiple users found matching `{}`! Please select one.".format(user_str), names)
            if selected is None:
                return None
            return users[selected]
        else:
            return discord.utils.find(is_user, collection)

    @bot.util
    async def listen_for(ctx, chars=[], timeout=30, lower=True):
        def check(message):
            return ((message.content.lower() if lower else message.content) in chars)
        msg = await ctx.bot.wait_for_message(author=ctx.author, check=check, timeout=timeout)
        return msg

    @bot.util
    async def input(ctx, msg, timeout=120):
        offer_msg = await ctx.reply(msg)
        result_msg = await ctx.bot.wait_for_message(author=ctx.author, timeout=timeout)
        if result_msg is None:
            return None
        result = result_msg.content
        try:
            await ctx.bot.delete_message(offer_msg)
            await ctx.bot.delete_message(result_msg)
        except Exception:
            pass
        return result

    @bot.util
    async def ask(ctx, msg, timeout=30):
        offer_msg = await ctx.reply(msg+" `y(es)`/`n(o)`")
        result_msg = await ctx.listen_for(["y", "yes", "n", "no"])
        if result_msg is None:
            return None
        result = result_msg.content.lower()
        try:
            await ctx.bot.delete_message(offer_msg)
            await ctx.bot.delete_message(result_msg)
        except Exception:
            pass
        if result in ["n", "no"]:
            return 0
        return 1

    @bot.util
    async def offer_create_role(ctx, input):
        offer_msg = await ctx.reply("Would you like to create this role? `y(es)`/`n(o)`")
        result_msg = await ctx.listen_for(["y", "yes", "n", "no"])
        if result_msg is None:
            return None
        result = result_msg.content.lower()
        try:
            await ctx.bot.delete_message(offer_msg)
            await ctx.bot.delete_message(result_msg)
        except Exception:
            pass
        if result in ["n", "no"]:
            return None
        try:
            # TODO: Lots of fancy stuff, move this out to an interactive create role utility
            role = await ctx.bot.create_role(ctx.server, name=input)
        except discord.Forbidden:
            await ctx.reply("Sorry, it seems I don't have permissions to create a role!")
            return None
        await ctx.reply("You have created the role `{}`!".format(input))
        return role

    @bot.util
    async def find_role(ctx, userstr, create=False, interactive=False):
        if not ctx.server:
            ctx.cmd_err = (1, "This is not valid outside of a server!")
            return None
        roleid = userstr.strip('<#@!>')
        if interactive:
            def check(role):
                return (role.id == roleid) or (userstr in role.name)
            roles = list(filter(check, ctx.server.roles))
            if len(roles) == 0:
                role = None
            else:
                selected = await ctx.selector("Multiple roles found! Please select one.",
                                              [role.name for role in roles])
                if selected is None:
                    return None
                role = roles[selected]
        else:
            if roleid.isdigit():
                def is_role(role):
                    return role.id == roleid
            else:
                def is_role(role):
                    return userstr.lower() in role.name.lower()
            role = discord.utils.find(is_role, ctx.server.roles)
        if role:
            return role
        else:
            msg = await ctx.reply("I can't find this role in this server!")
            if create:
                role = await ctx.offer_create_role(userstr)
                if not role:
                    ctx.cmd_err = (1, "Aborting...")
                    return None
                await ctx.bot.delete_message(msg)
                return role
            return None

    @bot.util
    async def selector(ctx, message, select_from, timeout=30):
        """
        Interactive method to ask the user to select an entry from a list.
        Returns the index of the list which was selected,
        or None if the request timed out or was cancelled.
        TODO: Some sort of class integration for paging.

        list select_from: List to select from
        """
        if len(select_from) == 0:
            return None
        if len(select_from) == 1:
            return 0
        lines = ["{:>3}:\t{}".format(i + 1, line) for (i, line) in enumerate(select_from)]
        msg = message
        msg += "```\n"
        msg += "\n".join(lines)
        msg += "```\n"
        msg += "Type the number of your selection or `c` to cancel."
        out_msg = await ctx.reply(msg)
        result_msg = await ctx.listen_for([str(i+1) for i in range(0, len(select_from))] + ["c"], timeout=timeout)
        await ctx.bot.delete_message(out_msg)
        if not result_msg:
            await ctx.reply("Question timed out, aborting...")
            ctx.cmd_err = (-1, "")  # User cancelled or didn't respond
            return None
        result = result_msg.content
        try:
            await ctx.bot.delete_message(result_msg)
        except discord.Forbidden:
            pass
        if result == "c":
            await ctx.reply("Cancelled selection.")
            ctx.cmd_err = (-1, "")  # User cancelled or didn't respond
            return None
        return int(result_msg.content) - 1

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
            embed.add_field(name=field[0], value=field[1], inline=bool(field[2]))
