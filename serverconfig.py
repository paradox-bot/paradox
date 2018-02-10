import conftypes
from configSetting import configSetting


server_settings = {}
"""
TBD: Fully modifiable strings with defaults
"""
server_settings["join"] = configSetting("join", "All", "All", conftypes.BOOL, True)
