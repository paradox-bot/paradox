'''
    BotData class, supersceding the old UserConf class.
    Still a basic implementation using INF files and JSON.
    TODO: Update to using a database (tinysql etc), but keep approximately the same interface.
'''

import configparser as cfgp
import json
import os

class BotData:
    userSection = 'USERS'
    serverSection = 'SERVERS'
    def __init__(self, conffile):
        self.conffile = conffile
        if not os.path.isfile(conffile):
            with open(conffile, 'a+') as configfile:
                configfile.write('')
        config = cfgp.ConfigParser()
        config.read(conffile)

        if self.userSection not in config.sections():
            config[self.userSection] = {}
        if self.serverSection not in config.sections():
            config[self.serverSection] = {}

        self.users = _dataManipulator(config[self.userSection], self)
        self.servers = _dataManipulator(config[self.serverSection], self)
        self.config = config

    def write(self):
        with open(self.conffile, 'w') as configfile:
            self.config.write(configfile)

class _dataManipulator:
    def __init__(self, dataArray, master):
        self.data = dataArray
        self.master = master
    def get(self, key, prop):
        if str(key) not in self.data:
            self.data[str(key)] = '{}'
        keyData = json.loads(self.data[str(key)])
        return keyData.get(prop, None)
    def getintlist(self, key, prop):
        value = self.get(key, prop)
        return value if value is not None else []
    def getStr(self, key, prop):
        value = self.get(key, prop)
        return value if value is not None else ""
    def set(self, key, prop, value):
        if str(key) not in self.data:
            self.data[str(key)] = "{}"
        keyData = json.loads(self.data[str(key)])
        keyData[prop] = value
        self.data[str(key)] = json.dumps(keyData)
        master.write()
