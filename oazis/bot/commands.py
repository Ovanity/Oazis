"""Bot command menu configuration."""

from aiogram import Bot
from aiogram.types import BotCommand


async def configure_bot_commands(bot: Bot) -> None:
    """Expose main commands as buttons in the Telegram command menu."""
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Démarrer Oazis"),
            BotCommand(command="drink", description="Enregistrer un verre (250 ml)"),
        ]
    )
