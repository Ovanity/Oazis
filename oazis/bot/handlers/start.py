"""Start command handler."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from oazis.bot.keyboards import glasses_goal_keyboard, hydration_log_keyboard, reminder_setup_keyboard
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
        await message.answer(
            "Réglons ton programme :\n"
            "• Objectif quotidien : choisis entre 4 et 10 verres.\n"
            "• Rappels : plage logique dans la journée et fréquence cohérente.\n"
            "Conseil : 1-2 verres le matin, 2-3 sur les repas, 1-2 le soir.",
            reply_markup=glasses_goal_keyboard(),
        )
        await message.answer(
            "Choisis ta plage et ta fréquence de rappels.",
            reply_markup=reminder_setup_keyboard(),
        )

    return router
