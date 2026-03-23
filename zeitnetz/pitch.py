"""Pitch class utilities — conversion tables, parsing, naming."""

GERMAN_TO_PC = {
    "c": 0, "cis": 1, "d": 2, "dis": 3, "e": 4, "f": 5,
    "fis": 6, "g": 7, "gis": 8, "a": 9, "ais": 10, "b": 10,
    "h": 11, "his": 0, "ces": 11, "des": 1, "es": 3, "ges": 6, "as": 8,
}

PC_TO_GERMAN = {
    0: "c", 1: "cis", 2: "d", 3: "dis", 4: "e", 5: "f",
    6: "fis", 7: "g", 8: "gis", 9: "a", 10: "ais", 11: "h",
}

PC_TO_MUSIC21 = {
    0: "C4", 1: "C#4", 2: "D4", 3: "D#4", 4: "E4", 5: "F4",
    6: "F#4", 7: "G4", 8: "G#4", 9: "A4", 10: "A#4", 11: "B4",
}

PC_TO_MIDICENT = {pc: (60 + pc) * 100 for pc in range(12)}


def pc_name(pc):
    """Return the German pitch name for a pitch class (0–11)."""
    return PC_TO_GERMAN[pc % 12]


def parse_pitch_input(s):
    """Parse a string of 12 pitch classes (integers 0–11 or German names).
    Returns a list of 12 integers. Raises ValueError on bad input."""
    tokens = s.strip().split()
    if len(tokens) != 12:
        raise ValueError(f"Pitch row must have 12 values, got {len(tokens)}")
    result = []
    for t in tokens:
        try:
            v = int(t)
            if not 0 <= v <= 11:
                raise ValueError(f"PC {v} out of range 0–11")
            result.append(v)
        except ValueError:
            tl = t.lower()
            if tl in GERMAN_TO_PC:
                result.append(GERMAN_TO_PC[tl])
            else:
                raise ValueError(f"Unknown pitch name: '{t}'")
    if set(result) != set(range(12)):
        raise ValueError("Pitch row must contain each class 0–11 exactly once")
    return result


def parse_int_list(s, expected, name):
    """Parse a space-separated string of integers."""
    tokens = s.strip().split()
    if len(tokens) != expected:
        raise ValueError(f"{name} must have {expected} values, got {len(tokens)}")
    return [int(t) for t in tokens]


def r_limit(value, lo, hi):
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


def r_limit_midicent(mc, lo=None, hi=None, tol=None):
    """Constrain a midicent value to [lo, hi] with tolerance band."""
    from zeitnetz.constants import MC_LOW, MC_HIGH, MC_TOLERANCE
    lo = lo if lo is not None else MC_LOW
    hi = hi if hi is not None else MC_HIGH
    tol = tol if tol is not None else MC_TOLERANCE
    if mc < lo - tol:
        return lo
    if mc > hi + tol:
        return hi
    return mc
