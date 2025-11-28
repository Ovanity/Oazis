"""Scheduler factory and job registration."""

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


def register_jobs(
    scheduler: AsyncIOScheduler,
    service: HydrationService,
    settings: Settings,
    bot: Bot,
) -> None:
    """Attach recurring jobs to the scheduler."""
    scheduler.add_job(
        send_hydration_reminders,
        trigger=IntervalTrigger(minutes=settings.reminder_interval_minutes),
        args=[bot, service, settings],
        id="hydration_reminders",
        replace_existing=True,
    )
    logger.info(
        "Hydration reminders scheduled every {minutes} minutes between {start}:00 and {end}:00",
        minutes=settings.reminder_interval_minutes,
        start=settings.hydration_start_hour,
        end=settings.hydration_end_hour,
    )
