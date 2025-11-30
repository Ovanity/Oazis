"""Scheduler factory and per-user job registration."""

from datetime import datetime, time, timedelta
from math import ceil
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from oazis.config import Settings
from oazis.services.hydration import HydrationService

from .jobs import send_hydration_reminder_for_user, _is_valid_window


def create_scheduler(settings: Settings) -> AsyncIOScheduler:
    """Create an AsyncIOScheduler configured with the app timezone."""
    return AsyncIOScheduler(timezone=settings.timezone)


def compute_next_aligned_run(
    start_hour: int,
    end_hour: int,
    interval_minutes: int,
    timezone: str,
    *,
    now: datetime | None = None,
) -> datetime:
    """Return the next datetime aligned on the interval grid inside the window."""
    current = (now or datetime.now(ZoneInfo(timezone))).replace(second=0, microsecond=0)
    today = current.date()
    tzinfo = ZoneInfo(timezone)

    start_today = datetime.combine(today, time(hour=start_hour, minute=0, tzinfo=tzinfo))
    end_today = datetime.combine(today, time(hour=end_hour, minute=0, tzinfo=tzinfo))

    if current < start_today:
        return start_today

    if start_today <= current < end_today:
        minutes_since_start = (current - start_today).total_seconds() // 60
        steps = ceil(minutes_since_start / interval_minutes)
        candidate = start_today + timedelta(minutes=steps * interval_minutes)
        if candidate < end_today:
            return candidate

    tomorrow = today + timedelta(days=1)
    return datetime.combine(tomorrow, time(hour=start_hour, minute=0, tzinfo=tzinfo))


class ReminderScheduler:
    """Manage per-user reminder jobs with aligned schedules."""

    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, service: HydrationService, settings: Settings) -> None:
        self.scheduler = scheduler
        self.bot = bot
        self.service = service
        self.settings = settings

    async def schedule_for_user(self, user_id: int) -> None:
        """Create or replace a reminder job for a single user."""
        user = await self.service.ensure_user(user_id)
        start_hour = user.reminder_start_hour or self.settings.hydration_start_hour
        end_hour = user.reminder_end_hour or self.settings.hydration_end_hour
        interval_minutes = user.reminder_interval_minutes or self.settings.reminder_interval_minutes
        timezone = user.timezone or self.settings.timezone

        if interval_minutes <= 0 or not _is_valid_window(start_hour, end_hour):
            logger.warning(
                "Skip scheduling for user {user_id}: invalid config start={start} end={end} interval_min={interval}",
                user_id=user_id,
                start=start_hour,
                end=end_hour,
                interval=interval_minutes,
            )
            return

        next_run = compute_next_aligned_run(start_hour, end_hour, interval_minutes, timezone)
        job_id = self._job_id(user_id)

        self.scheduler.add_job(
            send_hydration_reminder_for_user,
            trigger=IntervalTrigger(
                minutes=interval_minutes,
                start_date=next_run,
                timezone=ZoneInfo(timezone),
            ),
            args=[self.bot, self.service, self.settings, user_id],
            id=job_id,
            replace_existing=True,
        )
        logger.info(
            "Scheduled reminders for user {user_id}: every {interval} minutes between {start}:00 and {end}:00 (tz={tz}) – next at {next}",
            user_id=user_id,
            interval=interval_minutes,
            start=start_hour,
            end=end_hour,
            tz=timezone,
            next=next_run.isoformat(),
        )

    async def schedule_for_all_users(self) -> None:
        """Create or replace reminder jobs for every known user."""
        users = await self.service.list_users()
        if not users:
            logger.info("No users to schedule reminders for.")
            return

        for user in users:
            await self.schedule_for_user(user.telegram_id)

    def _job_id(self, user_id: int) -> str:
        return f"hydration_reminder_user_{user_id}"
