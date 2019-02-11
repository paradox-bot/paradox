import discord


def load_into(bot):
    @bot.util
    async def listen_for(ctx, chars=[], check=None, timeout=30, lower=True):
        if not check:

            def check(message):
                return ((message.content.lower()
                         if lower else message.content) in chars)

        msg = await ctx.bot.wait_for_message(
            author=ctx.author, check=check, timeout=timeout)
        return msg

    @bot.util
    async def input(ctx, msg, timeout=120):
        offer_msg = await ctx.reply(msg)
        result_msg = await ctx.bot.wait_for_message(
            author=ctx.author, timeout=timeout)
        if result_msg is None:
            return None
        result = result_msg.content
        try:
            await ctx.bot.delete_message(offer_msg)
            await ctx.bot.delete_message(result_msg)
        except Exception:
            pass
        return result

    @bot.util
    async def ask(ctx, msg, timeout=30):
        offer_msg = await ctx.reply(msg + " `y(es)`/`n(o)`")
        result_msg = await ctx.listen_for(["y", "yes", "n", "no"],
                                          timeout=timeout)
        if result_msg is None:
            return None
        result = result_msg.content.lower()
        try:
            await ctx.bot.delete_message(offer_msg)
            await ctx.bot.delete_message(result_msg)
        except Exception:
            pass
        if result in ["n", "no"]:
            return 0
        return 1

    @bot.util
    async def exchange(ctx, questions, callback):
        """
        Begins an interactive exchange.
        Questions is a list of tuples with a specific format:
            (question, default)
        callback is a coroutine which takes the responses dict and context at each response.
        Meant for updating.
        This method handles the routine wok of going back and forth, cancelling, etc.
        """

    @bot.util
    async def selector(ctx, message, select_from, timeout=120, max_len=20):
        """
        Interactive method to ask the user to select an entry from a list.
        Returns the index of the list which was selected,
        or None if the request timed out or was cancelled.
        TODO: Some sort of class integration for paging.

        list select_from: List to select from
        """
        if len(select_from) == 0:
            return None
        if len(select_from) == 1:
            return 0
        pages = [
            "{}\n{}\nType the number of your selection or `c` to cancel.".
            format(message, page)
            for page in ctx.paginate_list(select_from, block_length=max_len)
        ]
        out_msg = await ctx.pager(pages)
        result_msg = await ctx.listen_for(
            [str(i + 1) for i in range(0, len(select_from))] + ["c"],
            timeout=timeout)
        try:
            await ctx.bot.delete_message(out_msg)
        except discord.NotFound:
            pass
        if not result_msg:
            await ctx.reply("Question timed out, aborting...")
            ctx.cmd_err = (-1, "")  # User cancelled or didn't respond
            return None
        result = result_msg.content
        try:
            await ctx.bot.delete_message(result_msg)
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass
        if result == "c":
            await ctx.reply("Cancelled selection.")
            ctx.cmd_err = (-1, "")  # User cancelled or didn't respond
            return None
        return int(result_msg.content) - 1
