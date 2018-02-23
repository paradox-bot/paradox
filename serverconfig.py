import conftypes
from configSetting import serverConfigSetting


serv_conf = {}
"""
TBD: Fully modifiable strings with defaults
"""
serv_conf["join"] = serverConfigSetting("join_msgs_enabled", "Join message",
                                                   "Enables/Disables join messages",
                                                   "manage_server",
                                                   "manage_server",
                                                   conftypes.ENABLED_BOOL,
                                                   False)
serv_conf["join_msg"] = serverConfigSetting("join_msgs_msg", "Join message",
                                               "Message to post when a user joins",
                                               "manage_server",
                                               "manage_server",
                                               conftypes.FMTSTR,
                                               "Give a warm welcome to $mention$!")
serv_conf["join_ch"] = serverConfigSetting("join_msgs_channel", "Join message",
                                                   "Channel to post in when user joins",
                                                   "manage_server",
                                                   "manage_server",
                                                   conftypes.CHANNEL,
                                                   0)
# serv_conf["cat Join message"] = "posts a message when a user joins"


serv_conf["leave"] = serverConfigSetting("leave_msgs_enabled", "Leave message",
                                              "Enables/Disables leave messages",
                                              "manage_server",
                                              "manage_server",
                                              conftypes.ENABLED_BOOL,
                                              False)
serv_conf["leave_msg"] = serverConfigSetting("leave_msgs_msg", "Leave message",
                                          "Message to post when a user leaves",
                                          "manage_server",
                                          "manage_server",
                                          conftypes.FMTSTR,
                                          "Goodbye $username$, we hope you had a nice stay!")
serv_conf["leave_ch"] = serverConfigSetting("leave_msgs_channel", "Leave message",
                                              "Channel to post in when user leaves",
                                              "manage_server",
                                              "manage_server",
                                              conftypes.CHANNEL,
                                              0)
# serv_conf["leave_desc"] = "posts a message when a user leaves"


serv_conf["prefix"] = serverConfigSetting("guild_prefix", "Guild settings",
                                             "Custom bot prefix",
                                             "",
                                             "manage_server",
                                             conftypes.STR,
                                             "")
# serv_conf["guild_desc"] = "general guild settings"
