"""Stage 4 — Full Score computation.

Builds the extended Zeitnetz grid, runs the sequential family scan,
and assigns families to staves (round-robin).
No MusicXML generation — pure data computation.
"""

from dataclasses import dataclass
from zeitnetz.constants import BAR
from zeitnetz.core.zeitnetz_grid import build_row_templates, build_grid_until_families_done
from zeitnetz.core.family_scan import sequential_scan
from zeitnetz.core.staff_assignment import round_robin


@dataclass
class Stage4Result:
    zn_events: list         # list of ZnEvent
    row_start_pos: dict     # row_label -> pos
    total_32: int           # total grid positions
    n_bars: int
    n_cycles: int           # extra cycles added
    fam_entries: dict       # family_number -> list of FamilyEntry
    n_families: int         # total families
    n_activated: int        # families that activated
    all_done: bool
    staff_assign: dict      # family_number -> staff_number
    n_staves: int
    remaining_queue: list   # families that never activated


def run(voices, families):
    """Execute Stage 4 computation.

    Parameters
    ----------
    voices : list of VoiceData (from Stage 2)
    families : list of FamilyDef (from Stage 3)

    Returns Stage4Result.
    """
    templates = build_row_templates(voices)

    # Build extended grid
    zn_events, row_start_pos, total_32, n_cycles, all_done = \
        build_grid_until_families_done(templates, families)

    # Sequential scan
    fam_entries, scan_done, remaining = sequential_scan(zn_events, families)

    # Count activated families
    activated_fams = [f for f in families if len(fam_entries[f.family]) > 0]
    n_activated = len(activated_fams)

    # Round-robin staff assignment
    n_families = len(families)
    n_staves = min(12, n_families)
    assign = round_robin(n_families, n_staves)

    n_bars = (total_32 + BAR - 1) // BAR

    return Stage4Result(
        zn_events=zn_events,
        row_start_pos=row_start_pos,
        total_32=total_32,
        n_bars=n_bars,
        n_cycles=n_cycles,
        fam_entries=fam_entries,
        n_families=n_families,
        n_activated=n_activated,
        all_done=all_done and scan_done,
        staff_assign=assign,
        n_staves=n_staves,
        remaining_queue=remaining,
    )
