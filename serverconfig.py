import conftypes
from configSetting import configSetting


server_settings = {}
"""
TBD: Fully modifiable strings with defaults
"""
server_settings["join-msgs-enabled"] = configSetting("join-msgs-enabled", "All", "All", conftypes.BOOL, True)
