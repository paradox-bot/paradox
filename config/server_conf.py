from contextBot.Conf import Conf
from paraSetting import paraSetting

server_conf = Conf("s_conf")


@server_conf.Setting
class Server_Setting_Prefix(paraSetting):
    name = "prefix"
    vis_name = "prefix"
    hidden = False
    default = ""
    desc = "Custom server prefix"


def load_into(bot):
    bot.add_to_ctx(server_conf)
    bot.s_conf = server_conf
