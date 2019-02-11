from datetime import datetime


async def store_status(bot, before, after):
    if before.status != after.status:
        status = (str(before.status), str(after.status), int(datetime.utcnow().strftime('%s')))
        await bot.data.users.set(before.id, "old_status", status)


def load_into(bot):
    bot.data.users.ensure_exists("old_status")
    bot.add_after_event("member_update", store_status)
