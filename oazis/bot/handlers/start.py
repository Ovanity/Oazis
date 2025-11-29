"""Start command handler."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from oazis.bot.keyboards import hydration_log_keyboard
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
            "Je t'aiderai à suivre ton hydratation quotidienne.\n"
            "👉 Appuie sur le bouton ci-dessous dès que tu bois un verre (250 ml par défaut).",
            reply_markup=hydration_log_keyboard(),
        )

    return router
