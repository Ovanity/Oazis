"""Shared helpers for human-friendly formatting."""


def format_volume_ml(volume_ml: int) -> str:
    """Return a human-readable volume using ml, cl or L.

    Rules (roughly adapted to French habits):
    - >= 1000 ml → liters, 1 decimal if needed: 1500 -> '1,5 L'
    - else if divisible by 10 → centiliters: 250 -> '25 cl'
    - otherwise → milliliters.
    """
    if volume_ml <= 0:
        return "0 ml"

    # Liters
    if volume_ml >= 1000:
        liters = volume_ml / 1000
        if float(int(liters)) == liters:
            return f"{int(liters)} L"
        return f"{liters:.1f}".replace(".", ",") + " L"

    # Centiliters when it falls nicely
    if volume_ml % 10 == 0:
        cl = volume_ml // 10
        return f"{cl} cl"

    return f"{volume_ml} ml"


def format_progress(consumed_ml: int, goal_ml: int) -> str:
    """Return a string like '75 cl / 2 L'."""
    return f"{format_volume_ml(consumed_ml)} / {format_volume_ml(goal_ml)}"


def format_interval(minutes: int) -> str:
    """Return a human-friendly interval string (e.g., '1 h', '1 h 30', '45 min')."""
    if minutes <= 0:
        return "—"
    hours = minutes // 60
    mins = minutes % 60
    parts: list[str] = []
    if hours:
        parts.append(f"{hours} h")
    if mins:
        parts.append(f"{mins} min")
    if not parts:
        return "0 min"
    return " ".join(parts)
