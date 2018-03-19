import asyncio
import subprocess
import datetime


def load_into(bot):
    @bot.util
    def strfdelta(self, delta, sec = False):
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
    async def run_sh(self, to_run):
        """
        Runs a command asynchronously in a subproccess shell.
        """
        process = await asyncio.create_subprocess_shell(to_run, stdout=asyncio.subprocess.PIPE)
        if self.bot.DEBUG > 1:
            await self.log("Running the shell command:\n{}\nwith pid {}".format(to_run, str(process.pid)))
        stdout, stderr = await process.communicate()
        if self.bot.DEBUG > 1:
            await self.log("Completed the shell command:\n{}\n{}".format(to_run, "with errors." if process.returncode != 0 else ""))
        return stdout.decode().strip()

    @bot.util
    async def tail(self, filename, n):
        p1 = subprocess.Popen('tail -n ' + str(n) + ' ' + filename,
                            shell=True, stdin=None, stdout=subprocess.PIPE)
        out, err = p1.communicate()
        p1.stdout.close()
        return out.decode('utf-8')

    @bot.util
    def convdatestring(self, datestring):
        datestring = datestring.strip(' ,')
        datearray = []
        funcs = {'d' : lambda x: x * 24 * 60 * 60,
                'h' : lambda x: x * 60 * 60,
                'm' : lambda x: x * 60,
                's' : lambda x: x}
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
