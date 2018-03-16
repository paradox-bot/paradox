from contextBot.CommandHandler import CommandHandler
from contextBot.Command import Command

from snippets import snippets
from checks import checks


class paraCH(CommandHandler):
    name = "General commands"
    snippets = snippets
    checks = checks
    priority = 1
    CmdCls = Command
