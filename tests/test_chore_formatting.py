import unittest

from chore_formatting import (
    OVERDUE,
    TODAY,
    UPCOMING,
    VERY_OVERDUE,
    VERY_OVERDUE_FRAME_WIDTH,
    draw_chore_row,
    get_chore_display_state,
    is_very_overdue,
)


DAY = 86400


class RecordingDraw:
    def __init__(self):
        self.rectangles = []
        self.texts = []

    def rectangle(self, box, **options):
        self.rectangles.append((box, options))

    def text(self, position, text, **options):
        self.texts.append((position, text, options))


class VeryOverdueTests(unittest.TestCase):
    def test_fourteen_day_chore_reaches_fifty_percent_at_seven_days(self):
        chore = {"rotationTime": 14 * DAY, "timeLeftNext": -7 * DAY}

        self.assertTrue(is_very_overdue(chore, True, 50))

    def test_chore_below_threshold_is_not_very_overdue(self):
        chore = {"rotationTime": 14 * DAY, "timeLeftNext": -(7 * DAY - 1)}

        self.assertFalse(is_very_overdue(chore, True, 50))

    def test_disabled_format_never_marks_a_chore(self):
        chore = {"rotationTime": 14 * DAY, "timeLeftNext": -30 * DAY}

        self.assertFalse(is_very_overdue(chore, False, 50))

    def test_upcoming_chore_is_not_very_overdue(self):
        chore = {"rotationTime": 14 * DAY, "timeLeftNext": DAY}

        self.assertFalse(is_very_overdue(chore, True, 50))

    def test_non_recurring_or_missing_frequency_uses_normal_format(self):
        self.assertFalse(
            is_very_overdue({"rotationTime": -1, "timeLeftNext": -DAY}, True, 50)
        )
        self.assertFalse(is_very_overdue({"timeLeftNext": -DAY}, True, 50))

    def test_one_time_chore_is_very_overdue_after_ten_days(self):
        exactly_ten_days = {"rotationTime": -2, "timeLeftNext": -10 * DAY}
        more_than_ten_days = {
            "rotationTime": -2,
            "timeLeftNext": -(10 * DAY + 1),
        }

        self.assertFalse(is_very_overdue(exactly_ten_days, True, 50, 10))
        self.assertTrue(is_very_overdue(more_than_ten_days, True, 50, 10))

    def test_only_when_necessary_task_never_uses_special_format(self):
        chore = {"rotationTime": -1, "timeLeftNext": -100 * DAY}

        self.assertFalse(is_very_overdue(chore, True, 50, 10))

    def test_custom_percentage_is_supported(self):
        chore = {"rotationTime": 10 * DAY, "timeLeftNext": -10 * DAY}

        self.assertTrue(is_very_overdue(chore, True, 100))

    def test_negative_or_non_finite_threshold_is_rejected(self):
        chore = {"rotationTime": 14 * DAY, "timeLeftNext": -7 * DAY}

        for threshold in (-1, float("inf"), "not-a-number"):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    is_very_overdue(chore, True, threshold)

    def test_invalid_one_time_threshold_is_rejected(self):
        chore = {"rotationTime": -2, "timeLeftNext": -11 * DAY}

        with self.assertRaises(ValueError):
            is_very_overdue(chore, True, 50, -1)


class ChoreDisplayStateTests(unittest.TestCase):
    def test_all_display_states(self):
        cases = (
            ({"rotationTime": 14 * DAY, "timeLeftNext": 2 * DAY}, UPCOMING),
            ({"rotationTime": 14 * DAY, "timeLeftNext": DAY - 1}, TODAY),
            ({"rotationTime": 14 * DAY, "timeLeftNext": -DAY}, OVERDUE),
            (
                {"rotationTime": 14 * DAY, "timeLeftNext": -7 * DAY},
                VERY_OVERDUE,
            ),
            (
                {"rotationTime": -2, "timeLeftNext": -(10 * DAY + 1)},
                VERY_OVERDUE,
            ),
        )

        for chore, expected_state in cases:
            with self.subTest(chore=chore):
                self.assertEqual(
                    get_chore_display_state(chore, True, 50, 10),
                    expected_state,
                )

    def test_disabling_special_format_falls_back_to_overdue(self):
        chore = {"rotationTime": 14 * DAY, "timeLeftNext": -20 * DAY}

        self.assertEqual(
            get_chore_display_state(chore, False, 50, 10),
            OVERDUE,
        )


class ChoreRowRenderingTests(unittest.TestCase):
    row_box = (0, 10, 99, 35)
    columns = ((10, "Title"), (40, "Person"), (70, "Time"))
    font = object()

    def draw(self, state):
        black = RecordingDraw()
        red = RecordingDraw()
        draw_chore_row(
            black,
            red,
            state,
            self.row_box,
            self.columns,
            self.font,
        )
        return black, red

    def assert_text_calls(self, calls, expected_fill):
        self.assertEqual(len(calls), 3)
        for (position, text, options), (expected_x, expected_text) in zip(
            calls, self.columns
        ):
            self.assertEqual(position, (expected_x, 12))
            self.assertEqual(text, expected_text)
            self.assertIs(options["font"], self.font)
            self.assertEqual(options["fill"], expected_fill)

    def test_upcoming_row_is_black_text_on_white(self):
        black, red = self.draw(UPCOMING)

        self.assertEqual(black.rectangles, [])
        self.assertEqual(red.rectangles, [])
        self.assert_text_calls(black.texts, 0)
        self.assertEqual(red.texts, [])

    def test_today_row_is_white_text_on_black(self):
        black, red = self.draw(TODAY)

        self.assertEqual(black.rectangles, [(self.row_box, {"fill": 0})])
        self.assert_text_calls(black.texts, 255)
        self.assertEqual(red.rectangles, [])
        self.assertEqual(red.texts, [])

    def test_overdue_row_is_white_text_on_red(self):
        black, red = self.draw(OVERDUE)

        self.assertEqual(black.rectangles, [])
        self.assertEqual(black.texts, [])
        self.assertEqual(red.rectangles, [(self.row_box, {"fill": 0})])
        self.assert_text_calls(red.texts, 255)

    def test_very_overdue_row_has_six_pixel_frame_and_white_text(self):
        black, red = self.draw(VERY_OVERDUE)

        self.assertEqual(len(black.rectangles), VERY_OVERDUE_FRAME_WIDTH)
        self.assertEqual(
            black.rectangles[0],
            ((0, 10, 99, 35), {"outline": 0}),
        )
        self.assertEqual(
            black.rectangles[-1],
            ((5, 15, 94, 30), {"outline": 0}),
        )
        self.assertEqual(
            red.rectangles,
            [((6, 16, 93, 29), {"fill": 0})],
        )
        self.assert_text_calls(black.texts, 255)
        self.assert_text_calls(red.texts, 255)

    def test_unknown_display_state_is_rejected(self):
        with self.assertRaises(ValueError):
            self.draw("unknown")


if __name__ == "__main__":
    unittest.main()
