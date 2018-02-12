import conftypes
from configSetting import configSetting


serv_conf = {}
"""
TBD: Fully modifiable strings with defaults
"""
serv_conf["join"] = {}
serv_conf["join"]["enabled"] = configSetting("join_msgs_enabled",
                                             "Enables/Disables join messages",
                                             "manage_server",
                                             "manage_server",
                                             conftypes.BOOL,
                                             False)
serv_conf["join"]["msg"] = configSetting("join_msgs_msg",
                                         "Message to post when a user joins",
                                         "manage_server",
                                         "manage_server",
                                         conftypes.FMTSTR,
                                         "Give a warm welcome to $mention$!")
serv_conf["join"]["channel"] = configSetting("join_msgs_channel",
                                             "Channel to post in when user joins",
                                             "manage_server",
                                             "manage_server",
                                             conftypes.CHANNEL,
                                             0)
serv_conf["join"]["desc"] = "User join message"


serv_conf["leave"] = {}
serv_conf["leave"]["enabled"] = configSetting("leave_msgs_enabled",
                                              "Enables/Disables leave messages",
                                              "manage_server",
                                              "manage_server",
                                              conftypes.BOOL,
                                              False)
serv_conf["leave"]["msg"] = configSetting("leave_msgs_msg",
                                          "Message to post when a user leaves",
                                          "manage_server",
                                          "manage_server",
                                          conftypes.FMTSTR,
                                          "Goodbye $user$, we hope you had a nice stay!")
serv_conf["leave"]["channel"] = configSetting("leave_msgs_channel",
                                              "Channel to post in when user leaves",
                                              "manage_server",
                                              "manage_server",
                                              conftypes.CHANNEL,
                                              0)
serv_conf["leave"]["desc"] = "User leave message"


serv_conf["guild"] = {}
serv_conf["guild"]["prefix"] = configSetting("guild_prefix",
                                             "Custom bot prefix",
                                             "",
                                             "manage_server",
                                             conftypes.STR,
                                             "")
"""
serv_conf["general"] = {}
serv_conf["general"]["prefix"] = configSetting("prefix", "Custom bot prefix", "manage_server", "manage_server", conftypes.STR, "")
"""
