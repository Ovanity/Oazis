"""Hydration-related commands."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from oazis.services.hydration import HydrationService


def build_router(service: HydrationService) -> Router:
    router = Router(name="hydration")

    @router.message(Command("drink"))
    async def confirm_drink(message: Message) -> None:
        if not message.from_user:
            return

        entry = await service.record_glass(message.from_user.id)
        await message.answer(
            f"👌 Noté. Tu as consommé {entry.consumed_ml}/{entry.goal_ml} ml aujourd'hui."
        )

    return router

