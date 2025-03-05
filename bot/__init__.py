from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from bot.routers import user_router
from bot.middlewares import GlobalMiddleware


bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

dp.message.middleware(GlobalMiddleware())
dp.callback_query.middleware(GlobalMiddleware())

dp.include_router(user_router)