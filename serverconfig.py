import conftypes
from configSetting import configSetting


serv_conf = {}
"""
TBD: Fully modifiable strings with defaults
"""
serv_conf["join"] = {}
serv_conf["join"]["enabled"] = configSetting("join_msgs_enabled", "Enables/Disables join messages", "server_manager", "server_manager", conftypes.BOOL, False)
serv_conf["join"]["msg"] = configSetting("join_msgs_msg", "Message to post when a user joins", "server_manager", "server_manager", conftypes.FMTSTR, "Give a warm welcome to $user!")
serv_conf["join"]["channel"] = configSetting("join_msgs_channel", "Channel to post in when user joins", "server_manager", "server_manager", conftypes.CHANNEL, 0)
serv_conf["join"]["desc"] = "User join message"

serv_conf["leave"] = {}
serv_conf["leave"]["enabled"] = configSetting("leave_msgs_enabled", "Enables/Disables leave messages", "server_manager", "server_manager", conftypes.BOOL, False)
serv_conf["leave"]["msg"] = configSetting("leave_msgs_msg", "Message to post when a user leaves", "server_manager", "server_manager", conftypes.FMTSTR, "Goodbye $user, we hope you had a nice stay!")
serv_conf["leave"]["channel"] = configSetting("leave_msgs_channel", "Channel to post in when user leaves", "server_manager", "server_manager", conftypes.CHANNEL, 0)
serv_conf["leave"]["desc"] = "User leave message"

"""
serv_conf["general"] = {}
serv_conf["general"]["prefix"] = configSetting("prefix", "Custom bot prefix", "server_manager", "server_manager", conftypes.STR, "")
"""
