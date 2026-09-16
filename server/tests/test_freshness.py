"""
Boundary tests for server/freshness.py (INV-05 / D-09, D-10, D-11), written
before the implementation exists (RED commit precedes GREEN commit).

Every date in this suite is built relative to a fixed TODAY, never
date.today() -- so the suite cannot start failing on a calendar boundary.
TODAY is pinned to 2026-06-15 and every case below is a literal ISO date
computed by hand against that anchor (see the comment on each case).

Freezer "months elapsed" is whole calendar months between purchaseDate and
TODAY: the month difference, decremented by one if TODAY's day-of-month has
not yet reached purchaseDate's day-of-month. That is the same definition
server/freshness.py implements, so the two agree at every boundary tested
here (exactly 6 months, exactly 12 months, one day short of 6 months).
"""

from datetime import date

import pytest

import freshness

TODAY = date(2026, 6, 15)


# ---------------------------------------------------------------------------
# Pantry (D-09) -- no early warning window at all
# ---------------------------------------------------------------------------


def test_pantry_best_by_five_days_away_is_fresh():
    assert freshness.computeBatchFreshness("Pantry", None, "2026-06-20", TODAY) == freshness.FRESH


def test_pantry_best_by_tomorrow_is_fresh():
    assert freshness.computeBatchFreshness("Pantry", None, "2026-06-16", TODAY) == freshness.FRESH


def test_pantry_best_by_today_is_fresh():
    assert freshness.computeBatchFreshness("Pantry", None, "2026-06-15", TODAY) == freshness.FRESH


def test_pantry_best_by_yesterday_is_expired():
    assert freshness.computeBatchFreshness("Pantry", None, "2026-06-14", TODAY) == freshness.EXPIRED


def test_pantry_best_by_absent_is_unknown():
    assert freshness.computeBatchFreshness("Pantry", None, None, TODAY) == freshness.UNKNOWN


# ---------------------------------------------------------------------------
# Fridge (D-10) -- warning window of FRIDGE_EXPIRING_SOON_DAYS
# ---------------------------------------------------------------------------


def test_fridge_best_by_four_days_away_is_fresh():
    assert freshness.computeBatchFreshness("Fridge", None, "2026-06-19", TODAY) == freshness.FRESH


def test_fridge_best_by_exactly_three_days_away_is_expiring_soon():
    assert freshness.computeBatchFreshness("Fridge", None, "2026-06-18", TODAY) == freshness.EXPIRING_SOON


def test_fridge_best_by_tomorrow_is_expiring_soon():
    assert freshness.computeBatchFreshness("Fridge", None, "2026-06-16", TODAY) == freshness.EXPIRING_SOON


def test_fridge_best_by_today_is_expiring_soon():
    assert freshness.computeBatchFreshness("Fridge", None, "2026-06-15", TODAY) == freshness.EXPIRING_SOON


def test_fridge_best_by_yesterday_is_expired():
    assert freshness.computeBatchFreshness("Fridge", None, "2026-06-14", TODAY) == freshness.EXPIRED


def test_fridge_best_by_absent_is_unknown():
    assert freshness.computeBatchFreshness("Fridge", None, None, TODAY) == freshness.UNKNOWN


# ---------------------------------------------------------------------------
# Freezer (D-11) -- computed from purchase/freeze date, best-by ignored
# ---------------------------------------------------------------------------


def test_freezer_frozen_thirty_days_ago_is_fresh():
    # TODAY (2026-06-15) minus 30 days = 2026-05-16 -> 0 whole months elapsed.
    assert freshness.computeBatchFreshness("Freezer", "2026-05-16", None, TODAY) == freshness.FRESH


def test_freezer_frozen_just_under_six_months_ago_is_fresh():
    # One day short of exactly 6 months -> 5 whole months elapsed.
    assert freshness.computeBatchFreshness("Freezer", "2025-12-16", None, TODAY) == freshness.FRESH


