def load_into(bot):
    @bot.util
    async def request_reason(ctx, action="ban"):
        reason = await ctx.input("📋 Please provide a reason! (`no` for no reason or `c` to abort {})".format(action))
        if reason.lower() == "no":
            reason = "None"
        elif reason.lower() == "c":
            await ctx.reply("📋 Aborting...")
            return None
        elif reason is None:
            await ctx.reply("📋 Request timed out, aborting.")
            return None
        return reason
