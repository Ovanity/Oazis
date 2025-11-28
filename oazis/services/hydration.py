"""Domain services for hydration tracking."""

import asyncio
from datetime import date, datetime
from typing import List

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from oazis.config import Settings
from oazis.db import DailyHydration, HydrationEvent, User
from oazis.db.session import session_scope


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
            target = user.daily_target_ml or self.settings.default_daily_target_ml

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

    def _get_or_create_user(self, session: Session, telegram_id: int) -> User:
        user = session.get(User, telegram_id)
        if user:
            return user

        user = User(
            telegram_id=telegram_id,
            timezone=self.settings.timezone,
            daily_target_ml=self.settings.default_daily_target_ml,
            reminder_start_hour=self.settings.hydration_start_hour,
            reminder_end_hour=self.settings.hydration_end_hour,
            reminder_interval_minutes=self.settings.reminder_interval_minutes,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
