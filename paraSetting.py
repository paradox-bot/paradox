from contextBot.ConfSetting import ConfSetting
from checks import checks
from functools import wraps

class paraSetting(ConfSetting):
    name = ""
    vis_name = ""
    hidden = False
    default = ""
    desc = ""

    checks = checks

    @classmethod
    async def get(cls, ctx):
        pass

    @classmethod
    async def set(cls, ctx, value):
        pass

    @classmethod
    async def read(cls, ctx):
        value = await ctx.data.get(self.name)
        return (value if value else  (await cls.dyn_default()))

    @classmethod
    async def hr_get(cls, ctx):
        pass

    @classmethod
    async def write(cls, ctx, value):
        return await ctx.data.set(self.name, value)

    @classmethod
    async def dyn_default(cls, ctx):
        return cls.default

    @classmethod
    def require(cls, check):
        def decorator(func):
            if check not in cls.checks:
                async def unknown_check(ctx, **check_kwargs):
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
                    ctx.cmd_err = (err_code,err_msg)
            return wrapper
        return decorator





