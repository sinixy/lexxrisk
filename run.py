import asyncio


async def run():
    from db import db, update_database
    await db.init()
    await update_database(db)

    from bot import bot, dp
    print('Go!')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())