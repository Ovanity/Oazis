"""Inline keyboards shared across handlers."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from oazis.bot.formatting import format_volume_ml

DRINK_CALLBACK_PREFIX = "hydration:drink:"
REMINDER_PAUSE_TODAY = "reminder:pause:today"
REMINDER_RESUME = "reminder:resume"
GLASS_GOAL_PREFIX = "settings:glasses:"
REMINDER_WINDOW_PREFIX = "settings:window:"
REMINDER_INTERVAL_PREFIX = "settings:interval:"

GLASS_GOAL_OPTIONS = (4, 6, 8, 10)
REMINDER_WINDOWS = (
    ("8-22", "🌅 8h – 22h"),
    ("9-21", "🌤 9h – 21h"),
    ("10-20", "🌙 10h – 20h"),
)
REMINDER_FREQUENCIES = (
    (60, "⚡️ Toutes les 60 min"),
    (90, "🌿 Toutes les 90 min"),
    (120, "🕰 Toutes les 120 min"),
)
ONBOARD_START = "onboard:start"
ONBOARD_GOAL_PREFIX = "onboard:goal:"
ONBOARD_WINDOW_PREFIX = "onboard:window:"
ONBOARD_FREQ_PREFIX = "onboard:freq:"
ONBOARD_PROFILE_PREFIX = "onboard:profile:"
NAV_HUB = "nav:hub"
NAV_HYDRATION = "nav:hydration"
NAV_SETTINGS = "nav:settings"
NAV_STATS = "nav:stats"
NAV_RESTART_ONBOARDING = "nav:onboarding"


def hydration_log_keyboard(volume_ml: int = 250) -> InlineKeyboardMarkup:
    """Single large button to log a glass of water."""
    builder = InlineKeyboardBuilder()
    label = format_volume_ml(volume_ml)
    builder.button(
        text=f"🥤 J'ai bu {label}",
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


def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Commencer", callback_data=ONBOARD_START)
    builder.button(text="🏝️ Ouvrir le hub", callback_data=NAV_HUB)
    builder.adjust(1)
    return builder.as_markup()


def onboarding_goal_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for count in GLASS_GOAL_OPTIONS:
        builder.button(text=f"{count} verres / jour", callback_data=f"{ONBOARD_GOAL_PREFIX}{count}")
    builder.adjust(2, 2)
    return builder.as_markup()


def onboarding_window_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value, label in REMINDER_WINDOWS:
        builder.button(text=label, callback_data=f"{ONBOARD_WINDOW_PREFIX}{value}")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_frequency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for minutes, label in REMINDER_FREQUENCIES:
        builder.button(text=label, callback_data=f"{ONBOARD_FREQ_PREFIX}{minutes}")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_profile_keyboard() -> InlineKeyboardMarkup:
    """Bundled presets combining window + frequency to reduce friction."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🌿 Doux (9h–21h, 90 min)",
        callback_data=f"{ONBOARD_PROFILE_PREFIX}balanced",
    )
    builder.button(
        text="⚡️ Soutenu (8h–22h, 60 min)",
        callback_data=f"{ONBOARD_PROFILE_PREFIX}focus",
    )
    builder.button(
        text="🕰 Discret (10h–20h, 120 min)",
        callback_data=f"{ONBOARD_PROFILE_PREFIX}light",
    )
    builder.adjust(1)
    return builder.as_markup()


def hub_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏝️ Hub", callback_data=NAV_HUB)
    builder.button(text="💧 Hydratation", callback_data=NAV_HYDRATION)
    builder.button(text="📊 Statistiques", callback_data=NAV_STATS)
    builder.button(text="⚙️ Réglages", callback_data=NAV_SETTINGS)
    builder.adjust(1)
    return builder.as_markup()


def hydration_actions_keyboard(volume_ml: int = 250) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    label = format_volume_ml(volume_ml)
    builder.button(text=f"🥤 +1 verre ({label})", callback_data=f"{DRINK_CALLBACK_PREFIX}{volume_ml}")
    builder.button(text="📊 Statistiques", callback_data=NAV_STATS)
    builder.button(text="⚙️ Réglages", callback_data=NAV_SETTINGS)
    builder.button(text="🏝️ Hub", callback_data=NAV_HUB)
    builder.adjust(1, 2, 1)
    return builder.as_markup()


def reminder_actions_keyboard(volume_ml: int = 250) -> InlineKeyboardMarkup:
    """Focused keyboard for reminders: log only (pause via Réglages)."""
    builder = InlineKeyboardBuilder()
    label = format_volume_ml(volume_ml)
    builder.button(text=f"🥤 J'ai bu {label}", callback_data=f"{DRINK_CALLBACK_PREFIX}{volume_ml}")
    builder.adjust(1)
    return builder.as_markup()


def settings_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Objectif quotidien", callback_data=NAV_RESTART_ONBOARDING + ":goal")
    builder.button(text="🕒 Plage des rappels", callback_data=NAV_RESTART_ONBOARDING + ":window")
    builder.button(text="⏱️ Fréquence des rappels", callback_data=NAV_RESTART_ONBOARDING + ":freq")
    builder.button(text="🔕 Pause rappels (aujourd'hui)", callback_data=REMINDER_PAUSE_TODAY)
    builder.button(text="🔔 Reprendre les rappels", callback_data=REMINDER_RESUME)
    builder.button(text="🏝️ Hub", callback_data=NAV_HUB)
    builder.adjust(1)
    return builder.as_markup()