def test_freezer_frozen_exactly_six_months_ago_is_expiring_soon():
    assert freshness.computeBatchFreshness("Freezer", "2025-12-15", None, TODAY) == freshness.EXPIRING_SOON


def test_freezer_frozen_nine_months_ago_is_expiring_soon():
    assert freshness.computeBatchFreshness("Freezer", "2025-09-15", None, TODAY) == freshness.EXPIRING_SOON


def test_freezer_frozen_exactly_twelve_months_ago_is_expiring_soon():
    assert freshness.computeBatchFreshness("Freezer", "2025-06-15", None, TODAY) == freshness.EXPIRING_SOON


def test_freezer_frozen_thirteen_months_ago_is_expired():
    assert freshness.computeBatchFreshness("Freezer", "2025-05-15", None, TODAY) == freshness.EXPIRED


def test_freezer_purchase_date_absent_is_unknown():
    assert freshness.computeBatchFreshness("Freezer", None, "2026-12-01", TODAY) == freshness.UNKNOWN


def test_freezer_best_by_supplied_alongside_purchase_date_changes_nothing():
    # Exactly 6 months elapsed -> expiring_soon regardless of what bestByDate says.
    farFutureBestBy = freshness.computeBatchFreshness("Freezer", "2025-12-15", "2099-01-01", TODAY)
    farPastBestBy = freshness.computeBatchFreshness("Freezer", "2025-12-15", "2020-01-01", TODAY)
    assert farFutureBestBy == freshness.EXPIRING_SOON
    assert farPastBestBy == freshness.EXPIRING_SOON


# ---------------------------------------------------------------------------
# Item-level roll-up (computeItemFreshness)
# ---------------------------------------------------------------------------


def test_item_with_no_batches_is_unknown():
    assert freshness.computeItemFreshness("Pantry", [], TODAY) == freshness.UNKNOWN


def test_item_with_one_fresh_and_one_expired_batch_is_expired():
    batches = [
        {"purchaseDate": "2026-06-01", "bestByDate": "2026-06-20"},  # fresh
        {"purchaseDate": "2026-06-01", "bestByDate": "2026-06-14"},  # expired
    ]
    assert freshness.computeItemFreshness("Pantry", batches, TODAY) == freshness.EXPIRED


def test_item_with_one_fresh_and_one_expiring_soon_batch_is_expiring_soon():
    batches = [
        {"purchaseDate": "2026-06-01", "bestByDate": "2026-06-19"},  # fresh (4 days away)
        {"purchaseDate": "2026-06-01", "bestByDate": "2026-06-18"},  # expiring_soon (3 days away)
    ]
    assert freshness.computeItemFreshness("Fridge", batches, TODAY) == freshness.EXPIRING_SOON


def test_item_with_one_unknown_and_one_fresh_batch_is_fresh():
    batches = [
        {"purchaseDate": "2026-06-01", "bestByDate": None},  # unknown
        {"purchaseDate": "2026-06-01", "bestByDate": "2026-06-20"},  # fresh
    ]
    assert freshness.computeItemFreshness("Pantry", batches, TODAY) == freshness.FRESH


def test_item_roll_up_does_not_depend_on_batch_order():
    batches = [
        {"purchaseDate": "2026-06-01", "bestByDate": "2026-06-20"},  # fresh
        {"purchaseDate": "2026-06-01", "bestByDate": "2026-06-14"},  # expired
    ]
    forward = freshness.computeItemFreshness("Pantry", batches, TODAY)
    reversed_result = freshness.computeItemFreshness("Pantry", list(reversed(batches)), TODAY)
    assert forward == reversed_result == freshness.EXPIRED


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------


def test_unknown_location_raises_value_error():
    with pytest.raises(ValueError):
        freshness.computeBatchFreshness("Garage", None, "2026-06-20", TODAY)


def test_malformed_date_string_raises_value_error_rather_than_returning_fresh():
    with pytest.raises(ValueError):
        freshness.computeBatchFreshness("Pantry", None, "not-a-date", TODAY)
