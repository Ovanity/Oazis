"""Inline keyboards shared across handlers."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

DRINK_CALLBACK_PREFIX = "hydration:drink:"


def hydration_log_keyboard(volume_ml: int = 250) -> InlineKeyboardMarkup:
    """Single large button to log a glass of water."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🥤 J'ai bu {volume_ml} ml",
        callback_data=f"{DRINK_CALLBACK_PREFIX}{volume_ml}",
    )
    builder.adjust(1)  # One button per row to keep it large and easy to hit
    return builder.as_markup()
