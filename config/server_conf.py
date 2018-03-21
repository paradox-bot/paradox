from contextBot.Conf import Conf
from paraSetting import paraSetting

server_conf = Conf("s_conf")



def load_into(bot):
    bot.add_to_ctx(server_conf)
    bot.s_conf = server_conf
