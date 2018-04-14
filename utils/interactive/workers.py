import discord


def load_into(bot):
    @bot.util
    async def find_user(ctx, user_str, in_server=False, interactive=False, limit=20, collection=None, is_member=True):
        if user_str == "":
            return None
        maybe_user_id = user_str.strip('<@!> ')
        if is_member:
            def is_user(member):
                return ((member.id == maybe_user_id) or
                        (user_str.lower() in member.display_name.lower()) or
                        (user_str.lower() in member.name.lower()))
        else:
            def is_user(member):
                return ((member.id == maybe_user_id) or
                        (user_str.lower() in member.name.lower()))

        collection = collection if collection else (ctx.server.members if in_server else ctx.bot.get_all_members())
        if interactive:
            users = list(filter(is_user, collection))
            if len(users) == 0:
                return None
            if len(users) > limit:
                await ctx.reply("Over {} users found matching `{}`! Please refine your search".format(limit, user_str))
                ctx.cmd_err = (-1, "")
                return None
            if is_member:
                names = ["{} {}".format(user.display_name, ("({})".format(user.name)) if user.nick else "") for user in users]
            else:
                names = [user.name for user in users]
            selected = await ctx.selector("Multiple users found matching `{}`! Please select one.".format(user_str), names)
            if selected is None:
                return None
            return users[selected]
        else:
            return discord.utils.find(is_user, collection)

    @bot.util
    async def offer_create_role(ctx, input, timeout=30):
        result = await ctx.ask("Would you like to create this role?", timeout=timeout)
        if result == 0:
            return None
        try:
            # TODO: Lots of fancy stuff, move this out to an interactive create role utility
            role = await ctx.bot.create_role(ctx.server, name=input)
        except discord.Forbidden:
            await ctx.reply("Sorry, it seems I don't have permissions to create a role!")
            return None
        await ctx.reply("You have created the role `{}`!".format(input))
        return role

    @bot.util
    async def create_role(ctx, name):
        pass

    @bot.util
    async def find_role(ctx, userstr, create=False, interactive=False):
        if not ctx.server:
            ctx.cmd_err = (1, "This is not valid outside of a server!")
            return None
        if userstr == "":
            await ctx.reply("Looking up a role without a name! Something's wacky. Please check your input and try again")
            ctx.cmd_err = (-1, "")
            return None
        roleid = userstr.strip('<#@!>')
        if interactive:
            def check(role):
                return (role.id == roleid) or (userstr.lower() in role.name.lower())
            roles = list(filter(check, ctx.server.roles))
            if len(roles) == 0:
                role = None
            else:
                selected = await ctx.selector("Multiple roles found matching `{}`! Please select one.".format(userstr),
                                              [role.name for role in roles])
                if selected is None:
                    return None
                role = roles[selected]
        else:
            if roleid.isdigit():
                def is_role(role):
                    return role.id == roleid
            else:
                def is_role(role):
                    return userstr.lower() in role.name.lower()
            role = discord.utils.find(is_role, ctx.server.roles)
        if role:
            return role
        else:
            msg = await ctx.reply("I can't find this role in this server!")
            if create:
                role = await ctx.offer_create_role(userstr)
                if not role:
                    ctx.cmd_err = (1, "Aborting...")
                    await ctx.bot.delete_message(msg)
                    return None
                await ctx.bot.delete_message(msg)
                return role
            return None
