from contextBot.Conf import Conf
from paraSetting import paraSetting
import settingTypes

server_conf = Conf("s_conf")

# TODO can do the write check with what's


class Server_Setting(paraSetting):
    @classmethod
    async def read(cls, ctx):
        value = await ctx.data.servers.get(ctx.server.id, cls.name)
        return value

    @classmethod
    async def write(cls, ctx, value):
        (code, msg) = await ctx.CH.checks["in_server_has_mod"](ctx)
        if code != 0:
            ctx.cmd_err = (code, msg)
            return
        return await ctx.data.servers.set(ctx.server.id, cls.name, value)


@server_conf.setting
class Server_Setting_Prefix(Server_Setting, settingTypes.STR):
    name = "texit_guild_prefix"
    vis_name = "prefix"
    desc = "Custom server prefix"
    category = "Guild settings"

    @classmethod
    async def dyn_default(cls, ctx):
        return ctx.bot.prefix


@server_conf.setting
class Server_Setting_Autorole(Server_Setting, settingTypes.ROLE):
    name = "guild_autorole"
    vis_name = "autorole"
    desc = "Role automatically given to new members"
    category = "Guild settings"
    default = "0"


@server_conf.setting
class Server_Setting_Autorole_Bot(Server_Setting, settingTypes.ROLE):
    name = "guild_autorole_bot"
    vis_name = "autorole_bot"
    desc = "Role automatically given to new bots. By default same as autorole."
    category = "Guild settings"

    @classmethod
    async def dyn_default(cls, ctx):
        return await ctx.server_conf.guild_autorole.get(ctx)


@server_conf.setting
class Server_Setting_selfroles(Server_Setting, settingTypes.ROLELIST):
    name = "self_roles"
    vis_name = "selfroles"
    desc = "Roles which users can give themselves with giveme command"
    default = None
    category = "Guild settings"

# Moderation settings


@server_conf.setting
class Server_Setting_modlog_ch(Server_Setting, settingTypes.CHANNEL):
    name = "modlog_ch"
    vis_name = "modlog_ch"
    desc = "Channel to report moderation events in"
    default = None
    category = "Moderation"


@server_conf.setting
class Server_Setting_modrole(Server_Setting, settingTypes.ROLE):
    name = "mod_role"
    vis_name = "modrole"
    desc = "Role required to use moderation commands"
    default = None
    category = "Moderation"


@server_conf.setting
class Server_Setting_mute_role(Server_Setting, settingTypes.ROLE):
    name = "mute_role"
    vis_name = "mute_role"
    desc = "Role given to mute users (automatically set, but can be overridden)"
    default = None
    category = "Moderation"

# Join and leave message settings


@server_conf.setting
class Server_Setting_Join(Server_Setting, settingTypes.BOOL):
    name = "join_msgs_enabled"
    vis_name = "join"
    desc = "Enables/Disables join messages"
    default = False
    category = "Join message"

    outputs = {True: "Enabled",
               False: "Disabled"}


@server_conf.setting
class Server_Setting_Join_Msg(Server_Setting, settingTypes.FMTSTR):
    name = "join_msgs_msg"
    vis_name = "join_msg"
    desc = "Join message"
    default = "Give a warm welcome to $mention$!"
    category = "Join message"


@server_conf.setting
class Server_Setting_Join_Ch(Server_Setting, settingTypes.CHANNEL):
    name = "join_ch"
    vis_name = "join_ch"
    desc = "Channel to post in when a user joins"
    default = None
    category = "Join message"


@server_conf.setting
class Server_Setting_Leave(Server_Setting, settingTypes.BOOL):
    name = "leave_msgs_enabled"
    vis_name = "leave"
    desc = "Enables/Disables leave messages"
    default = False
    category = "Leave message"

    outputs = {True: "Enabled",
               False: "Disabled"}


@server_conf.setting
class Server_Setting_Leave_Msg(Server_Setting, settingTypes.FMTSTR):
    name = "leave_msgs_msg"
    vis_name = "leave_msg"
    desc = "Leave message"
    default = "Goodbye $username$, we hope you had a nice stay!"
    category = "Leave message"


@server_conf.setting
class Server_Setting_Leave_Ch(Server_Setting, settingTypes.CHANNEL):
    name = "leave_ch"
    vis_name = "leave_ch"
    desc = "Channel to post in when a user leaves"
    default = None
    category = "Leave message"


# Maths related settings

@server_conf.setting
class Server_Setting_Latex_Listen(Server_Setting, settingTypes.BOOL):
    name = "texit_latex_listen_enabled"
    vis_name = "latex"
    desc = "Enables/Disables listening for LaTeX messages"
    default = False
    category = "Mathematical settings"

    outputs = {True: "Enabled",
               False: "Disabled"}

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        listens = ctx.bot.objects["server_tex_listeners"]
        if value and not (ctx.cmd_err and ctx.cmd_err[0] != 0):
            channels = await ctx.bot.data.servers.get(ctx.server.id, "texit_maths_channels")
            listens[str(ctx.server.id)] = channels if channels else []
        else:
            listens.pop(ctx.server.id)
        return result


@server_conf.setting
class Server_Setting_Maths_Channels(Server_Setting, settingTypes.CHANNELLIST):
    name = "texit_maths_channels"
    vis_name = "latex_channels"
    desc = "Only listen to LaTeX in these channels, if set"
    category = "Mathematical settings"
    default = None

    @classmethod
    async def humanise(cls, ctx, raw):
        if not raw:
            return "All channels"
        return await super().humanise(ctx, raw)

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        listens = ctx.bot.objects["server_tex_listeners"]
        if (ctx.cmd_err and ctx.cmd_err[0] != 0):
            return
        if ctx.server.id not in listens:
            return
        listens[ctx.server.id] = value if value else []
        return result


def load_into(bot):
    bot.add_to_ctx(server_conf, name="server_conf")
    bot.s_conf = server_conf
