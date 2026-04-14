from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from bot.config import ADMIN_ID


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if isinstance(event, Message) else event.from_user.id
        return user_id == ADMIN_ID
