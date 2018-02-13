import conftypes
from configSetting import botConfigSetting

bot_conf = {}

bot_conf["masters"] = botConfigSetting("masters", "My Owners!", "", "master",
                                       conftypes.userMasterList, "[]")

bot_conf["blacklist"] = botConfigSetting("blacklisted_users", "The users I have blacklisted!", "", "master",
                                         conftypes.userBlackList, "[]")
