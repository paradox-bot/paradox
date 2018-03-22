from contextBot.ConfSetting import ConfSetting
from checks import checks
from functools import wraps


class paraSetting(ConfSetting):
    name = ""  # Name used to describe the setting in data, and how the setting is retireved
    vis_name = ""  # Visible name shown to user in, say, configuration list
    hidden = False  # Whether this setting is hidden from the configuration lists
    default = ""  # What the default value is. Returned by read when no value is found
    desc = ""  # Human readable description of the setting.
    accept = ""  # Human readable string describing what the acceptable values are.
    category = ""  # Setting category

    write_perm = "has_manage_server"  # Require to pass this check before reading a setting
    read_perm = None  # TODO

    checks = checks  # Default checks dict is just checks

    # The logic to understand human input strings and turn raw values into human readable strings.

    @classmethod
    async def humanise(cls, ctx, raw):
        """
        Takes a value and makes it human readable.
        """
        pass

    @classmethod
    async def understand(cls, ctx, userstr):
        """
        Takes a human entered string, attempts to make it a value.
        May set ctx.cmd_err on failure.
        """
        pass

    # Getting and setting human readable versions of the setting

    @classmethod
    async def hr_get(cls, ctx):
        """
        Returns a human readable value.
        """
        value = await cls.get(ctx)
        return await cls.humanise(ctx, value)

    @classmethod
    async def hr_set(cls, ctx, value):
        """
        Attempts to set a value from user input
        """
        if cls.write_perm:
            await cls.checks[cls.write_perm](ctx)
            if ctx.cmd_err[0]:
                return ctx.cmd_err[0]
        value = await cls.understand(ctx, value)
        return ctx.cmd_err[0] if ctx.cmd_err[0] else (await cls.set(ctx, value))

    # Methods to obtain and set internally useable values

    @classmethod
    async def get(cls, ctx):
        """
        Obtains a raw value using read, returns a useable value
        """
        raw = await cls.read(ctx)
        return raw if raw else (await cls.dyn_default(ctx))

    @classmethod
    async def set(cls, ctx, value):
        """
        Takes a value, makes it raw, and sets it.
        """
        raw = value  # Most values should be understood by the db interface, so we can send it on
        return await cls.write(ctx, raw)

    # Helper functions for setting info

    @classmethod
    async def dyn_default(cls, ctx):
        """
        This is for setting a "dynamic default".
        If the default value for say the prefix relies on context,
        this method may be use to retrieve it.
        """
        return cls.default

    @classmethod
    def require(cls, check, **check_kwargs):
        """
        A decorator for adding a required check to a function.
        """
        def decorator(func):
            nonlocal check
            if check not in cls.checks:
                async def unknown_check(ctx, **kwargs):
                    await ctx.log("Attempted to run the check {} which does not exist".format(check))
                    return ("3", "There was an internal error: ERR_BAD_CONF_CHECK")
                check = unknown_check
            else:
                check = cls.checks[check]

            @wraps(func)
            async def wrapper(cls, ctx, *argv, **kwargs):
                (err_code, err_msg) = await check(ctx, **check_kwargs)
                if not err_code:
                    await func(cls, ctx, *argv, **kwargs)
                else:
                    ctx.cmd_err = (err_code, err_msg)
            return wrapper
        return decorator
