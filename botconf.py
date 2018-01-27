'''
    Extremely rudimentary configuration class.
    Used for grabbing general settings from a file.
    Needs much improvement.
'''
import configparser as cfgp
import json


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

