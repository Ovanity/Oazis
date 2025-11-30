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
from oazis.scheduler import ReminderScheduler
from oazis.services.hydration import HydrationService


def build_router(service: HydrationService, reminder_scheduler: ReminderScheduler) -> Router:
    router = Router(name="hub")

    @router.message(Command("hub"))
    async def open_hub_command(message: Message) -> None:
        if not message.from_user:
            return
        await _send_hub(
            message.answer,
            service,
            message.from_user.id,
            reminder_scheduler,
            source="command",
            chat_id=message.chat.id if message.chat else None,
            chat_type=message.chat.type if message.chat else None,
        )

    @router.callback_query(lambda c: c.data == NAV_HUB)
    async def open_hub_callback(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await callback.answer()
        await _send_hub(
            callback.message.answer,
            service,
            callback.from_user.id,
            reminder_scheduler,
            source="callback",
            chat_id=callback.message.chat.id if callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message.chat else None,
        )

    @router.callback_query(lambda c: c.data == NAV_HYDRATION)
    async def open_hydration(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await callback.answer()
        await _send_hydration_view(
            callback.message.answer,
            service,
            callback.from_user.id,
            reminder_scheduler,
            source="callback",
            chat_id=callback.message.chat.id if callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message.chat else None,
        )

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
        stats_text = await _build_stats_text(
            service,
            callback.from_user.id,
            source="callback",
            chat_id=callback.message.chat.id if callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message.chat else None,
        )
        await callback.message.answer(stats_text, reply_markup=hub_keyboard())

    @router.message(Command("stats"))
    async def stats_command(message: Message) -> None:
        if not message.from_user:
            return
        stats_text = await _build_stats_text(
            service,
            message.from_user.id,
            source="command",
            chat_id=message.chat.id if message.chat else None,
            chat_type=message.chat.type if message.chat else None,
        )
        await message.answer(stats_text, reply_markup=hub_keyboard())

    return router


async def _send_hub(send_func, service: HydrationService, user_id: int, reminder_scheduler: ReminderScheduler, *, source: str, chat_id: int | None, chat_type: str | None) -> None:
    user = await service.ensure_user(user_id)
    await reminder_scheduler.schedule_for_user(user_id)
    entry = await service.get_today_entry(user_id)
    target_ml = entry.goal_ml if entry else user.daily_target_ml or service.settings.default_daily_target_ml
    consumed_ml = entry.consumed_ml if entry else 0
    goal_reached = consumed_ml >= target_ml
    logger.info(
        "event=hub_opened user_id={user_id} chat_id={chat_id} chat_type={chat_type} source={source} target_ml={target_ml} consumed_ml={consumed_ml} goal_reached={goal_reached}",
        user_id=user_id,
        chat_id=chat_id,
        chat_type=chat_type,
        source=source,
        target_ml=target_ml,
        consumed_ml=consumed_ml,
        goal_reached=goal_reached,
    )

    text = (
        "🏝️ <b>Oazis</b>\n\n"
        "Ton espace hydratation, tout en douceur.\n\n"
        "💧 <b>Hydratation</b>\n\n"
        f"• Objectif : <b>{format_volume_ml(target_ml)}</b>\n"
        f"• Enregistré : <b>{format_volume_ml(consumed_ml)}</b>\n"
        "• Rappels : ajuste ça dans ⚙️ Réglages si besoin\n"
    )
    if goal_reached:
        text += (
            "\n🎉 <b>Objectif du jour atteint</b>\n"
            "Bravo, tu peux te détendre pour aujourd'hui."
        )

    text += "\n\n<i>Avec amour, par Martin.</i>"
    await send_func(text, reply_markup=hub_keyboard())


async def _send_hydration_view(send_func, service: HydrationService, user_id: int, reminder_scheduler: ReminderScheduler, *, source: str, chat_id: int | None, chat_type: str | None) -> None:
    user = await service.ensure_user(user_id)
    await reminder_scheduler.schedule_for_user(user_id)
    entry = await service.get_today_entry(user_id)

    target_ml = entry.goal_ml if entry else user.daily_target_ml or service.settings.default_daily_target_ml
    consumed_ml = entry.consumed_ml if entry else 0
    start = user.reminder_start_hour or service.settings.hydration_start_hour
    end = user.reminder_end_hour or service.settings.hydration_end_hour
    interval = user.reminder_interval_minutes or service.settings.reminder_interval_minutes
    goal_glasses = user.daily_target_glasses or service.settings.default_daily_glasses
    logger.info(
        "event=hydration_view_opened user_id={user_id} chat_id={chat_id} chat_type={chat_type} source={source} target_ml={target_ml} consumed_ml={consumed_ml} goal_glasses={goal_glasses} start_hour={start} end_hour={end} interval_min={interval}",
        user_id=user_id,
        chat_id=chat_id,
        chat_type=chat_type,
        source=source,
        target_ml=target_ml,
        consumed_ml=consumed_ml,
        goal_glasses=goal_glasses,
        start=start,
        end=end,
        interval=interval,
    )

    text = (
        "💧 <b>Hydratation du jour</b>\n\n"
        f"• Objectif : <b>{goal_glasses} verres</b> (~{format_volume_ml(target_ml)})\n"
        f"• Enregistré : <b>{format_progress(consumed_ml, target_ml)}</b>\n"
        f"• Rappels : toutes les <b>{interval} min</b> entre <b>{start}h</b> et <b>{end}h</b>\n\n"
        "👉 Utilise les boutons ci-dessous pour noter un verre."
    )
    await send_func(text, reply_markup=hydration_actions_keyboard(service.settings.glass_volume_ml))


async def _build_stats_text(service: HydrationService, user_id: int, *, source: str, chat_id: int | None, chat_type: str | None) -> str:
    await service.ensure_user(user_id)
    stats = await service.get_stats(user_id, days=30)
    avg_ml = stats.average_ml
    goal_hits = stats.goal_hits
    logger.info(
        "event=stats_viewed user_id={user_id} chat_id={chat_id} chat_type={chat_type} source={source} days_considered={days} today_consumed_ml={today_consumed} today_goal_ml={today_goal} average_ml={avg_ml} goal_hits={goal_hits}",
        user_id=user_id,
        chat_id=chat_id,
        chat_type=chat_type,
        source=source,
        days=stats.days_considered,
        today_consumed=stats.today_consumed_ml,
        today_goal=stats.today_goal_ml,
        avg_ml=avg_ml,
        goal_hits=goal_hits,
    )
    text = (
        "📊 <b>Statistiques</b>\n\n"
        f"• Aujourd'hui : <b>{format_progress(stats.today_consumed_ml, stats.today_goal_ml)}</b>\n"
        f"• Moyenne sur {stats.days_considered} jours : <b>{format_volume_ml(avg_ml)}/jour</b>\n"
        f"• Jours avec objectif atteint : <b>{goal_hits}</b>\n\n"
    )
    if goal_hits >= 5:
        text += "🌟 Beau rythme, continue comme ça."
    elif goal_hits >= 2:
        text += "🧩 Les habitudes se construisent pas à pas."
    else:
        text += "✨ Commence en douceur, un verre après l'autre."
    return text
