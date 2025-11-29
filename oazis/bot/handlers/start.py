"""Start command handler and onboarding flow."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from loguru import logger

from oazis.bot.keyboards import (
    ONBOARD_PROFILE_PREFIX,
    ONBOARD_GOAL_PREFIX,
    ONBOARD_START,
    hub_keyboard,
    onboarding_goal_keyboard,
    onboarding_profile_keyboard,
    start_keyboard,
)
from oazis.services.hydration import HydrationService


def build_router(service: HydrationService) -> Router:
    router = Router(name="start")

    @router.message(CommandStart())
    async def handle_start(message: Message) -> None:
        if not message.from_user:
            return

        user = await service.ensure_user(message.from_user.id)
        logger.info(
            "event=user_start user_id={user_id} chat_id={chat_id} chat_type={chat_type} username={username} language={language} is_premium={is_premium}",
            user_id=user.telegram_id,
            chat_id=message.chat.id if message.chat else None,
            chat_type=message.chat.type if message.chat else None,
            username=message.from_user.username,
            language=message.from_user.language_code,
            is_premium=getattr(message.from_user, "is_premium", False),
        )

        await message.answer(
            "👋 <b>Bienvenue sur Oazis</b>\n\n"
            "Pour t'aider à boire assez chaque jour, sans prise de tête.\n\n"
            "On règle ton programme en quelques clics, puis tout se gère depuis le hub.\n\n"
            "<i>Avec amour, par Martin.</i>",
            reply_markup=start_keyboard(),
        )

    @router.callback_query(lambda c: c.data == ONBOARD_START)
    async def start_onboarding(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        await callback.answer()
        await callback.message.answer(
            "🚀 <b>Onboarding</b>\n\n"
            "💧 Choisis ton objectif quotidien (entre 4 et 10 verres).\n\n"
            "Tu pourras toujours ajuster ça plus tard dans les réglages.",
            reply_markup=onboarding_goal_keyboard(),
        )

    @router.callback_query(lambda c: c.data and c.data.startswith(ONBOARD_GOAL_PREFIX))
    async def onboarding_goal(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        try:
            count = int(callback.data.removeprefix(ONBOARD_GOAL_PREFIX))
        except ValueError:
            await callback.answer("Choix invalide.", show_alert=True)
            return
        if not 4 <= count <= 10:
            await callback.answer("Choisis entre 4 et 10 verres.", show_alert=True)
            return
        await service.update_user_preferences(callback.from_user.id, daily_target_glasses=count)
        logger.info(
            "event=onboarding_goal_set user_id={user_id} chat_id={chat_id} chat_type={chat_type} goal_glasses={goal} goal_ml={goal_ml} language={language} is_premium={is_premium}",
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id if callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message.chat else None,
            goal=count,
            goal_ml=count * service.settings.glass_volume_ml,
            language=callback.from_user.language_code,
            is_premium=getattr(callback.from_user, "is_premium", False),
        )
        await callback.answer("Objectif enregistré.")
        await callback.message.answer(
            f"🎯 Objectif réglé sur <b>{count} verres / jour</b>.\n\n"
            "⏱️ Choisis maintenant le type de rappels qui te convient le mieux.",
            reply_markup=onboarding_profile_keyboard(),
        )

    @router.callback_query(lambda c: c.data and c.data.startswith(ONBOARD_PROFILE_PREFIX))
    async def onboarding_profile(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        profile = callback.data.removeprefix(ONBOARD_PROFILE_PREFIX)
        if profile == "balanced":
            start, end, interval = 9, 21, 90
            label = "🌿 Doux — quelques rappels sur la journée (9h–21h, ~1h30)"
        elif profile == "focus":
            start, end, interval = 8, 22, 60
            label = "⚡️ Focus — rappels fréquents pour ancrer l’habitude (8h–22h, ~1h)"
        elif profile == "light":
            start, end, interval = 10, 20, 120
            label = "🕰 Discret — plus rares pour rester léger (10h–20h, ~2h)"
        else:
            await callback.answer("Choix invalide.", show_alert=True)
            return

        await service.update_user_preferences(
            callback.from_user.id,
            reminder_start_hour=start,
            reminder_end_hour=end,
            reminder_interval_minutes=interval,
        )
        await callback.answer("Rappels enregistrés.")

        user = await service.ensure_user(callback.from_user.id)
        start = user.reminder_start_hour
        end = user.reminder_end_hour
        goal = user.daily_target_glasses or 0
        logger.info(
            "event=onboarding_profile_set user_id={user_id} chat_id={chat_id} chat_type={chat_type} profile={profile} start_hour={start} end_hour={end} interval_min={interval} goal_glasses={goal} language={language} is_premium={is_premium}",
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id if callback.message.chat else None,
            chat_type=callback.message.chat.type if callback.message.chat else None,
            profile=profile,
            start=start,
            end=end,
            interval=interval,
            goal=goal,
            language=callback.from_user.language_code,
            is_premium=getattr(callback.from_user, "is_premium", False),
        )

        summary = (
            "✅ <b>Paramètres enregistrés</b>\n\n"
            f"• Objectif : <b>{goal} verres / jour</b>\n"
            f"• Rappels : <b>{label}</b>\n\n"
            "Tu es prêt.\n"
            "Utilise le bouton 🏝️ Hub ci-dessous pour tout gérer tranquillement."
        )
        await callback.message.answer(summary, reply_markup=hub_keyboard())

    return router
