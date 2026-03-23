"""Stage 3 — Klangfamilien (Sound Families).

3.1: Derive starting pitches by scanning each rhythm row until finding
     the control-row target. The number of families is DYNAMIC — it depends
     on where the targets land in each row.

3.2: Derive end pitches by reading rows in reverse circular order,
     each row reversed, producing a 1-to-1 pairing with start pitches.

OM patch: "3 – Klangfamilien"
"""

from dataclasses import dataclass
from zeitnetz.constants import (
    CONTROL_ROW_INDEX,
    FAMILY_ROW_ORDER,
    END_PITCH_ROW_ORDER,
)


@dataclass
class RowFamilies:
    row_index: int
    target_pc: int
    pitches: list  # pitch classes read (including target)
    rhythm_row: list


@dataclass
class FamilyDef:
    family: int     # 1-based family number
    start_pc: int
    end_pc: int
    row: int        # row index where start pitch lives


def run_stage3_1(s1):
    """Stage 3.1 — determine starting pitches of all sound families.

    For each rhythm row i, scan pitch by pitch until the i-th element
    of pitch permutation [CONTROL_ROW_INDEX] (control row) is found.
    The number of families varies with the input.

    Returns a list of 12 RowFamilies objects."""
    control_row = s1.pitch_perms[CONTROL_ROW_INDEX]
    result = []
    for i in range(12):
        rr = s1.rhythm_perms[i]
        target = control_row[i]
        pitches = []
        for pc in rr:
            pitches.append(pc)
            if pc == target:
                break
        result.append(RowFamilies(
            row_index=i,
            target_pc=target,
            pitches=pitches,
            rhythm_row=rr,
        ))
    return result


def run_stage3_2(s3_1):
    """Stage 3.2 — determine end pitches and build family definitions.

    The number of families is derived from the data (NOT hardcoded).

    Returns a list of FamilyDef objects."""
    by_row = {rf.row_index: rf for rf in s3_1}

    # Build start-pitch list in family order
    start_pitches = []
    for ri in FAMILY_ROW_ORDER:
        for pc in by_row[ri].pitches:
            start_pitches.append((ri, pc))

    # Build end-pitch tape (reverse circular order, each row reversed)
    end_tape = []
    for ri in END_PITCH_ROW_ORDER:
        for pc in reversed(by_row[ri].pitches):
            end_tape.append(pc)

    n_families = len(start_pitches)

    # Pair start and end pitches
    families = []
    for i in range(n_families):
        row_idx, spc = start_pitches[i]
        families.append(FamilyDef(
            family=i + 1,
            start_pc=spc,
            end_pc=end_tape[i],
            row=row_idx,
        ))
    return families


def run(s1):
    """Execute full Stage 3 (3.1 + 3.2). Returns (stage3_1_result, families)."""
    s3_1 = run_stage3_1(s1)
    families = run_stage3_2(s3_1)
    return s3_1, families
