import unittest

from chore_formatting import is_very_overdue


DAY = 86400


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


if __name__ == "__main__":
    unittest.main()
