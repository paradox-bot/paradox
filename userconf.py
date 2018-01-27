'''
    Provides a UserConf class.
    Currently a basic implementation using INF files and JSON
    TODO: Update to using a database (tinysql etc), but keep approximately the same interface.
'''
import configparser as cfgp
import json
import os

class UserConf:
    userSection = 'USERS'
    def __init__(self, conffile):
        self.conffile = conffile
        if not os.path.isfile(conffile):
            with open(conffile, 'a+') as configfile:
                configfile.write('')
        config = cfgp.ConfigParser()
        config.read(conffile)
        if self.userSection not in config.sections():
            config[self.userSection] = {}
        self.users = config[self.userSection]
        self.config = config
    def get(self, userid, prop):
        if str(userid) not in self.users:
            self.users[str(userid)] = '{}'
        user = json.loads(self.users[str(userid)])
        return user.get(prop, None)
    def getintlist(self, userid, prop):
        value = self.get(userid, prop)
        return value if value is not None else []
    def getStr(self, userid, prop):
        value = self.get(userid, prop)
        return value if value is not None else ""
    def set(self, userid, prop, value):
        if str(userid) not in self.users:
            self.users[str(userid)] = "{}"
        user = json.loads(self.users[str(userid)])
        user[prop] = value
        self.users[str(userid)] = json.dumps(user)
        self.write()
    def write(self):
        with open(self.conffile, 'w') as configfile:
            self.config.write(configfile)
