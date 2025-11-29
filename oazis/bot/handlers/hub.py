"""Hub navigation and module entry points."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from oazis.bot.formatting import format_progress, format_volume_ml
from oazis.bot.keyboards import (
    NAV_HUB,
    NAV_HYDRATION,
    NAV_SETTINGS,
    NAV_STATS,
    hub_keyboard,
    hydration_actions_keyboard,
    settings_menu_keyboard,
)
from oazis.services.hydration import HydrationService


def build_router(service: HydrationService) -> Router:
    router = Router(name="hub")

    @router.message(Command("hub"))
    async def open_hub_command(message: Message) -> None:
        if not message.from_user:
            return
        await _send_hub(message.answer, service, message.from_user.id)

    @router.callback_query(lambda c: c.data == NAV_HUB)
    async def open_hub_callback(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await callback.answer()
        await _send_hub(callback.message.answer, service, callback.from_user.id)

    @router.callback_query(lambda c: c.data == NAV_HYDRATION)
    async def open_hydration(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await callback.answer()
        await _send_hydration_view(callback.message.answer, service, callback.from_user.id)

    @router.callback_query(lambda c: c.data == NAV_SETTINGS)
    async def open_settings(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await callback.answer()
        await callback.message.answer(
            "⚙️ <b>Réglages</b>\n"
            "Ajuste ton programme en un clic.",
            reply_markup=settings_menu_keyboard(),
        )

    @router.callback_query(lambda c: c.data == NAV_STATS)
    async def open_stats(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await callback.answer()
        stats_text = await _build_stats_text(service, callback.from_user.id)
        await callback.message.answer(stats_text, reply_markup=hub_keyboard())

    @router.message(Command("stats"))
    async def stats_command(message: Message) -> None:
        if not message.from_user:
            return
        stats_text = await _build_stats_text(service, message.from_user.id)
        await message.answer(stats_text, reply_markup=hub_keyboard())

    return router


async def _send_hub(send_func, service: HydrationService, user_id: int) -> None:
    user = await service.ensure_user(user_id)
    entry = await service.get_today_entry(user_id)
    target_ml = entry.goal_ml if entry else user.daily_target_ml or service.settings.default_daily_target_ml
    consumed_ml = entry.consumed_ml if entry else 0
    goal_reached = consumed_ml >= target_ml

    text = (
        "🏝️ <b>Oazis</b>\n"
        "Ton espace hydratation, en douceur.\n\n"
        "💧 <b>Hydratation</b>\n"
        f"• Objectif : <b>{format_volume_ml(target_ml)}</b>\n"
        f"• Enregistré : <b>{format_volume_ml(consumed_ml)}</b>\n"
        "• Rappels : ajuste dans ⚙️ Réglages si besoin\n"
    )
    if goal_reached:
        text += "\n🎉 <b>Objectif du jour atteint</b> — bravo, tu peux te détendre."

    text += "\n\n<i>Avec amour, par Martin.</i>"
    await send_func(text, reply_markup=hub_keyboard())


async def _send_hydration_view(send_func, service: HydrationService, user_id: int) -> None:
    user = await service.ensure_user(user_id)
    entry = await service.get_today_entry(user_id)

    target_ml = entry.goal_ml if entry else user.daily_target_ml or service.settings.default_daily_target_ml
    consumed_ml = entry.consumed_ml if entry else 0
    start = user.reminder_start_hour or service.settings.hydration_start_hour
    end = user.reminder_end_hour or service.settings.hydration_end_hour
    interval = user.reminder_interval_minutes or service.settings.reminder_interval_minutes
    goal_glasses = user.daily_target_glasses or service.settings.default_daily_glasses

    text = (
        "💧 <b>Hydratation du jour</b>\n\n"
        f"• Objectif : <b>{goal_glasses} verres</b> (~{format_volume_ml(target_ml)})\n"
        f"• Enregistré : <b>{format_progress(consumed_ml, target_ml)}</b>\n"
        f"• Rappels : toutes les <b>{interval} min</b> entre <b>{start}h</b> et <b>{end}h</b>\n\n"
        "👉 Appuie ci-dessous pour noter un verre."
    )
    await send_func(text, reply_markup=hydration_actions_keyboard(service.settings.glass_volume_ml))


async def _build_stats_text(service: HydrationService, user_id: int) -> str:
    await service.ensure_user(user_id)
    stats = await service.get_stats(user_id, days=30)
    avg_ml = stats.average_ml
    goal_hits = stats.goal_hits
    text = (
        "📊 <b>Statistiques</b>\n"
        f"• Aujourd'hui : <b>{format_progress(stats.today_consumed_ml, stats.today_goal_ml)}</b>\n"
        f"• Moyenne {stats.days_considered}j : <b>{format_volume_ml(avg_ml)}/jour</b>\n"
        f"• Jours avec objectif atteint ({stats.days_considered}j) : <b>{goal_hits}</b>\n"
    )
    if goal_hits >= 5:
        text += "🌟 Beau rythme, continue comme ça."
    elif goal_hits >= 2:
        text += "🧩 Les habitudes se construisent pas à pas."
    else:
        text += "✨ Commence en douceur, un verre après l'autre."
    return text
