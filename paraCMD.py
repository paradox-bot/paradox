from contextBot.Command import Command
import re
import textwrap


class paraCMD(Command):
    def __init__(self, name, func, CH, aliases=[], **kwargs):
        super().__init__(name, func, CH, **kwargs)
        self.parse_help()
        self.aliases = aliases
        self.flags = kwargs["flags"] if "flags" in kwargs else None
        self.edit_handler = kwargs.get("edit_handler", None)

    async def run(self, ctx):
        if self.flags:
            (params, arg_str, flags) = await ctx.parse_flags(ctx.arg_str, self.flags)
            ctx.flags = flags
            ctx.params = params
            ctx.arg_str = arg_str

        await super().run(ctx)

    def parse_help(self):
        lines = self.long_help.split("\n")
        help_fields = []
        field = ""
        field_name = ""
        table_field = False
        for i in range(0, len(lines)):
            if re.match(r"^.*:[0-9]?$", lines[i]):
                if field_name and field:
                    help_fields.append((field_name, field + ("" if table_field else "\n```")))
                    table_field = False
                if re.match(r"^.*:[0-9]$", lines[i]):
                    field_name = lines[i][:-2]
                    field_len = int(lines[i][-1])
                    table_field = True
                    field = ""
                else:
                    field_name = lines[i][:-1]
                    field = "```\n"
            else:
                if table_field:
                    if "::" in lines[i]:
                        row = lines[i].strip().split("::")
                        row_name, row_content = row
                        field += "`​{}{}`: {}\n".format(" " * (field_len - len(row_name)), row_name, row_content)
                else:
                    field += lines[i].strip() + "\n"
        if field_name and field:
            help_fields.append((field_name, field + ("" if table_field else "\n```")))
        self.help_fields = list(map(lambda f: (f[0], (textwrap.dedent(f[1])).strip()), help_fields))
