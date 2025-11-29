"""Hydration-related commands and inline buttons."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from oazis.bot.keyboards import DRINK_CALLBACK_PREFIX, hydration_log_keyboard
from oazis.services.hydration import HydrationService


def build_router(service: HydrationService) -> Router:
    router = Router(name="hydration")

    @router.message(Command("drink"))
    async def confirm_drink(message: Message) -> None:
        if not message.from_user:
            return

        entry = await service.record_glass(message.from_user.id)
        await message.answer(
            f"👌 Noté. Tu as consommé {entry.consumed_ml}/{entry.goal_ml} ml aujourd'hui.",
            reply_markup=hydration_log_keyboard(),
        )

    @router.callback_query(F.data.startswith(DRINK_CALLBACK_PREFIX))
    async def handle_drink_button(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data:
            await callback.answer("Action impossible.", show_alert=True)
            return

        volume_ml = _extract_volume(callback.data)
        if volume_ml is None:
            await callback.answer("Bouton invalide.", show_alert=True)
            return

        entry = await service.record_glass(callback.from_user.id, volume_ml=volume_ml)
        response_text = f"👌 Noté. Tu as consommé {entry.consumed_ml}/{entry.goal_ml} ml aujourd'hui."

        if callback.message:
            await callback.message.answer(response_text, reply_markup=hydration_log_keyboard(volume_ml))
        await callback.answer("Hydratation enregistrée.")

    return router


def _extract_volume(callback_data: str) -> int | None:
    """Return the volume encoded in the callback data, or None if malformed."""
    if not callback_data.startswith(DRINK_CALLBACK_PREFIX):
        return None

    payload = callback_data.removeprefix(DRINK_CALLBACK_PREFIX)
    try:
        return int(payload)
    except ValueError:
        return None
