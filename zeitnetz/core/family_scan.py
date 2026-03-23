"""Family activation scanning — shared by Stage 4 and Final.

Implements the sequential scan that activates and deactivates families
over the Zeitnetz event stream, plus the duration-as-count transformation.
"""

from dataclasses import dataclass


@dataclass
class FamilyEntry:
    """A single entry of a family in the Zeitnetz."""
    zn_index: int    # index in the Zeitnetz event list
    pos: int         # grid position in 32nd-note units
    pc: int          # pitch class
    dur: int         # duration from the Zeitnetz event


def sequential_scan(zn_events, families):
    """Run the sequential activation scan over the Zeitnetz events.

    Families activate in queue order (1, 2, 3, ..., N).
    A family activates when its start_pc matches the current event.
    Every active family receives every event.
    A family deactivates (inclusive) when its end_pc matches,
    EXCEPT same-pitch families (start_pc == end_pc) which require >= 2 events.

    Parameters
    ----------
    zn_events : list of ZnEvent
    families : list of FamilyDef

    Returns
    -------
    fam_entries : dict mapping family_number -> list of FamilyEntry
    all_activated : bool (True if all families activated and deactivated)
    remaining_queue : list of FamilyDef (families that never activated)
    """
    family_queue = list(families)
    active = []
    fam_entries = {f.family: [] for f in families}
    fam_evt_count = {}

    for ev in zn_events:
        # Activate next queued family if start_pc matches
        if family_queue and family_queue[0].start_pc == ev.pc:
            f = family_queue.pop(0)
            active.append(f)
            fam_evt_count[f.family] = 0

        # Every active family receives this event
        for f in active:
            fam_entries[f.family].append(FamilyEntry(
                zn_index=ev.index, pos=ev.pos, pc=ev.pc, dur=ev.dur
            ))
            fam_evt_count[f.family] += 1

        # Deactivate families whose end_pc matches
        new_active = []
        for f in active:
            if f.end_pc == ev.pc:
                if f.start_pc == f.end_pc:
                    # Same start/end: need at least 2 events
                    if fam_evt_count[f.family] >= 2:
                        continue  # deactivate
                    else:
                        new_active.append(f)
                else:
                    continue  # deactivate (normal case)
            else:
                new_active.append(f)
        active = new_active

        # Stop early if all families done
        if not family_queue and not active:
            break

    all_done = (not family_queue) and (not active)
    return fam_entries, all_done, family_queue


def test_all_families_done(zn_events, families):
    """Quick test: can all families activate and deactivate?
    Lightweight version without storing entries."""
    family_queue = list(families)
    active = []
    fam_evt_count = {}

    for ev in zn_events:
        if family_queue and family_queue[0].start_pc == ev.pc:
            f = family_queue.pop(0)
            active.append(f)
            fam_evt_count[f.family] = 0

        for f in active:
            fam_evt_count[f.family] += 1

        new_active = []
        for f in active:
            if f.end_pc == ev.pc:
                if f.start_pc == f.end_pc:
                    if fam_evt_count[f.family] >= 2:
                        continue
                    else:
                        new_active.append(f)
                else:
                    continue
            else:
                new_active.append(f)
        active = new_active

        if not family_queue and not active:
            return True

    return False


def duration_as_count_transform(fam_entries, zn_events):
    """Transform family entries: durations become event-skip counts.

    For each family, the first entry stays at its original position.
    Subsequent entries advance by the previous entry's duration value,
    counting forward through the Zeitnetz event list.

    The pitch at each new position is taken from the Zeitnetz event.

    Parameters
    ----------
    fam_entries : dict mapping family_number -> list of FamilyEntry
    zn_events : list of ZnEvent

    Returns
    -------
    final_entries : dict mapping family_number -> list of FamilyEntry
    max_index : int (maximum Zeitnetz event index used)
    """
    final_entries = {}
    max_index = 0

    for fn, entries in fam_entries.items():
        if not entries:
            final_entries[fn] = []
            continue

        start_idx = entries[0].zn_index
        durations = [e.dur for e in entries]

        new_entries = []
        idx = start_idx
        for i in range(len(entries)):
            if idx >= len(zn_events):
                break
            ev = zn_events[idx]
            new_entries.append(FamilyEntry(
                zn_index=idx, pos=ev.pos, pc=ev.pc, dur=ev.dur
            ))
            max_index = max(max_index, idx)
            # Advance by this entry's duration for the next entry
            if i < len(entries) - 1:
                idx += durations[i]
                max_index = max(max_index, idx)

        final_entries[fn] = new_entries

    return final_entries, max_index
