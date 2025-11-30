"""Settings callbacks for user preferences."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from oazis.bot.keyboards import (
    GLASS_GOAL_PREFIX,
    REMINDER_PAUSE_TODAY,
    REMINDER_RESUME,
    NAV_RESTART_ONBOARDING,
    REMINDER_FREQUENCIES,
    REMINDER_WINDOWS,
    REMINDER_INTERVAL_PREFIX,
    REMINDER_WINDOW_PREFIX,
    glasses_goal_keyboard,
    hydration_log_keyboard,
    reminder_frequency_keyboard,
    reminder_window_keyboard,
    settings_menu_keyboard,
)
from oazis.scheduler import ReminderScheduler
from oazis.services.hydration import HydrationService


def build_router(service: HydrationService, reminder_scheduler: ReminderScheduler) -> Router:
    router = Router(name="settings")

    @router.callback_query(lambda c: c.data and c.data.startswith(NAV_RESTART_ONBOARDING))
    async def open_settings_menu(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message or not callback.data:
            return
        await callback.answer()
        suffix = callback.data.removeprefix(NAV_RESTART_ONBOARDING)
        if suffix == ":goal":
            await callback.message.answer(
                "🎯 <b>Objectif quotidien</b>\n\n"
                "Choisis une cible entre 4 et 10 verres.",
                reply_markup=glasses_goal_keyboard(),
            )
        elif suffix == ":window":
            await callback.message.answer(
                "🕒 <b>Plage de rappels</b>\n\n"
                "Choisis une plage qui colle à ton rythme.",
                reply_markup=reminder_window_keyboard(),
            )
        elif suffix == ":freq":
            await callback.message.answer(
                "⏱️ <b>Fréquence des rappels</b>\n\n"
                "Prends le rythme qui te va le mieux.",
                reply_markup=reminder_frequency_keyboard(),
            )
        else:
            await callback.message.answer(
                "⚙️ <b>Réglages</b>\n\n"
                "Ajuste ton programme en un clic.",
                reply_markup=settings_menu_keyboard(),
            )

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
        logger.info(
            "event=settings_goal_updated user_id={user_id} chat_id={chat_id} chat_type={chat_type} goal_glasses={goal} goal_ml={goal_ml} language={language} is_premium={is_premium}",
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id if callback.message and callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message and callback.message.chat else None,
            goal=count,
            goal_ml=count * service.settings.glass_volume_ml,
            language=callback.from_user.language_code,
            is_premium=getattr(callback.from_user, "is_premium", False),
        )
        await callback.answer("Objectif mis à jour.")
        if callback.message:
            await callback.message.answer(
                f"✅ Objectif réglé sur {count} verres / jour (≈ {count * service.settings.glass_volume_ml} ml).\n\n"
                "Choisis maintenant ta plage horaire de rappels.",
                reply_markup=reminder_window_keyboard(),
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

        if payload not in {w for w, _ in REMINDER_WINDOWS}:
            await callback.answer("Plage non proposée.", show_alert=True)
            return

        await service.update_user_preferences(
            callback.from_user.id,
            reminder_start_hour=start,
            reminder_end_hour=end,
        )
        await reminder_scheduler.schedule_for_user(callback.from_user.id)
        logger.info(
            "event=settings_window_updated user_id={user_id} chat_id={chat_id} chat_type={chat_type} start_hour={start} end_hour={end} language={language} is_premium={is_premium}",
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id if callback.message and callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message and callback.message.chat else None,
            start=start,
            end=end,
            language=callback.from_user.language_code,
            is_premium=getattr(callback.from_user, "is_premium", False),
        )
        await callback.answer("Plage enregistrée.")
        if callback.message:
            await callback.message.answer(
                f"✅ Rappels entre {start}h et {end}h.\n\n"
                "Choisis la fréquence des rappels :",
                reply_markup=reminder_frequency_keyboard(),
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

        if interval not in {freq for freq, _ in REMINDER_FREQUENCIES}:
            await callback.answer("Intervalle non supporté.", show_alert=True)
            return

        await service.update_user_preferences(
            callback.from_user.id,
            reminder_interval_minutes=interval,
        )
        await reminder_scheduler.schedule_for_user(callback.from_user.id)
        logger.info(
            "event=settings_interval_updated user_id={user_id} chat_id={chat_id} chat_type={chat_type} interval_min={interval} language={language} is_premium={is_premium}",
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id if callback.message and callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message and callback.message.chat else None,
            interval=interval,
            language=callback.from_user.language_code,
            is_premium=getattr(callback.from_user, "is_premium", False),
        )
        await callback.answer("Fréquence mise à jour.")
        if callback.message:
            await callback.message.answer(
                f"✅ Rappel toutes les {interval} minutes.\n\n"
                "Conseil :\n"
                "• 1–2 verres le matin\n"
                "• 2–3 sur les repas\n"
                "• 1–2 le soir\n\n"
                "Tu es prêt : utilise le bouton ci-dessous pour enregistrer tes verres.",
                reply_markup=hydration_log_keyboard(),
            )

    @router.callback_query(lambda c: c.data == REMINDER_PAUSE_TODAY)
    async def handle_pause_today(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await service.pause_reminders_today(callback.from_user.id)
        logger.info(
            "event=reminders_paused_today user_id={user_id} chat_id={chat_id} chat_type={chat_type} language={language} is_premium={is_premium}",
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id if callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message.chat else None,
            language=callback.from_user.language_code,
            is_premium=getattr(callback.from_user, "is_premium", False),
        )
        await callback.answer("Rappels coupés pour aujourd'hui.")
        await callback.message.answer(
            "🔕 Rappels coupés pour aujourd'hui.\n\n"
            "Tu peux toujours noter un verre si tu en prends un.",
            reply_markup=hydration_log_keyboard(),
        )

    @router.callback_query(lambda c: c.data == REMINDER_RESUME)
    async def handle_resume(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await service.resume_reminders_today(callback.from_user.id)
        logger.info(
            "event=reminders_resumed_today user_id={user_id} chat_id={chat_id} chat_type={chat_type} language={language} is_premium={is_premium}",
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id if callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message.chat else None,
            language=callback.from_user.language_code,
            is_premium=getattr(callback.from_user, "is_premium", False),
        )
        await callback.answer("Rappels réactivés.")
        await callback.message.answer(
            "🔔 Rappels réactivés pour aujourd'hui.",
            reply_markup=hydration_log_keyboard(),
        )

    return router
