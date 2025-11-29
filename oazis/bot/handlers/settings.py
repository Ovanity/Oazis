"""Settings callbacks for user preferences."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from oazis.bot.keyboards import (
    GLASS_GOAL_PREFIX,
    REMINDER_INTERVAL_PREFIX,
    REMINDER_WINDOW_PREFIX,
    glasses_goal_keyboard,
    reminder_setup_keyboard,
)
from oazis.services.hydration import HydrationService


def build_router(service: HydrationService) -> Router:
    router = Router(name="settings")

    @router.callback_query(F.data.startswith(GLASS_GOAL_PREFIX))
    async def handle_glass_goal(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            await callback.answer("Action impossible.", show_alert=True)
            return

        try:
            count = int(callback.data.removeprefix(GLASS_GOAL_PREFIX))
        except ValueError:
            await callback.answer("Choix invalide.", show_alert=True)
            return

        if not 4 <= count <= 10:
            await callback.answer("Choisis entre 4 et 10 verres.", show_alert=True)
            return

        await service.update_user_preferences(callback.from_user.id, daily_target_glasses=count)
        await callback.answer("Objectif mis à jour.")
        if callback.message:
            await callback.message.answer(
                f"✅ Objectif réglé sur {count} verres / jour (≈ {count * service.settings.glass_volume_ml} ml).",
                reply_markup=glasses_goal_keyboard(),
            )

    @router.callback_query(F.data.startswith(REMINDER_WINDOW_PREFIX))
    async def handle_reminder_window(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            await callback.answer("Action impossible.", show_alert=True)
            return

        payload = callback.data.removeprefix(REMINDER_WINDOW_PREFIX)
        try:
            start_str, end_str = payload.split("-", maxsplit=1)
            start, end = int(start_str), int(end_str)
        except Exception:  # noqa: BLE001 - controlled parsing error
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
        if callback.message:
            await callback.message.answer(
                f"✅ Rappels entre {start}h et {end}h. "
                "Astuce : vise 1-2 verres le matin, 2-3 sur les repas, 1-2 le soir.",
                reply_markup=reminder_setup_keyboard(),
            )

    @router.callback_query(F.data.startswith(REMINDER_INTERVAL_PREFIX))
    async def handle_reminder_interval(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            await callback.answer("Action impossible.", show_alert=True)
            return

        try:
            interval = int(callback.data.removeprefix(REMINDER_INTERVAL_PREFIX))
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
        await callback.answer("Fréquence mise à jour.")
        if callback.message:
            await callback.message.answer(
                f"✅ Rappel toutes les {interval} minutes. "
                "Pense à boire dès le matin, une fois par repas, et un petit verre le soir.",
                reply_markup=reminder_setup_keyboard(),
            )

    return router
