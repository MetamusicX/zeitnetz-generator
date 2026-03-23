"""Stage 5 — Zeitnetz Final (duration-as-count transformation).

Transforms family entries so that duration values become event-skip counts.
Uses greedy staff assignment to minimise staves.
"""

from dataclasses import dataclass
from zeitnetz.constants import BAR, MAX_CYCLES
from zeitnetz.core.zeitnetz_grid import build_row_templates, build_grid
from zeitnetz.core.family_scan import duration_as_count_transform
from zeitnetz.core.staff_assignment import greedy_assign


@dataclass
class Stage5Result:
    zn_events: list         # extended Zeitnetz events (may be longer than Stage 4)
    row_start_pos: dict
    total_32: int
    n_bars: int
    n_cycles: int
    final_entries: dict     # family_number -> list of FamilyEntry (new positions)
    staff_assign: dict      # family_number -> staff_number
    n_staves: int
    max_grid_pos: int       # maximum grid position of any family entry


def run(voices, families, s4_result):
    """Execute Stage 5 computation.

    Parameters
    ----------
    voices : list of VoiceData (from Stage 2)
    families : list of FamilyDef (from Stage 3)
    s4_result : Stage4Result

    Returns Stage5Result.
    """
    templates = build_row_templates(voices)

    # Compute how many events we need
    _, max_idx = duration_as_count_transform(s4_result.fam_entries, s4_result.zn_events)

    # Build grid with enough events
    min_events_needed = max_idx + 1
    zn_events, row_start_pos, total_32, n_cycles = build_grid(
        templates, min_events=min_events_needed, max_cycles=MAX_CYCLES
    )

    # If still not enough events, keep extending
    while max_idx >= len(zn_events):
        zn_events, row_start_pos, total_32, n_cycles = build_grid(
            templates, min_events=max_idx + 100, max_cycles=MAX_CYCLES + 10
        )

    # Run the actual transformation with the extended grid
    final_entries, max_idx = duration_as_count_transform(
        s4_result.fam_entries, zn_events
    )

    # Find maximum grid position
    max_pos = 0
    for fn, entries in final_entries.items():
        if entries:
            max_pos = max(max_pos, entries[-1].pos)

    # Greedy staff assignment
    spans = []
    for fn, entries in final_entries.items():
        if entries:
            spans.append((fn, entries[0].pos, entries[-1].pos))
    assign, n_staves = greedy_assign(spans)

    # Determine score length from max family position
    score_total = max_pos + BAR
    n_bars = (score_total + BAR - 1) // BAR

    return Stage5Result(
        zn_events=zn_events,
        row_start_pos=row_start_pos,
        total_32=total_32,
        n_bars=n_bars,
        n_cycles=n_cycles,
        final_entries=final_entries,
        staff_assign=assign,
        n_staves=n_staves,
        max_grid_pos=max_pos,
    )
