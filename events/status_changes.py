from datetime import datetime

async def store_status(bot, before, after):
    if before.status != after.status:
        status = {"before": str(before.status),
                  "after": str(after.status),
                  "time": int(datetime.utcnow().strftime('%s'))}
        await bot.data.users.set(before.id, "previous_status", status)


def load_into(bot):
    # TODO: Ensure previous_status column exists for user
    bot.add_after_event("member_update", store_status)
