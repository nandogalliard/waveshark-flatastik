"""Rules for choosing special chore display formats."""

import math

SECONDS_PER_DAY = 86400
ONE_TIME_ROTATION = -2

UPCOMING = "upcoming"
TODAY = "today"
OVERDUE = "overdue"
VERY_OVERDUE = "very_overdue"

TASK_TEXT_Y_OFFSET = 2
VERY_OVERDUE_FRAME_WIDTH = 6


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


def get_chore_display_state(
    chore,
    enable_very_overdue_format=True,
    very_overdue_threshold_percent=50,
    very_overdue_one_time_days=10,
):
    """Classify a chore into one of the supported task-row display states."""
    if is_very_overdue(
        chore,
        enable_very_overdue_format,
        very_overdue_threshold_percent,
        very_overdue_one_time_days,
    ):
        return VERY_OVERDUE

    time_left = float(chore.get("timeLeftNext"))
    if time_left < 0:
        return OVERDUE
    if time_left < SECONDS_PER_DAY:
        return TODAY
    return UPCOMING


def _draw_columns(draw, columns, text_y, font, fill):
    for x_position, text in columns:
        draw.text((x_position, text_y), text, font=font, fill=fill)


def draw_chore_row(
    draw_black,
    draw_red,
    state,
    row_box,
    columns,
    font,
):
    """Draw one chore row on the e-paper display's black and red planes."""
    row_left, row_top, row_right, row_bottom = row_box
    text_y = row_top + TASK_TEXT_Y_OFFSET

    if state == VERY_OVERDUE:
        for inset in range(VERY_OVERDUE_FRAME_WIDTH):
            draw_black.rectangle(
                (
                    row_left + inset,
                    row_top + inset,
                    row_right - inset,
                    row_bottom - inset,
                ),
                outline=0,
            )
        draw_red.rectangle(
            (
                row_left + VERY_OVERDUE_FRAME_WIDTH,
                row_top + VERY_OVERDUE_FRAME_WIDTH,
                row_right - VERY_OVERDUE_FRAME_WIDTH,
                row_bottom - VERY_OVERDUE_FRAME_WIDTH,
            ),
            fill=0,
        )

        # Clear both color planes so every glyph stays white, including
        # descenders that reach into the thicker bottom frame.
        _draw_columns(draw_red, columns, text_y, font, fill=255)
        _draw_columns(draw_black, columns, text_y, font, fill=255)
    elif state == OVERDUE:
        draw_red.rectangle(row_box, fill=0)
        _draw_columns(draw_red, columns, text_y, font, fill=255)
    elif state == TODAY:
        draw_black.rectangle(row_box, fill=0)
        _draw_columns(draw_black, columns, text_y, font, fill=255)
    elif state == UPCOMING:
        _draw_columns(draw_black, columns, text_y, font, fill=0)
    else:
        raise ValueError(f"Unsupported chore display state: {state}")
