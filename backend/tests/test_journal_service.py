"""
Unit tests for app/services/journal_service.py.
_compute_streaks is a pure function — no mocking needed.
"""
from datetime import date, timedelta

from app.services.journal_service import _compute_streaks

today = date.today()
yesterday = today - timedelta(days=1)


# ── Edge cases ─────────────────────────────────────────────────────────────────

def test_no_sessions_returns_zero_zero():
    assert _compute_streaks([]) == (0, 0)


def test_single_session_today():
    current, longest = _compute_streaks([today])
    assert current == 1
    assert longest == 1


def test_single_session_yesterday_counts_as_current():
    # A gap of 1 day still counts as an active streak
    current, longest = _compute_streaks([yesterday])
    assert current == 1
    assert longest == 1


def test_session_two_days_ago_breaks_current_streak():
    dates = [today - timedelta(days=2)]
    current, longest = _compute_streaks(dates)
    assert current == 0


# ── Current streak ─────────────────────────────────────────────────────────────

def test_consecutive_days_builds_current_streak():
    dates = [today - timedelta(days=2), yesterday, today]
    current, longest = _compute_streaks(dates)
    assert current == 3


def test_streak_resets_after_gap():
    # 2-day streak last week, only today active now
    dates = [
        today - timedelta(days=8),
        today - timedelta(days=7),
        today,
    ]
    current, longest = _compute_streaks(dates)
    assert current == 1
    assert longest == 2


# ── Longest streak ─────────────────────────────────────────────────────────────

def test_longest_streak_found_in_past():
    # 5-day streak in the past, single session today
    past_streak = [today - timedelta(days=20 + i) for i in range(5)]
    dates = past_streak + [today]
    current, longest = _compute_streaks(dates)
    assert longest == 5
    assert current == 1


def test_longest_streak_equals_current_when_ongoing():
    dates = [today - timedelta(days=i) for i in range(4)]  # 4-day streak ending today
    current, longest = _compute_streaks(dates)
    assert current == 4
    assert longest == 4


# ── Deduplication ──────────────────────────────────────────────────────────────

def test_duplicate_dates_counted_once():
    dates = [today, today, yesterday, yesterday]
    current, longest = _compute_streaks(dates)
    assert current == 2
    assert longest == 2


# ── Longer sequences ───────────────────────────────────────────────────────────

def test_multiple_gaps_picks_correct_longest():
    # Gap 1: 3 consecutive days (far past)
    # Gap 2: 2 consecutive days (mid past)
    # No current streak
    group_a = [today - timedelta(days=30 + i) for i in range(3)]
    group_b = [today - timedelta(days=10 + i) for i in range(2)]
    current, longest = _compute_streaks(group_a + group_b)
    assert longest == 3
    assert current == 0
