"""Routers and handlers for the Telegram bot."""

from aiogram import Router

from oazis.services.hydration import HydrationService

from . import hydration, start


def build_router(service: HydrationService) -> Router:
    """Aggregate all routers."""
    router = Router(name="root")
    router.include_router(start.build_router(service))
    router.include_router(hydration.build_router(service))
    return router


__all__ = ["build_router"]

