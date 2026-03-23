"""Tests for auto_update_scheduler.next_fire_time and parse_schedule."""

import calendar
from datetime import datetime, timezone

from thymis_controller.auto_update_scheduler import (
    DEFAULT_SCHEDULE,
    next_fire_time,
    parse_schedule,
)


def utc(year, month, day, hour=0, minute=0, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# parse_schedule
# ---------------------------------------------------------------------------


class TestParseSchedule:
    def test_valid_daily(self):
        s = parse_schedule(
            '{"frequency": "daily", "time": "04:30", "weekdays": [0, 1]}'
        )
        assert s["frequency"] == "daily"
        assert s["time"] == "04:30"

    def test_valid_weekly(self):
        s = parse_schedule('{"frequency": "weekly", "time": "03:00", "weekday": 0}')
        assert s["weekday"] == 0

    def test_valid_monthly(self):
        s = parse_schedule(
            '{"frequency": "monthly", "time": "02:00", "day_of_month": 15}'
        )
        assert s["day_of_month"] == 15

    def test_valid_monthly_weekday(self):
        s = parse_schedule(
            '{"frequency": "monthly_weekday", "time": "03:00", "nth_weekday": 1, "weekday": 0}'
        )
        assert s["nth_weekday"] == 1

    def test_hourly_falls_back_to_default(self):
        # hourly is no longer a valid frequency
        assert parse_schedule('{"frequency": "hourly"}') == DEFAULT_SCHEDULE

    def test_invalid_json_falls_back_to_default(self):
        assert parse_schedule("not-json") == DEFAULT_SCHEDULE

    def test_unknown_frequency_falls_back_to_default(self):
        assert parse_schedule('{"frequency": "minutely"}') == DEFAULT_SCHEDULE

    def test_empty_string_falls_back_to_default(self):
        assert parse_schedule("") == DEFAULT_SCHEDULE


# ---------------------------------------------------------------------------
# next_fire_time — daily (multi-weekday, like old "weekly")
# ---------------------------------------------------------------------------


class TestDaily:
    def test_fires_today_when_weekday_matches_and_time_not_yet_reached(self):
        # 2024-03-11 is Monday (weekday 0)
        schedule = {"frequency": "daily", "time": "03:00", "weekdays": [0]}
        after = utc(2024, 3, 11, 2, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 11, 3, 0, 0)

    def test_skips_today_when_weekday_matches_but_time_passed(self):
        # Monday, 03:00 already passed — next Monday
        schedule = {"frequency": "daily", "time": "03:00", "weekdays": [0]}
        after = utc(2024, 3, 11, 4, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 18, 3, 0, 0)

    def test_fires_on_next_matching_weekday(self):
        # Monday (0) — fires next Wednesday (2)
        schedule = {"frequency": "daily", "time": "03:00", "weekdays": [2]}
        after = utc(2024, 3, 11, 4, 0, 0)  # Monday after 03:00
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 13, 3, 0, 0)  # Wednesday

    def test_fires_mon_to_thu_skips_weekend(self):
        # Friday — next Mon
        schedule = {"frequency": "daily", "time": "03:00", "weekdays": [0, 1, 2, 3]}
        after = utc(2024, 3, 15, 4, 0, 0)  # Friday
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 18, 3, 0, 0)  # Monday

    def test_empty_weekdays_falls_back_to_all_days(self):
        schedule = {"frequency": "daily", "time": "03:00", "weekdays": []}
        after = utc(2024, 3, 15, 4, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 16, 3, 0, 0)  # next day

    def test_result_is_strictly_after(self):
        # Exactly on time on a matching weekday → next week
        schedule = {"frequency": "daily", "time": "03:00", "weekdays": [0]}
        after = utc(2024, 3, 11, 3, 0, 0)  # Monday 03:00 exactly
        result = next_fire_time(schedule, after)
        assert result > after


# ---------------------------------------------------------------------------
# next_fire_time — weekly (single weekday)
# ---------------------------------------------------------------------------


