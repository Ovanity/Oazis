"""Entrypoint for the Oazis bot."""

import asyncio
import inspect
from pathlib import Path

from loguru import logger

from oazis.bot import create_bot, create_dispatcher
from oazis.config import get_settings
from oazis.db.session import get_engine, init_db
from oazis.logger import configure_logging
from oazis.scheduler import create_scheduler, register_jobs
from oazis.services.hydration import HydrationService


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
    dispatcher = create_dispatcher(hydration_service)

    scheduler = create_scheduler(settings)
    register_jobs(scheduler, hydration_service, settings, bot)
    scheduler.start()
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
