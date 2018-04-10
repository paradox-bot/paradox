from contextBot.Command import Command
import re
import textwrap


class paraCMD(Command):
    def __init__(self, name, func, CH, aliases=[], **kwargs):
        super().__init__(name, func, CH, **kwargs)
        self.parse_help()
        self.aliases = aliases

    def parse_help(self):
        lines = self.long_help.split("\n")
        help_fields = []
        field = ""
        field_name = ""
        for i in range(0, len(lines)):
            if re.match(r"^.*:$", lines[i]):
                if field_name and field:
                    help_fields.append((field_name, field))
                field_name = lines[i][:-1]
                field = ""
            else:
                field += lines[i] + "\n"
        if field_name and field:
            help_fields.append((field_name, field))
        self.help_fields = list(map(lambda f: (f[0], (textwrap.dedent(f[1])).strip()), help_fields))
