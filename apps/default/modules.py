def load_into(bot):
    # Basic bot tools
#    to_load = ["Bot_Admin", "Config", "Meta"]

    # Moderation tools
#    to_load += ["Server_Admin", "Server_Logging", "Server_Moderation"]

    # Maths
#    to_load += ["Maths", "Tex"]

    # Utilities
#    to_load += ["Info", "General", "Starboard", "Server_Utils"]
#    to_load = ["Bot_Admin", "Meta"]

 #   modules = ["modules/{}".format(module) for module in to_load]
    bot.load("modules", ignore=["RCS", "__pycache__"])
