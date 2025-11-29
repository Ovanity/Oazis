"""Start command handler."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from oazis.bot.keyboards import glasses_goal_keyboard
from oazis.services.hydration import HydrationService


def build_router(service: HydrationService) -> Router:
    router = Router(name="start")

    @router.message(CommandStart())
    async def handle_start(message: Message) -> None:
        if not message.from_user:
            return

        user = await service.ensure_user(message.from_user.id)
        logger.info("Registered user {user_id}", user_id=user.telegram_id)

        await message.answer(
            "👋 Bienvenue sur Oazis.\n"
            "Je t'aide à suivre ton hydratation quotidienne.\n"
            "Réglons ton programme étape par étape.",
            reply_markup=glasses_goal_keyboard(),
        )

    return router