class TestWeekly:
    def test_fires_today_when_weekday_matches_and_time_not_yet_reached(self):
        # 2024-03-11 is Monday (weekday 0)
        schedule = {"frequency": "weekly", "time": "03:00", "weekday": 0}
        after = utc(2024, 3, 11, 2, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 11, 3, 0, 0)

    def test_skips_today_when_weekday_matches_but_time_passed(self):
        # Monday, 03:00 already passed — next Monday
        schedule = {"frequency": "weekly", "time": "03:00", "weekday": 0}
        after = utc(2024, 3, 11, 4, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 18, 3, 0, 0)

    def test_fires_on_correct_day_when_today_is_different(self):
        # Today is Monday (0), scheduled for Wednesday (2)
        schedule = {"frequency": "weekly", "time": "03:00", "weekday": 2}
        after = utc(2024, 3, 11, 4, 0, 0)  # Monday after 03:00
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 13, 3, 0, 0)  # Wednesday

    def test_fires_exactly_one_day_per_week(self):
        # Friday (4) — even though multiple weekdays exist, only one fires
        schedule = {"frequency": "weekly", "time": "03:00", "weekday": 4}
        after = utc(2024, 3, 11, 4, 0, 0)  # Monday
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 15, 3, 0, 0)  # Friday

    def test_result_is_strictly_after(self):
        # Exactly on time on the matching weekday → next week
        schedule = {"frequency": "weekly", "time": "03:00", "weekday": 0}
        after = utc(2024, 3, 11, 3, 0, 0)  # Monday 03:00 exactly
        result = next_fire_time(schedule, after)
        assert result > after

    def test_result_lands_on_correct_weekday(self):
        # Sunday (6) — from a Wednesday
        schedule = {"frequency": "weekly", "time": "03:00", "weekday": 6}
        after = utc(2024, 3, 13, 4, 0, 0)  # Wednesday
        result = next_fire_time(schedule, after)
        assert result.weekday() == 6
        assert result == utc(2024, 3, 17, 3, 0, 0)  # Sunday


# ---------------------------------------------------------------------------
# next_fire_time — monthly (day_of_month)
# ---------------------------------------------------------------------------


class TestMonthly:
    def test_fires_this_month_when_day_not_yet_reached(self):
        schedule = {"frequency": "monthly", "time": "03:00", "day_of_month": 15}
        after = utc(2024, 3, 10, 4, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, 15, 3, 0, 0)

    def test_fires_next_month_when_day_passed(self):
        schedule = {"frequency": "monthly", "time": "03:00", "day_of_month": 5}
        after = utc(2024, 3, 10, 4, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 4, 5, 3, 0, 0)

    def test_fires_next_month_when_exactly_on_time(self):
        schedule = {"frequency": "monthly", "time": "03:00", "day_of_month": 10}
        after = utc(2024, 3, 10, 3, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 4, 10, 3, 0, 0)

    def test_clamps_day_to_28(self):
        # day 31 is clamped to 28 to avoid invalid dates
        schedule = {"frequency": "monthly", "time": "03:00", "day_of_month": 31}
        after = utc(2024, 3, 1, 0, 0, 0)
        result = next_fire_time(schedule, after)
        # clamped to 28, and 28 > 1 so fires this month
        assert result == utc(2024, 3, 28, 3, 0, 0)

    def test_crosses_year_boundary(self):
        schedule = {"frequency": "monthly", "time": "03:00", "day_of_month": 5}
        after = utc(2024, 12, 10, 4, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2025, 1, 5, 3, 0, 0)


# ---------------------------------------------------------------------------
# next_fire_time — monthly_weekday
# ---------------------------------------------------------------------------


