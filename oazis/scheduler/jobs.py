"""Scheduler job implementations."""

import random
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from loguru import logger

from oazis.bot.formatting import format_interval, format_progress, format_volume_ml
from oazis.bot.keyboards import reminder_actions_keyboard
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
        paused = await service.is_reminders_paused_today(user.telegram_id)

        if paused:
            logger.debug("Skip user {user_id}: reminders paused today", user_id=user.telegram_id)
            continue
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

        entry = await service.get_today_entry(user.telegram_id)
        target_glasses = user.daily_target_glasses or settings.default_daily_glasses
        target_ml = user.daily_target_ml or target_glasses * settings.glass_volume_ml
        if entry:
            target_ml = entry.goal_ml
        consumed = entry.consumed_ml if entry else 0

        if consumed >= target_ml:
            already_notified = await service.has_goal_been_notified(user.telegram_id)
            if not already_notified:
                await _send_goal_reached(bot, user.telegram_id, consumed, target_ml)
                await service.record_goal_notified(user.telegram_id)
            continue

        tip = _time_of_day_tip(now.hour)
        friendly_interval = format_interval(interval_minutes)

        try:
            await bot.send_message(
                user.telegram_id,
                "💧 <b>Rappel hydratation</b>\n"
                f"{_reminder_intro(start_hour, end_hour, friendly_interval)}\n"
                f"• Astuce : <i>{tip}</i>\n"
                f"{_reminder_humor()}\n"
                f"Objectif du jour : <b>{format_volume_ml(target_ml)}</b>\n"
                "👉 Appuie ci-dessous si tu viens de boire.",
                reply_markup=reminder_actions_keyboard(),
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


async def _send_goal_reached(bot: Bot, user_id: int, consumed_ml: int, target_ml: int) -> None:
    """Send a one-time celebratory message when the daily goal is hit."""
    progress = format_progress(consumed_ml, target_ml)
    text = (
        "🎉 <b>Objectif atteint</b> !\n"
        f"Total du jour : <b>{progress}</b>.\n"
        "Les rappels sont coupés pour aujourd'hui.\n"
        "Tu peux toujours enregistrer un verre supplémentaire si besoin 👇"
    )
    await bot.send_message(user_id, text, reply_markup=reminder_actions_keyboard())


def _reminder_intro(start_hour: int, end_hour: int, interval_text: str) -> str:
    choices = [
        f"• Plage : <b>{start_hour}h–{end_hour}h</b> • Rythme ~{interval_text}",
        f"• Dans ta plage <b>{start_hour}h–{end_hour}h</b> • On garde le rythme ~{interval_text}",
        f"• Fenêtre actuelle : <b>{start_hour}h–{end_hour}h</b> • Rappel ~{interval_text}",
    ]
    return random.choice(choices)


def _reminder_humor() -> str:
    choices = [
        "Je sais que tu n'aimes pas ça, mais ton corps te remerciera 😉",
        "L'eau, ce n'est pas toujours fun, mais c'est ton meilleur allié aujourd'hui 💧",
        "Promis, juste un verre et je te laisse tranquille un moment 😇",
    ]
    return random.choice(choices)
