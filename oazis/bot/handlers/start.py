"""Start command handler and onboarding flow."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from loguru import logger

from oazis.bot.keyboards import (
    ONBOARD_FREQ_PREFIX,
    ONBOARD_GOAL_PREFIX,
    ONBOARD_START,
    ONBOARD_WINDOW_PREFIX,
    hub_keyboard,
    onboarding_frequency_keyboard,
    onboarding_goal_keyboard,
    onboarding_window_keyboard,
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
            "Je t'aide à suivre ton hydratation en douceur, sans pression.\n"
            "Commence par configurer ton programme ou ouvre directement le hub.",
            reply_markup=start_keyboard(),
        )

    @router.callback_query(lambda c: c.data == ONBOARD_START)
    async def start_onboarding(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        await callback.answer()
        await callback.message.answer(
            "🚀 <b>Onboarding</b>\n"
            "💧 Choisis ton objectif quotidien (entre 4 et 10 verres).\n"
            "Tu pourras changer plus tard dans les réglages.",
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
            "🕒 Choisis maintenant ta plage de rappels.",
            reply_markup=onboarding_window_keyboard(),
        )

    @router.callback_query(lambda c: c.data and c.data.startswith(ONBOARD_WINDOW_PREFIX))
    async def onboarding_window(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            return
        payload = callback.data.removeprefix(ONBOARD_WINDOW_PREFIX)
        try:
            start_str, end_str = payload.split("-", maxsplit=1)
            start, end = int(start_str), int(end_str)
        except Exception:  # noqa: BLE001
            await callback.answer("Plage invalide.", show_alert=True)
            return
        if not (0 <= start < 24 and 0 < end <= 24 and start < end):
            await callback.answer("Plage incohérente.", show_alert=True)
            return
        await service.update_user_preferences(
            callback.from_user.id,
            reminder_start_hour=start,
            reminder_end_hour=end,
        )
        await callback.answer("Plage enregistrée.")
        await callback.message.answer(
            f"🕒 Rappels entre <b>{start}h</b> et <b>{end}h</b>.\n"
            "⏱️ Choisis la fréquence.",
            reply_markup=onboarding_frequency_keyboard(),
        )

    @router.callback_query(lambda c: c.data and c.data.startswith(ONBOARD_FREQ_PREFIX))
    async def onboarding_frequency(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            return
        try:
            interval = int(callback.data.removeprefix(ONBOARD_FREQ_PREFIX))
        except ValueError:
            await callback.answer("Choix invalide.", show_alert=True)
            return
        if interval not in {60, 90, 120}:
            await callback.answer("Intervalle non supporté.", show_alert=True)
            return
        await service.update_user_preferences(
            callback.from_user.id,
            reminder_interval_minutes=interval,
        )
        await callback.answer("Fréquence enregistrée.")

        user = await service.ensure_user(callback.from_user.id)
        start = user.reminder_start_hour
        end = user.reminder_end_hour
        goal = user.daily_target_glasses or 0

        summary = (
            "✅ <b>Paramètres enregistrés</b>\n"
            f"• Objectif : <b>{goal} verres/jour</b>\n"
            f"• Rappels : toutes les <b>{interval} min</b> "
            f"entre <b>{start}h</b> et <b>{end}h</b>\n"
            "Tu peux accéder au hub pour tout gérer."
        )
        await callback.message.answer(summary, reply_markup=hub_keyboard())

    return router
