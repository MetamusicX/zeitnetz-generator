"""Zeitnetz grid construction — shared by Stage 4, V2, and Final.

Builds the extended (cyclic) Zeitnetz from Stage 2 voice data.
The grid is a flat sequence of events, each at a specific position
in 32nd-note units, with pitch and duration.
"""

from dataclasses import dataclass
from zeitnetz.constants import MAX_CYCLES


@dataclass
class ZnEvent:
    pos: int        # position in 32nd-note units
    pc: int         # pitch class 0–11
    dur: int        # duration in 32nd-note units
    label: str      # row label (e.g., "Row 0", "Row 0b")
    index: int      # sequential index in the event list


def build_row_templates(voices):
    """Extract row templates from Stage 2 voice data.
    Returns [(voice_index, initial_rest, [(pc, dur), ...])]."""
    return [
        (v.voice_index, v.initial_rest_32nds, list(v.notes))
        for v in voices
    ]


def build_grid(row_templates, min_events=0, max_cycles=None):
    """Build the Zeitnetz event grid with cyclic extensions.

    Parameters
    ----------
    row_templates : list of (voice_index, initial_rest, notes)
    min_events : int
        Minimum number of events required. Extensions continue until met.
    max_cycles : int or None
        Safety cap on extra cycles. Defaults to MAX_CYCLES.

    Returns
    -------
    events : list of ZnEvent
    row_start_pos : dict mapping row_label -> position
    total_32 : int (total grid positions)
    n_cycles : int (number of extra cycles added)
    """
    if max_cycles is None:
        max_cycles = MAX_CYCLES

    events = []
    row_start_pos = {}
    pos = 0
    idx = 0

    # Original 12 rows (with initial rests)
    for vi, ir, notes in row_templates:
        if ir > 0:
            pos += ir
        label = f"Row {vi}"
        row_start_pos[label] = pos
        for pc, dur_32 in notes:
            events.append(ZnEvent(pos=pos, pc=pc, dur=dur_32, label=label, index=idx))
            pos += dur_32
            idx += 1

    # Cyclic extensions
    cycle = 0
    while cycle < max_cycles and len(events) < min_events:
        cycle += 1
        suffix = chr(ord('a') + cycle - 1)  # b, c, d, ...
        for vi, _ir, notes in row_templates:
            label = f"Row {vi}{suffix}"
            row_start_pos[label] = pos
            for pc, dur_32 in notes:
                events.append(ZnEvent(pos=pos, pc=pc, dur=dur_32, label=label, index=idx))
                pos += dur_32
                idx += 1

    return events, row_start_pos, pos, cycle


def build_grid_until_families_done(row_templates, families, max_cycles=None):
    """Build the grid with enough extensions for all families to complete.

    Uses the sequential scan test to determine when to stop extending.

    Returns same as build_grid, plus a bool indicating if all families finished.
    """
    from zeitnetz.core.family_scan import test_all_families_done

    if max_cycles is None:
        max_cycles = MAX_CYCLES

    events = []
    row_start_pos = {}
    pos = 0
    idx = 0

    # Original 12 rows
    for vi, ir, notes in row_templates:
        if ir > 0:
            pos += ir
        label = f"Row {vi}"
        row_start_pos[label] = pos
        for pc, dur_32 in notes:
            events.append(ZnEvent(pos=pos, pc=pc, dur=dur_32, label=label, index=idx))
            pos += dur_32
            idx += 1

    # Check if already done
    if test_all_families_done(events, families):
        return events, row_start_pos, pos, 0, True

    # Extend cyclically until done
    for cycle in range(1, max_cycles + 1):
        suffix = chr(ord('a') + cycle - 1)
        for vi, _ir, notes in row_templates:
            label = f"Row {vi}{suffix}"
            row_start_pos[label] = pos
            for pc, dur_32 in notes:
                events.append(ZnEvent(pos=pos, pc=pc, dur=dur_32, label=label, index=idx))
                pos += dur_32
                idx += 1

        if test_all_families_done(events, families):
            return events, row_start_pos, pos, cycle, True

    return events, row_start_pos, pos, max_cycles, False
