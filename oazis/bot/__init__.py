"""Bot factory and handler registration."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from oazis.config import Settings
from oazis.scheduler import ReminderScheduler
from oazis.services.hydration import HydrationService

from .handlers import build_router


def create_bot(settings: Settings) -> Bot:
    """Instantiate aiogram Bot with common defaults."""
    return Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(service: HydrationService, reminder_scheduler: ReminderScheduler) -> Dispatcher:
    """Create a dispatcher and attach routers."""
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(service, reminder_scheduler))
    return dispatcher


__all__ = ["create_bot", "create_dispatcher"]
