'''
    Extremely rudimentary configuration class.
    Used for grabbing general settings from a file.
    Needs much improvement.
'''
import configparser as cfgp
import json
import os


class Conf:
    Section = 'General'
    def __init__(self, conffile):
        self.conffile = conffile
        if not os.path.isfile(conffile):
            with open(conffile, 'a+') as configfile:
                configfile.write('')
        config = cfgp.ConfigParser()
        config.read(conffile)
        if self.Section not in config.sections():
            config[self.Section] = {}
        self.settings = config[self.Section]
        self.config = config
    def get(self, settingName, default=None):
        if settingName not in self.settings:
            return default
        return self.settings[settingName]
    def getintlist(self, settingName, default = []):
        return json.loads(self.get(settingName, str(default)))
    def getStr(self, settingName, default = ""):
        return self.get(settingName, default)
    def set(self, settingName, value):
        self.settings[settingName] = str(value)
        self.write()
    def write(self):
        with open(self.conffile, 'w') as configfile:
            self.config.write(configfile)

