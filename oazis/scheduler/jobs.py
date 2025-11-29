"""Scheduler job implementations."""

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from loguru import logger

from oazis.bot.keyboards import hydration_log_keyboard
from oazis.config import Settings
from oazis.services.hydration import HydrationService


async def send_hydration_reminders(bot: Bot, service: HydrationService, settings: Settings) -> None:
    """Send a simple hydration reminder to every registered user."""
    now = datetime.now(ZoneInfo(settings.timezone))

    users = await service.list_users()
    if not users:
        logger.debug("No users registered for reminders")
        return

    for user in users:
        start_hour = user.reminder_start_hour or settings.hydration_start_hour
        end_hour = user.reminder_end_hour or settings.hydration_end_hour
        interval_minutes = user.reminder_interval_minutes or settings.reminder_interval_minutes

        if not _is_valid_window(start_hour, end_hour):
            logger.debug(
                "Skip user {user_id}: invalid window {start}-{end}",
                user_id=user.telegram_id,
                start=start_hour,
                end=end_hour,
            )
            continue

        if interval_minutes <= 0:
            logger.debug("Skip user {user_id}: invalid interval {interval}", user_id=user.telegram_id, interval=interval_minutes)
            continue

        minutes_now = now.hour * 60 + now.minute
        minutes_start = start_hour * 60

        if not (minutes_start <= minutes_now < end_hour * 60):
            continue

        minutes_since_start = minutes_now - minutes_start
        if minutes_since_start % interval_minutes != 0:
            continue

        tip = _time_of_day_tip(now.hour)

        try:
            await bot.send_message(
                user.telegram_id,
                "💧 Rappel hydratation : pense à boire un verre d'eau.\n"
                f"{tip}\n"
                "👉 Utilise le bouton ci-dessous pour l'enregistrer.",
                reply_markup=hydration_log_keyboard(),
            )
        except Exception as exc:  # noqa: BLE001 - log and continue
            logger.error("Failed to send reminder to {user_id}: {error}", user_id=user.telegram_id, error=exc)


def _is_valid_window(start: int, end: int) -> bool:
    return 0 <= start < 24 and 0 < end <= 24 and start < end


def _time_of_day_tip(hour: int) -> str:
    if hour < 11:
        return "Astuce matin : un verre au réveil relance l'énergie."
    if hour < 15:
        return "Astuce midi : un verre avant le repas aide à rester alerte."
    if hour < 19:
        return "Astuce après-midi : garde un verre sur le bureau."
    return "Astuce soir : un petit verre, mais évite juste avant de dormir."
