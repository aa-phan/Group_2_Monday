"""
Item identity helpers for the household inventory (Track B).

An item's identity within a household+location is derived from its display
name via normalization: strip leading/trailing whitespace, lowercase, and
collapse every internal whitespace run to a single space. The result is the
`itemKey` used to merge repeat restocks of the "same" item together.

Per CONTEXT.md D-03 this module owns only the normalization half of item
identity. The substring/prefix matching half (e.g. "Milk" matching
"Whole Milk") is added by plan 02-03, which extends this same module.
"""

import re

_WHITESPACE_RUN = re.compile(r"\s+")


def normalizeItemName(rawName):
    """Normalize a raw item name into its itemKey.

    Strips leading/trailing whitespace, lowercases, and collapses every
    internal whitespace run to a single space.

    Raises:
        ValueError: if rawName is not a string, or normalizes to the empty
            string.
    """
    if not isinstance(rawName, str):
        raise ValueError("itemName must be a string")

    normalized = _WHITESPACE_RUN.sub(" ", rawName.strip()).lower()

    if normalized == "":
        raise ValueError("itemName must not be blank")

    return normalized