class TestMonthlyWeekday:
    def _first_weekday_of_month(self, year, month, weekday):
        """Helper: date of the first `weekday` (0=Mon) in given month."""
        cal = calendar.monthcalendar(year, month)
        days = [week[weekday] for week in cal if week[weekday] != 0]
        return days[0]

    def _last_weekday_of_month(self, year, month, weekday):
        cal = calendar.monthcalendar(year, month)
        days = [week[weekday] for week in cal if week[weekday] != 0]
        return days[-1]

    def test_first_monday_of_month_fires_this_month(self):
        schedule = {
            "frequency": "monthly_weekday",
            "time": "03:00",
            "nth_weekday": 1,
            "weekday": 0,  # Monday
        }
        # Before the first Monday of March 2024
        first_monday = self._first_weekday_of_month(2024, 3, 0)
        after = utc(2024, 3, first_monday - 1, 4, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, first_monday, 3, 0, 0)

    def test_first_monday_fires_next_month_when_already_passed(self):
        schedule = {
            "frequency": "monthly_weekday",
            "time": "03:00",
            "nth_weekday": 1,
            "weekday": 0,
        }
        first_monday_mar = self._first_weekday_of_month(2024, 3, 0)
        first_monday_apr = self._first_weekday_of_month(2024, 4, 0)
        after = utc(2024, 3, first_monday_mar, 4, 0, 0)  # day of, but after time
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 4, first_monday_apr, 3, 0, 0)

    def test_last_friday_of_month(self):
        schedule = {
            "frequency": "monthly_weekday",
            "time": "03:00",
            "nth_weekday": -1,
            "weekday": 4,  # Friday
        }
        last_fri = self._last_weekday_of_month(2024, 3, 4)
        after = utc(2024, 3, 1, 0, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, last_fri, 3, 0, 0)

    def test_second_wednesday_of_month(self):
        schedule = {
            "frequency": "monthly_weekday",
            "time": "03:00",
            "nth_weekday": 2,
            "weekday": 2,  # Wednesday
        }
        cal = calendar.monthcalendar(2024, 3)
        wednesdays = [week[2] for week in cal if week[2] != 0]
        second_wed = wednesdays[1]
        after = utc(2024, 3, 1, 0, 0, 0)
        result = next_fire_time(schedule, after)
        assert result == utc(2024, 3, second_wed, 3, 0, 0)

    def test_nth_greater_than_occurrences_skips_to_next_valid_month(self):
        # 5th Monday — some months only have 4 Mondays; scheduler must skip forward
        schedule = {
            "frequency": "monthly_weekday",
            "time": "03:00",
            "nth_weekday": 5,
            "weekday": 0,  # Monday
        }

        # Find the first month starting from 2024-03 that has a 5th Monday
        def has_5th_weekday(year, month, wd):
            cal = calendar.monthcalendar(year, month)
            days = [week[wd] for week in cal if week[wd] != 0]
            return len(days) >= 5, days[4] if len(days) >= 5 else None

        after = utc(2024, 3, 1, 0, 0, 0)
        result = next_fire_time(schedule, after)

        # Verify the result actually lands on a 5th Monday
        has_5th, day = has_5th_weekday(result.year, result.month, 0)
        assert has_5th
        assert result.day == day

    def test_result_is_strictly_after(self):
        schedule = {
            "frequency": "monthly_weekday",
            "time": "03:00",
            "nth_weekday": 1,
            "weekday": 0,
        }
        after = utc(2024, 6, 1, 0, 0, 0)
        result = next_fire_time(schedule, after)
        assert result > after

    def test_crosses_year_boundary(self):
        schedule = {
            "frequency": "monthly_weekday",
            "time": "03:00",
            "nth_weekday": 1,
            "weekday": 0,  # first Monday
        }
        first_monday_dec = self._first_weekday_of_month(2024, 12, 0)
        # After the first Monday of December — should land in January 2025
        after = utc(2024, 12, first_monday_dec, 4, 0, 0)
        result = next_fire_time(schedule, after)
        first_monday_jan = self._first_weekday_of_month(2025, 1, 0)
        assert result == utc(2025, 1, first_monday_jan, 3, 0, 0)
