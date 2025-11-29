"""Inline keyboards shared across handlers."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

DRINK_CALLBACK_PREFIX = "hydration:drink:"
GLASS_GOAL_PREFIX = "settings:glasses:"
REMINDER_WINDOW_PREFIX = "settings:window:"
REMINDER_INTERVAL_PREFIX = "settings:interval:"

GLASS_GOAL_OPTIONS = (4, 6, 8, 10)
REMINDER_WINDOWS = (
    ("8-22", "8h - 22h"),
    ("9-21", "9h - 21h"),
    ("10-20", "10h - 20h"),
)
REMINDER_FREQUENCIES = (
    (60, "Toutes les 60 min"),
    (90, "Toutes les 90 min"),
    (120, "Toutes les 120 min"),
)


def hydration_log_keyboard(volume_ml: int = 250) -> InlineKeyboardMarkup:
    """Single large button to log a glass of water."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🥤 J'ai bu {volume_ml} ml",
        callback_data=f"{DRINK_CALLBACK_PREFIX}{volume_ml}",
    )
    builder.adjust(1)  # One button per row to keep it large and easy to hit
    return builder.as_markup()


def glasses_goal_keyboard() -> InlineKeyboardMarkup:
    """Buttons for selecting a daily glass target."""
    builder = InlineKeyboardBuilder()
    for count in GLASS_GOAL_OPTIONS:
        builder.button(text=f"{count} verres / jour", callback_data=f"{GLASS_GOAL_PREFIX}{count}")
    builder.adjust(2, 2)
    return builder.as_markup()


def reminder_window_keyboard() -> InlineKeyboardMarkup:
    """Preset buttons for reminder windows."""
    builder = InlineKeyboardBuilder()
    for value, label in REMINDER_WINDOWS:
        builder.button(text=label, callback_data=f"{REMINDER_WINDOW_PREFIX}{value}")
    builder.adjust(1)
    return builder.as_markup()


def reminder_frequency_keyboard() -> InlineKeyboardMarkup:
    """Preset buttons for reminder frequencies."""
    builder = InlineKeyboardBuilder()
    for minutes, label in REMINDER_FREQUENCIES:
        builder.button(text=label, callback_data=f"{REMINDER_INTERVAL_PREFIX}{minutes}")
    builder.adjust(1)
    return builder.as_markup()
