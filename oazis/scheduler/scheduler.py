"""Scheduler factory and job registration."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from oazis.config import Settings
from oazis.services.hydration import HydrationService

from .jobs import send_hydration_reminders


def create_scheduler(settings: Settings) -> AsyncIOScheduler:
    """Create an AsyncIOScheduler configured with the app timezone."""
    return AsyncIOScheduler(timezone=settings.timezone)


def _aligned_start_date(granularity_minutes: int, timezone: str) -> datetime:
    """Return the next datetime aligned to the scheduler granularity in the given timezone."""
    now = datetime.now(ZoneInfo(timezone)).replace(second=0, microsecond=0)
    if granularity_minutes <= 0:
        return now

    total_minutes = now.hour * 60 + now.minute
    remainder = total_minutes % granularity_minutes
    delta_minutes = 0 if remainder == 0 else granularity_minutes - remainder
    return now + timedelta(minutes=delta_minutes)


def register_jobs(
    scheduler: AsyncIOScheduler,
    service: HydrationService,
    settings: Settings,
    bot: Bot,
) -> None:
    """Attach recurring jobs to the scheduler."""
    start_date = _aligned_start_date(settings.reminder_check_minutes, settings.timezone)
    scheduler.add_job(
        send_hydration_reminders,
        trigger=IntervalTrigger(
            minutes=settings.reminder_check_minutes,
            start_date=start_date,
        ),
        args=[bot, service, settings],
        id="hydration_reminders",
        replace_existing=True,
    )
    logger.info(
        "Hydration reminders evaluated every {tick} minutes (default interval {minutes} between {start}:00 and {end}:00) – next tick at {next}",
        tick=settings.reminder_check_minutes,
        minutes=settings.reminder_interval_minutes,
        start=settings.hydration_start_hour,
        end=settings.hydration_end_hour,
        next=start_date.isoformat(),
    )
