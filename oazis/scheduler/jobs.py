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
    if not settings.hydration_start_hour <= now.hour < settings.hydration_end_hour:
        logger.debug("Outside reminder window at {time}", time=now)
        return

    users = await service.list_users()
    if not users:
        logger.debug("No users registered for reminders")
        return

    for user in users:
        try:
            await bot.send_message(
                user.telegram_id,
                "💧 Rappel hydratation : pense à boire un verre d'eau.\n"
                "👉 Utilise le bouton ci-dessous pour l'enregistrer.",
                reply_markup=hydration_log_keyboard(),
            )
        except Exception as exc:  # noqa: BLE001 - log and continue
            logger.error("Failed to send reminder to {user_id}: {error}", user_id=user.telegram_id, error=exc)
