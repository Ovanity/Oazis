"""Start command handler and onboarding flow."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from loguru import logger

from oazis.bot.keyboards import (
    ONBOARD_PROFILE_PREFIX,
    ONBOARD_GOAL_PREFIX,
    ONBOARD_START,
    hub_keyboard,
    onboarding_goal_keyboard,
    onboarding_profile_keyboard,
    start_keyboard,
)
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
            "👋 <b>Bienvenue sur Oazis</b>\n"
            "Pour t'aider à boire suffisamment, sans prise de tête.\n"
            "Réglons ton programme en deux clics, puis tout se gère depuis le hub.\n"
            "<i>Avec amour, par Martin.</i>",
            reply_markup=start_keyboard(),
        )

    @router.callback_query(lambda c: c.data == ONBOARD_START)
    async def start_onboarding(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        await callback.answer()
        await callback.message.answer(
            "🚀 <b>Onboarding</b>\n"
            "💧 Choisis ton objectif quotidien (4 à 10 verres).\n"
            "Tu pourras toujours ajuster ensuite dans les réglages.",
            reply_markup=onboarding_goal_keyboard(),
        )

    @router.callback_query(lambda c: c.data and c.data.startswith(ONBOARD_GOAL_PREFIX))
    async def onboarding_goal(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            return
        try:
            count = int(callback.data.removeprefix(ONBOARD_GOAL_PREFIX))
        except ValueError:
            await callback.answer("Choix invalide.", show_alert=True)
            return
        if not 4 <= count <= 10:
            await callback.answer("Choisis entre 4 et 10 verres.", show_alert=True)
            return
        await service.update_user_preferences(callback.from_user.id, daily_target_glasses=count)
        await callback.answer("Objectif enregistré.")
        await callback.message.answer(
            f"🎯 Objectif réglé sur <b>{count} verres/jour</b>.\n"
            "⏱️ Choisis le type de rappels qui te convient.",
            reply_markup=onboarding_profile_keyboard(),
        )

    @router.callback_query(lambda c: c.data and c.data.startswith(ONBOARD_PROFILE_PREFIX))
    async def onboarding_profile(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            return
        profile = callback.data.removeprefix(ONBOARD_PROFILE_PREFIX)
        if profile == "balanced":
            start, end, interval = 9, 21, 90
            label = "🌿 Doux — quelques rappels sur la journée (9h–21h, ~1h30)"
        elif profile == "focus":
            start, end, interval = 8, 22, 60
            label = "⚡️ Focus — rappels fréquents pour ancrer l’habitude (8h–22h, ~1h)"
        elif profile == "light":
            start, end, interval = 10, 20, 120
            label = "🕰 Discret — plus rares pour rester léger (10h–20h, ~2h)"
        else:
            await callback.answer("Choix invalide.", show_alert=True)
            return

        await service.update_user_preferences(
            callback.from_user.id,
            reminder_start_hour=start,
            reminder_end_hour=end,
            reminder_interval_minutes=interval,
        )
        await callback.answer("Rappels enregistrés.")

        user = await service.ensure_user(callback.from_user.id)
        start = user.reminder_start_hour
        end = user.reminder_end_hour
        goal = user.daily_target_glasses or 0

        summary = (
            "✅ <b>Paramètres enregistrés</b>\n\n"
            f"• Objectif : <b>{goal} verres/jour</b>\n"
            f"• Rappels : <b>{label}</b>\n\n"
            "Tu peux accéder au hub pour tout gérer."
        )
        await callback.message.answer(summary, reply_markup=hub_keyboard())

    return router
