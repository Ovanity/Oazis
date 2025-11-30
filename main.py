"""Entrypoint for the Oazis bot."""

import asyncio
import inspect
from pathlib import Path

from loguru import logger

from oazis.bot import create_bot, create_dispatcher
from oazis.config import get_settings
from oazis.db.session import get_engine, init_db
from oazis.logger import configure_logging
from oazis.scheduler import ReminderScheduler, create_scheduler
from oazis.services.hydration import HydrationService
from oazis.bot.commands import configure_bot_commands


def _ensure_sqlite_dir(database_url: str) -> None:
    """Create parent directories for SQLite files if needed."""
    if not database_url.startswith("sqlite:///"):
        return

    db_path = database_url.removeprefix("sqlite:///")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.debug)
    logger.info("Starting Oazis bot")

    _ensure_sqlite_dir(settings.database_url)
    engine = get_engine(settings.database_url, echo=settings.debug)
    init_db(engine)
    logger.info("Database initialized")

    hydration_service = HydrationService(engine, settings)

    bot = create_bot(settings)
    await configure_bot_commands(bot)
    me = await bot.get_me()
    if me.username:
        logger.info("Start link: https://t.me/{username}?start=go", username=me.username)
    scheduler = create_scheduler(settings)
    reminder_scheduler = ReminderScheduler(scheduler, bot, hydration_service, settings)
    await reminder_scheduler.schedule_for_all_users()
    scheduler.start()
    dispatcher = create_dispatcher(hydration_service, reminder_scheduler)
    logger.info("Scheduler started")

    try:
        await dispatcher.start_polling(bot)
    finally:
        shutdown_result = scheduler.shutdown(wait=False)
        if inspect.isawaitable(shutdown_result):
            await shutdown_result
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
