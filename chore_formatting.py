"""Rules for choosing special chore display formats."""

import math

SECONDS_PER_DAY = 86400
ONE_TIME_ROTATION = -2


def _non_negative_number(value, setting_name):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{setting_name} must be a number") from exc

    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{setting_name} must be a finite, non-negative number")

    return number


def is_very_overdue(
    chore,
    enabled=True,
    threshold_percent=50,
    one_time_days=10,
):
    """Return whether a recurring or one-time chore is very overdue."""
    if not enabled:
        return False

    try:
        rotation_time = float(chore.get("rotationTime"))
        time_left = float(chore.get("timeLeftNext"))
    except (TypeError, ValueError):
        return False

    if time_left >= 0:
        return False

    overdue_seconds = -time_left

    if rotation_time == ONE_TIME_ROTATION:
        days = _non_negative_number(
            one_time_days, "very_overdue_one_time_days"
        )
        return overdue_seconds > days * SECONDS_PER_DAY

    if rotation_time <= 0:
        return False

    threshold = _non_negative_number(
        threshold_percent, "very_overdue_threshold_percent"
    )
    threshold_seconds = rotation_time * threshold / 100
    return overdue_seconds >= threshold_seconds
