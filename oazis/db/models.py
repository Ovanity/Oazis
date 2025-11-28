"""Persistence models for hydration tracking."""

from datetime import date, datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """Telegram user registered in the bot."""

    telegram_id: int = Field(primary_key=True, description="Telegram user id")
    role: str = Field(default="user")
    timezone: Optional[str] = Field(default=None, description="Preferred timezone for reminders")
    daily_target_ml: Optional[int] = Field(default=None, description="Custom daily water target")
    reminder_start_hour: Optional[int] = Field(default=None)
    reminder_end_hour: Optional[int] = Field(default=None)
    reminder_interval_minutes: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    hydration_days: List["DailyHydration"] = Relationship(back_populates="user")
    events: List["HydrationEvent"] = Relationship(back_populates="user")


class DailyHydration(SQLModel, table=True):
    """Aggregated hydration metrics for a user and a given date."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.telegram_id")
    date: date
    goal_ml: int
    consumed_ml: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="hydration_days")


class HydrationEvent(SQLModel, table=True):
    """Timeline of hydration-related events."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.telegram_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(description="e.g. reminder_sent, glass_logged")
    notes: Optional[str] = Field(default=None, description="Optional metadata or payload")

    user: User = Relationship(back_populates="events")

