"""Routers and handlers for the Telegram bot."""

from aiogram import Router

from oazis.scheduler import ReminderScheduler
from oazis.services.hydration import HydrationService

from . import hydration, hub, settings, start


def build_router(service: HydrationService, reminder_scheduler: ReminderScheduler) -> Router:
    """Aggregate all routers."""
    router = Router(name="root")
    router.include_router(start.build_router(service, reminder_scheduler))
    router.include_router(hub.build_router(service, reminder_scheduler))
    router.include_router(settings.build_router(service, reminder_scheduler))
    router.include_router(hydration.build_router(service, reminder_scheduler))
    return router


__all__ = ["build_router"]
