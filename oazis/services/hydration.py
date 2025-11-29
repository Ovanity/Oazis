"""Domain services for hydration tracking."""

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from loguru import logger
from oazis.config import Settings
from oazis.db import DailyHydration, HydrationEvent, User
from oazis.db.session import session_scope


@dataclass
class HydrationStats:
    days_considered: int
    total_ml: int
    average_ml: int
    goal_hits: int
    today_consumed_ml: int
    today_goal_ml: int


class HydrationService:
    """Simple service layer orchestrating hydration persistence and rules."""

    def __init__(self, engine: Engine, settings: Settings) -> None:
        self.engine = engine
        self.settings = settings

    async def ensure_user(self, telegram_id: int) -> User:
        """Return an existing user or create one with default settings."""
        return await asyncio.to_thread(self._ensure_user_sync, telegram_id)

    def _ensure_user_sync(self, telegram_id: int) -> User:
        with session_scope(self.engine) as session:
            return self._get_or_create_user(session, telegram_id)

    async def record_glass(self, telegram_id: int, volume_ml: int = 250) -> DailyHydration:
        """Increment today's hydration entry for a user."""
        return await asyncio.to_thread(self._record_glass_sync, telegram_id, volume_ml)

    def _record_glass_sync(self, telegram_id: int, volume_ml: int) -> DailyHydration:
        today = date.today()
        with session_scope(self.engine) as session:
            user = self._get_or_create_user(session, telegram_id)
            target_glasses = user.daily_target_glasses or self.settings.default_daily_glasses
            target = user.daily_target_ml or target_glasses * self.settings.glass_volume_ml

            stmt = select(DailyHydration).where(
                DailyHydration.user_id == telegram_id, DailyHydration.date == today
            )
            entry = session.exec(stmt).first()
            if not entry:
                entry = DailyHydration(user_id=telegram_id, date=today, goal_ml=target)
                session.add(entry)

            entry.consumed_ml += volume_ml
            entry.updated_at = datetime.utcnow()

            session.add(
                HydrationEvent(
                    user_id=telegram_id,
                    event_type="glass_logged",
                    notes=f"{volume_ml}ml",
                )
            )
            session.commit()
            session.refresh(entry)
            return entry

    async def list_users(self) -> List[User]:
        """Return every registered user. Used by scheduler for reminders."""
        return await asyncio.to_thread(self._list_users_sync)

    def _list_users_sync(self) -> List[User]:
        with session_scope(self.engine) as session:
            users = session.exec(select(User)).all()
            return list(users)

    async def get_stats(self, telegram_id: int, days: int = 7) -> HydrationStats:
        """Return basic hydration stats over the last `days` (inclusive of today)."""
        return await asyncio.to_thread(self._get_stats_sync, telegram_id, days)

    async def get_today_entry(self, telegram_id: int) -> DailyHydration | None:
        """Return today's hydration entry for a user, if any."""
        return await asyncio.to_thread(self._get_today_entry_sync, telegram_id)

    def _get_today_entry_sync(self, telegram_id: int) -> DailyHydration | None:
        with session_scope(self.engine) as session:
            stmt = select(DailyHydration).where(
                DailyHydration.user_id == telegram_id,
                DailyHydration.date == date.today(),
            )
            return session.exec(stmt).first()

    async def pause_reminders_today(self, telegram_id: int) -> None:
        """Pause reminders for the rest of the day."""
        await asyncio.to_thread(self._pause_reminders_today_sync, telegram_id)

    def _pause_reminders_today_sync(self, telegram_id: int) -> None:
        with session_scope(self.engine) as session:
            session.add(
                HydrationEvent(
                    user_id=telegram_id,
                    event_type="reminders_paused",
                    notes="paused_until_end_of_day",
                )
            )
            session.commit()

    async def is_reminders_paused_today(self, telegram_id: int) -> bool:
        """Return True if user paused reminders for today."""
        return await asyncio.to_thread(self._is_reminders_paused_today_sync, telegram_id)

    def _is_reminders_paused_today_sync(self, telegram_id: int) -> bool:
        """Check the latest pause/resume event today to decide."""
        today = date.today()
        day_start = datetime.combine(today, time.min)
        day_end = datetime.combine(today, time.max)
        with session_scope(self.engine) as session:
            stmt = (
                select(HydrationEvent)
                .where(
                    HydrationEvent.user_id == telegram_id,
                    HydrationEvent.event_type.in_(["reminders_paused", "reminders_resumed"]),
                    HydrationEvent.timestamp >= day_start,
                    HydrationEvent.timestamp <= day_end,
                )
                .order_by(HydrationEvent.timestamp.desc())
            )
            event = session.exec(stmt).first()
            if not event:
                return False
            return event.event_type == "reminders_paused"

    async def resume_reminders_today(self, telegram_id: int) -> None:
        """Resume reminders for the rest of the day."""
        await asyncio.to_thread(self._resume_reminders_today_sync, telegram_id)

    def _resume_reminders_today_sync(self, telegram_id: int) -> None:
        with session_scope(self.engine) as session:
            session.add(
                HydrationEvent(
                    user_id=telegram_id,
                    event_type="reminders_resumed",
                    notes="resumed_until_end_of_day",
                )
            )
            session.commit()

    def _get_stats_sync(self, telegram_id: int, days: int) -> HydrationStats:
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        with session_scope(self.engine) as session:
            user = self._get_or_create_user(session, telegram_id)
            stmt = select(DailyHydration).where(
                DailyHydration.user_id == telegram_id,
                DailyHydration.date >= start_date,
            )
            entries = session.exec(stmt).all()

            today_entry = next((e for e in entries if e.date == today), None)
            target_glasses = user.daily_target_glasses or self.settings.default_daily_glasses
            default_goal_ml = user.daily_target_ml or target_glasses * self.settings.glass_volume_ml
            today_goal_ml = today_entry.goal_ml if today_entry else default_goal_ml
            today_consumed_ml = today_entry.consumed_ml if today_entry else 0

            total_ml = sum(e.consumed_ml for e in entries)
            goal_hits = sum(1 for e in entries if e.consumed_ml >= e.goal_ml)
            days_considered = max(days, 1)
            average_ml = total_ml // days_considered

            return HydrationStats(
                days_considered=days_considered,
                total_ml=total_ml,
                average_ml=average_ml,
                goal_hits=goal_hits,
                today_consumed_ml=today_consumed_ml,
                today_goal_ml=today_goal_ml,
            )

    async def has_goal_been_notified(self, telegram_id: int) -> bool:
        """Check whether a goal_reached notification was already sent today."""
        return await asyncio.to_thread(self._has_goal_been_notified_sync, telegram_id)

    def _has_goal_been_notified_sync(self, telegram_id: int) -> bool:
        today = date.today()
        day_start = datetime.combine(today, time.min)
        day_end = datetime.combine(today, time.max)
        with session_scope(self.engine) as session:
            stmt = select(HydrationEvent).where(
                HydrationEvent.user_id == telegram_id,
                HydrationEvent.event_type == "goal_notified",
                HydrationEvent.timestamp >= day_start,
                HydrationEvent.timestamp <= day_end,
            )
            return session.exec(stmt).first() is not None

    async def record_goal_notified(self, telegram_id: int) -> None:
        """Persist an event to avoid re-sending goal reached notifications."""
        await asyncio.to_thread(self._record_goal_notified_sync, telegram_id)

    def _record_goal_notified_sync(self, telegram_id: int) -> None:
        with session_scope(self.engine) as session:
            session.add(
                HydrationEvent(
                    user_id=telegram_id,
                    event_type="goal_notified",
                    notes="daily goal reached",
                )
            )
            session.commit()

    async def update_user_preferences(
        self,
        telegram_id: int,
        *,
        daily_target_glasses: int | None = None,
        reminder_start_hour: int | None = None,
        reminder_end_hour: int | None = None,
        reminder_interval_minutes: int | None = None,
    ) -> User:
        """Persist updated user preferences."""
        return await asyncio.to_thread(
            self._update_user_preferences_sync,
            telegram_id,
            daily_target_glasses,
            reminder_start_hour,
            reminder_end_hour,
            reminder_interval_minutes,
        )

    def _update_user_preferences_sync(
        self,
        telegram_id: int,
        daily_target_glasses: int | None,
        reminder_start_hour: int | None,
        reminder_end_hour: int | None,
        reminder_interval_minutes: int | None,
    ) -> User:
        with session_scope(self.engine) as session:
            user = self._get_or_create_user(session, telegram_id)
            if daily_target_glasses is not None:
                user.daily_target_glasses = daily_target_glasses
                user.daily_target_ml = daily_target_glasses * self.settings.glass_volume_ml
            if reminder_start_hour is not None:
                user.reminder_start_hour = reminder_start_hour
            if reminder_end_hour is not None:
                user.reminder_end_hour = reminder_end_hour
            if reminder_interval_minutes is not None:
                user.reminder_interval_minutes = reminder_interval_minutes

            # Align today's goal if an entry already exists
            target_glasses = user.daily_target_glasses or self.settings.default_daily_glasses
            new_goal_ml = user.daily_target_ml or target_glasses * self.settings.glass_volume_ml
            stmt = select(DailyHydration).where(
                DailyHydration.user_id == telegram_id,
                DailyHydration.date == date.today(),
            )
            entry = session.exec(stmt).first()
            if entry:
                entry.goal_ml = new_goal_ml
                entry.updated_at = datetime.utcnow()
                session.add(entry)

            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def _get_or_create_user(self, session: Session, telegram_id: int) -> User:
        user = session.get(User, telegram_id)
        if user:
            return user

        user = User(
            telegram_id=telegram_id,
            timezone=self.settings.timezone,
            daily_target_glasses=self.settings.default_daily_glasses,
            daily_target_ml=self.settings.default_daily_glasses * self.settings.glass_volume_ml,
            reminder_start_hour=self.settings.hydration_start_hour,
            reminder_end_hour=self.settings.hydration_end_hour,
            reminder_interval_minutes=self.settings.reminder_interval_minutes,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(
            "event=user_created user_id={user_id} timezone={timezone} target_glasses={glasses} target_ml={target_ml} start_hour={start} end_hour={end} interval_min={interval}",
            user_id=user.telegram_id,
            timezone=user.timezone,
            glasses=user.daily_target_glasses,
            target_ml=user.daily_target_ml,
            start=user.reminder_start_hour,
            end=user.reminder_end_hour,
            interval=user.reminder_interval_minutes,
        )
        return user
