import random

import pytest

from itemIdentity import AmbiguousItemMatch, findMatchingItemKey, normalizeItemName


# ---------------------------------------------------------------------------
# normalizeItemName (plan 02-01) -- re-asserted here so this file is a
# complete regression suite for itemIdentity.py, not just the new function.
# ---------------------------------------------------------------------------


def test_normalize_strips_and_lowercases():
    assert normalizeItemName("  Milk  ") == "milk"


def test_normalize_collapses_internal_whitespace():
    assert normalizeItemName("Whole   Milk") == "whole milk"


def test_normalize_rejects_blank():
    with pytest.raises(ValueError):
        normalizeItemName("   ")


# ---------------------------------------------------------------------------
# findMatchingItemKey -- exact match
# ---------------------------------------------------------------------------


def test_exact_match_wins_outright():
    assert findMatchingItemKey("milk", ["milk", "whole milk"]) == "milk"


# ---------------------------------------------------------------------------
# findMatchingItemKey -- loose match, single candidate
# ---------------------------------------------------------------------------


def test_loose_match_key_is_substring_of_name():
    assert findMatchingItemKey("whole milk", ["milk"]) == "milk"


def test_loose_match_name_is_substring_of_key():
    assert findMatchingItemKey("milk", ["whole milk"]) == "whole milk"


def test_loose_match_prefix_case_falls_out_of_substring():
    assert findMatchingItemKey("oat", ["oats"]) == "oats"


# ---------------------------------------------------------------------------
# findMatchingItemKey -- ambiguity raises rather than guesses
# ---------------------------------------------------------------------------


def test_ambiguous_match_raises_with_both_candidates():
    with pytest.raises(AmbiguousItemMatch) as excinfo:
        findMatchingItemKey("milk", ["whole milk", "skim milk"])
    assert set(excinfo.value.candidates) == {"whole milk", "skim milk"}


def test_ambiguous_match_raises_when_key_is_substring_both_ways():
    with pytest.raises(AmbiguousItemMatch) as excinfo:
        findMatchingItemKey("milk", ["milk powder", "milk chocolate"])
    assert set(excinfo.value.candidates) == {"milk powder", "milk chocolate"}


def test_ambiguous_match_candidates_are_sorted():
    with pytest.raises(AmbiguousItemMatch) as excinfo:
        findMatchingItemKey("milk", ["skim milk", "whole milk"])
    assert excinfo.value.candidates == sorted(excinfo.value.candidates)


# ---------------------------------------------------------------------------
# findMatchingItemKey -- no match
# ---------------------------------------------------------------------------


def test_no_match_returns_none():
    assert findMatchingItemKey("rice", ["milk", "oats"]) is None


def test_no_match_against_empty_keys_returns_none():
    assert findMatchingItemKey("rice", []) is None


# ---------------------------------------------------------------------------
# Out of scope by decision D-03 -- must NOT match
# ---------------------------------------------------------------------------


def test_edit_distance_does_not_match():
    # "mlk" is not a substring of "milk" and "milk" is not a substring of
    # "mlk" -- no fuzzy/edit-distance matching per D-03.
    assert findMatchingItemKey("mlk", ["milk"]) is None


def test_milks_does_match_because_milk_is_a_substring_of_milks():
    # Not an edit-distance case -- "milk" IS a plain substring of "milks".
    assert findMatchingItemKey("milks", ["milk"]) == "milk"


def test_synonyms_do_not_match():
    assert findMatchingItemKey("dairy", ["milk"]) is None


def test_exact_match_relies_on_caller_normalization():
    # findMatchingItemKey itself does no casing/whitespace normalization --
    # the caller normalizes first (per the module's separation of concerns).
    # Passing an already-normalized name is exact.
    assert findMatchingItemKey("milk", ["milk"]) == "milk"


# ---------------------------------------------------------------------------
# Determinism -- order independence
# ---------------------------------------------------------------------------


def test_result_does_not_depend_on_existing_keys_order():
    keys = ["milk", "oats", "rice", "whole milk"]
    baseline = findMatchingItemKey("whole milk", keys)

    shuffled = list(keys)
    random.Random(42).shuffle(shuffled)
    assert findMatchingItemKey("whole milk", shuffled) == baseline


def test_ambiguity_candidates_do_not_depend_on_existing_keys_order():
    keys = ["whole milk", "skim milk"]

    with pytest.raises(AmbiguousItemMatch) as first:
        findMatchingItemKey("milk", keys)

    shuffled = list(keys)
    random.Random(7).shuffle(shuffled)
    with pytest.raises(AmbiguousItemMatch) as second:
        findMatchingItemKey("milk", shuffled)

    assert first.value.candidates == second.value.candidates
