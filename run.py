import asyncio

from common.logger import logger


async def run():
    logger.info('Starting...')
    from db import db, update_database
    await db.init()
    await update_database(db)
    logger.info('Database initialized')

    from bot import bot, dp
    print('Go!')
    logger.info('Bot started')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())