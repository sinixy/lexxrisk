from aiogram import BaseMiddleware, types, Bot
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable, Union

from bot.models import User
from bot.models.enums import Role
from common.logger import logger
from risk import manager


class GlobalMiddleware(BaseMiddleware):

    async def __call__(self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Union[types.Message, types.CallbackQuery],
        data: Dict[str, Any]
    ):
        user_id = event.from_user.id
        user = await User.get(user_id)
        bot: Bot = data["bot"]

        if not user:
            await bot.send_message(user_id, "Ваш аккаунт не зарегистрирован в системе! Пожалуйста, обратитесь к администратору.")
            return
        if not user.account_id and user.role != Role.admin:
            await bot.send_message(user_id, "Ваш телеграм не подвязан к аккаунту Такиона! Пожалуйста, обратитесь к администратору.")
            return
        
        data["user"] = user
        
        try:
            if not data.get('takion'):
                data['takion'] = await manager.get_takion_by_account(user.account_id)
            return await handler(event, data)
        except Exception as e:
            await bot.send_message(user_id, "Возникла ошибка в боте! Пожалуйста, сообщите к администратору.\n\n" + str(e))
            await data["state"].clear()
            logger.exception(str(e))
    