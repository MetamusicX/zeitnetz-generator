"""Fixed constants for the Zeitnetz system."""

# Row reading order for family numbering (Stage 3.1 start pitches)
FAMILY_ROW_ORDER = [7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5, 6]

# Reverse circular order for end pitches (Stage 3.2)
END_PITCH_ROW_ORDER = [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]

# Control row index for Stage 3 target extraction
CONTROL_ROW_INDEX = 10

# Grid positions per bar (always 12)
BAR = 12

# Safety cap for cyclic Zeitnetz extension
MAX_CYCLES = 20

# Midicent limits from 'Loop-Familie-anfang-end-note' patch
MC_LOW = 6800
MC_HIGH = 7100
MC_TOLERANCE = 200

# Duration thresholds from 'Loop-Dauer' patch
DUR_SHORT = 25
DUR_MEDIUM = 425
DUR_LONG = 725

# Default 105-bar time signature sequence (Mouvement wedge pattern)
DEFAULT_TS_SEQ = [
    7, 6, 6, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4,
    5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    6, 6, 6, 6, 6, 6, 5, 5, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 2, 2, 1,
]
