import conftypes
from configSetting import configSetting


server_settings = {}

server_settings["join-msgs-enabled"] = configSetting("join-msgs-enabled", "All", "All", conftypes.BOOL, True)
