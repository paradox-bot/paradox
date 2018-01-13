import discord
import asyncio
import json
import configparser as cfgp

CONFFILE = "paradox.conf"

class Conf(cfgp.ConfigParser):
    section = "General"

    def __init__(self, conffile):
        super().__init__()
        self.read(conffile)

    def kget(self, option):
        return self.get(self.section, option)

    def kgetint(self, option):
        return self.getint(self.section, option)

    def kgetfloat(self, option):
        return self.getfloat(self.section, option)

    def kgetboolean(self, option):
        return self.getboolean(self.section, option)

    def kgetintlist(self, option):
        return json.loads(self.kget(option))



conf = Conf(CONFFILE)
TOKEN = conf.kget("TOKEN")
PREFIX = conf.kget("PREFIX")


client = discord.Client()



@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("Logged into", len(client.servers), "servers")
    

async def reply(message, content):
    await client.send_message(message.channel, content)

client.run(conf.kget("TOKEN"))
