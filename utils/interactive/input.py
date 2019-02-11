import discord


def load_into(bot):
    @bot.util
    async def listen_for(ctx, chars=[], check=None, timeout=30, lower=True):
        if not check:

            def check(message):
                return ((message.content.lower() if lower else message.content) in chars)

        msg = await ctx.bot.wait_for_message(author=ctx.author, check=check, timeout=timeout)
        return msg

    @bot.util
    async def input(ctx, msg, timeout=120):
        offer_msg = await ctx.reply(msg)
        result_msg = await ctx.bot.wait_for_message(author=ctx.author, timeout=timeout)
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
    async def ask(ctx, msg, timeout=30, use_msg=None):
        out = "{} {}".format(msg, "`y(es)`/`n(o)`")
        offer_msg = await ctx.bot.edit_message(use_msg, out) if use_msg else await ctx.reply(out)
        result_msg = await ctx.listen_for(["y", "yes", "n", "no"], timeout=timeout)

        if result_msg is None:
            return None
        result = result_msg.content.lower()
        try:
            if not use_msg:
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
    async def selector(ctx, message, select_from, timeout=120, max_len=20, silent=False):
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
            "{}\n{}\nType the number of your selection or `c` to cancel.".format(message, page)
            for page in ctx.paginate_list(select_from, block_length=max_len)
        ]
        out_msg = await ctx.pager(pages)
        result_msg = await ctx.listen_for([str(i + 1) for i in range(0, len(select_from))] + ["c"], timeout=timeout)
        try:
            await ctx.bot.delete_message(out_msg)
        except discord.NotFound:
            pass
        if not result_msg:
            if not silent:
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
            if not silent:
                await ctx.reply("Cancelled selection.")
            ctx.cmd_err = (-1, "")  # User cancelled or didn't respond
            return None
        return int(result_msg.content) - 1

    @bot.util
    async def silent_selector(ctx, message, select_from, timeout=120, use_msg=None):
        if len(select_from) == 0:
            return None
        if len(select_from) == 1:
            return 0
        page = "{}\n{}\nType the number of your selection or `c` to cancel.".format(
            message,
            ctx.paginate_list(select_from, block_length=50)[0])

        out_msg = await ctx.bot.edit_message(use_msg, page) if use_msg else await ctx.reply(page)
        result_msg = await ctx.listen_for([str(i + 1) for i in range(0, len(select_from))] + ["c"], timeout=timeout)

        if not use_msg:
            try:
                await ctx.bot.delete_message(out_msg)
            except discord.NotFound:
                pass

        if not result_msg:
            return None

        result = result_msg.content
        try:
            await ctx.bot.delete_message(result_msg)
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass
        if result == "c":
            return None
        return int(result_msg.content) - 1

    @bot.util
    async def menu(ctx, items, callback, menu_msg=None, title="Menu", prompt=None, timeout=120):
        menu = {
            "items": items,
            "callback": callback,
            "msg": menu_msg,
            "title": title,
            "timeout": timeout,
            "result": None,
            "prompt": None,
            "done": False
        }

        if "menu" in ctx.objs and not ctx.objs["menu"]["done"]:
            if "menu_stack" not in ctx.objs:
                ctx.objs["menu_stack"] = []
            ctx.objs["menu_stack"].append(ctx.objs["menu"].copy())

        ctx.objs["menu"] = menu

        while True:
            # Print the menu
            nice_list = ctx.paginate_list(menu["items"], title=menu["title"], block_length=50)[0]
            nice_list = "{}\n{}".format(
                nice_list, menu["prompt"] if menu["prompt"] else "Please type your selection number or `c` to go back.")
            menu["msg"] = await ctx.bot.edit_message(
                menu["msg"], nice_list) if menu["msg"] is not None else await ctx.reply(nice_list)

            # Listen for a valid reply
            listening = [str(i + 1) for i in range(0, len(items))]
            listening.append("c")
            result = await ctx.listen_for(listening, timeout=600)

            if result is not None:
                # Attempt to delete the user message
                try:
                    await ctx.bot.delete_message(result)
                except discord.Forbidden:
                    pass
                except discord.NotFound:
                    pass

                result = result.content
                if result != "c":
                    try:
                        await menu["callback"](ctx, int(result) - 1)
                    except ctx.TimedOut:
                        pass
                    except ctx.UserCancelled:
                        pass
                else:
                    # User cancelled
                    menu["result"] = "User Cancelled!"
            else:
                # Timed out waiting for user input
                menu["result"] = "Menu timed out!"

            menu = ctx.objs["menu"]
            if menu["done"] or menu["result"]:
                if "menu_stack" in ctx.objs and ctx.objs["menu_stack"]:
                    ctx.objs["menu"] = ctx.objs["menu_stack"].pop()
                return 0 if menu["done"] else menu["result"]

    @bot.util
    async def outer_menu(ctx, *args, **kwargs):
        try:
            result = await ctx.menu(*args, **kwargs)
            if result != 0:
                await ctx.bot.edit_message(ctx.objs["menu"]["msg"], result)
            else:
                await ctx.bot.delete_message(ctx.objs["menu"]["msg"])
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass

    class TimedOut(Exception):
        pass

    bot.add_to_ctx(TimedOut)

    class UserCancelled(Exception):
        pass

    bot.add_to_ctx(UserCancelled)

    @bot.util
    async def wait_for_string(ctx, max_len=2000, check=None):
        invalid = True
        to_delete = []
        to_return = None

        while invalid:
            output = await ctx.bot.wait_for_message(author=ctx.author, timeout=600, channel=ctx.ch)
            to_delete.append(output)
            if output is None:
                break

            if output.content != "c":
                if check is not None:
                    err = check(ctx, output)
                    if err:
                        to_delete.append(await ctx.reply(err))
                        continue
                if len(output.content) > max_len:
                    to_delete.append(await ctx.reply("This is too long! Please try again."))
                    continue
                else:
                    invalid = False
                    if output.content == "_":
                        to_return = ""
                    else:
                        to_return = output.content
            else:
                invalid = False

        for msg in to_delete:
            try:
                await ctx.bot.delete_message(msg)
            except discord.Forbidden:
                pass
            except discord.NotFound:
                pass

        if invalid:
            raise ctx.TimedOut()
        return to_return
