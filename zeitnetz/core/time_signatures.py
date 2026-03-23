"""Time signature definitions and sequence generation.

7 types, each mapping 12 grid positions to a proportionally scaled bar:
  Type 1: 3/8   unit = 32nd note
  Type 2: 4/8   unit = 16th-note triplet
  Type 3: 3/4   unit = 16th note
  Type 4: 4/4   unit = 8th-note triplet
  Type 5: 3/2   unit = 8th note
  Type 6: 4/2   unit = quarter-note triplet
  Type 7: 12/4  unit = quarter note
"""

from fractions import Fraction
from zeitnetz.constants import DEFAULT_TS_SEQ


# Each type: time signature string, unit quarterLength, tuplet config (or None)
TS_DEFS = {
    1: {"ts": "3/8",  "unit_ql": Fraction(1, 8),  "is_tuplet": False},
    2: {"ts": "4/8",  "unit_ql": Fraction(1, 6),  "is_tuplet": True,
        "tup_written": "16th",    "tup_actual": 3, "tup_normal": 2},
    3: {"ts": "3/4",  "unit_ql": Fraction(1, 4),  "is_tuplet": False},
    4: {"ts": "4/4",  "unit_ql": Fraction(1, 3),  "is_tuplet": True,
        "tup_written": "eighth",  "tup_actual": 3, "tup_normal": 2},
    5: {"ts": "3/2",  "unit_ql": Fraction(1, 2),  "is_tuplet": False},
    6: {"ts": "4/2",  "unit_ql": Fraction(2, 3),  "is_tuplet": True,
        "tup_written": "quarter", "tup_actual": 3, "tup_normal": 2},
    7: {"ts": "12/4", "unit_ql": Fraction(1, 1),  "is_tuplet": False},
}


def get_ts_for_bar(bar_index, ts_sequence):
    """Return the time signature type (1–7) for a given bar index (0-based)."""
    return ts_sequence[bar_index % len(ts_sequence)]


def generate_auto_ts_sequence(n_bars):
    """Generate a wedge/arch time signature sequence for a given piece length.

    The pattern follows the same logic as Mouvement's 105-bar sequence:
    Descent 7->1, Ascent 1->7, Descent 7->1, applied cyclically.

    The proportions scale to the piece length. Each full cycle has:
    - Descent: type 7 appears 1x, 6 2x, 5 3x, 4 4x, 3 5x, 2 6x, 1 14x (35 bars)
    - Ascent:  types 2-6 each 7x, type 7 14x (49 bars)
    - Descent: type 6 6x, 5 5x, 4 4x, 3 3x, 2 2x, 1 1x (21 bars)
    Total: 105 bars per cycle.

    For pieces significantly longer or shorter than 329 bars, the sequence
    scales proportionally while maintaining the wedge shape.
    """
    if n_bars <= 0:
        return []

    # Build one cycle of the wedge pattern
    cycle = []

    # Descent 7 -> 1 (increasing repetitions as types get smaller)
    for t in range(7, 0, -1):
        if t == 7:
            count = 1
        elif t == 1:
            count = 14
        else:
            count = 8 - t  # 7->1, 6->2, 5->3, 4->4, 3->5, 2->6
        cycle.extend([t] * count)

    # Ascent 2 -> 7 (7 bars each, 14 for type 7)
    for t in range(2, 8):
        count = 14 if t == 7 else 7
        cycle.extend([t] * count)

    # Descent 6 -> 1 (decreasing: 6x6, 5x5, 4x4, 3x3, 2x2, 1x1)
    for t in range(6, 0, -1):
        cycle.extend([t] * t)

    return cycle


def parse_ts_sequence(s):
    """Parse a space-separated string of type numbers (1-7).
    Returns a list of ints. Raises ValueError on bad input."""
    tokens = s.strip().split()
    if not tokens:
        raise ValueError("Time signature sequence cannot be empty")
    result = []
    for t in tokens:
        v = int(t)
        if not 1 <= v <= 7:
            raise ValueError(f"TS type {v} out of range 1–7")
        result.append(v)
    return result
