from paraCH import paraCH

cmds = paraCH()

@cmds.cmd("ban",
          category="Moderation",
          short_help="Bans users")
async def cmd_ban(ctx):
    """
    Usage: {prefix}ban <user1> [user2] [user3]... [-r <reason>] [-p <days>]

    Bans the users listed with an optional reason.
    If -p is provided, purges <days> days of message history for each user.
    """
    pass

@cmds.cmd("hackban",
          category="Moderation",
          short_help="Pre-bans users by id")
async def cmd_hackban(ctx):
    """
    Usage: {prefix}hackban <userid1> [userid2] [userid3]... [-r <reason>]

    Bans the user ids listed with an optional reason.
    """
    pass


@cmds.cmd("softban",
          category="Moderation",
          short_help="Softbans a user")
async def cmd_ban(ctx):
    """
    Usage: {prefix}ban <user1> [user2] [user3]... [-r <reason>]

    Bans the users listed with an optional reason.
    """
    pass
