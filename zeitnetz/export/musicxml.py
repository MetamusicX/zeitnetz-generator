"""MusicXML generation using music21.

All export functions receive plain Python data structures and produce
MusicXML files. No compositional computation happens here.
"""

import os
from fractions import Fraction
from music21 import stream, note, meter, clef, bar, metadata, expressions
from music21 import duration as m21duration
from music21.note import Rest as m21Rest

from zeitnetz.pitch import PC_TO_MUSIC21, pc_name
from zeitnetz.constants import BAR
from zeitnetz.core.time_signatures import TS_DEFS, get_ts_for_bar


# ─── Helpers ──────────────────────────────────────────────────────────────

def _make_score(title):
    """Create a music21 Score with metadata."""
    sc = stream.Score()
    sc.metadata = metadata.Metadata()
    sc.metadata.title = title
    sc.metadata.composer = "Zeitnetz Generator"
    return sc


def _build_part_uniform(name, notes_sorted, n_bars, labels_dict=None, lyric_fn=None):
    """Build a part with uniform 3/8 time signature (Stage 4).

    notes_sorted: list of tuples, first element is grid position,
                  second is pitch class.
    """
    part = stream.Part()
    part.partName = name
    ni = 0

    for b in range(n_bars):
        m = stream.Measure(number=b + 1)
        if b == 0:
            m.append(meter.TimeSignature("3/8"))
            m.append(clef.TrebleClef())

        bs = b * BAR
        be = bs + BAR

        if labels_dict:
            for lp, lt in labels_dict.items():
                if bs <= lp < be:
                    te = expressions.TextExpression(lt)
                    te.placement = "above"
                    m.insert(Fraction(lp - bs, 8), te)

        cur = bs
        while cur < be:
            if ni < len(notes_sorted) and notes_sorted[ni][0] == cur:
                entry = notes_sorted[ni]
                n = note.Note(PC_TO_MUSIC21[entry[1]])
                n.quarterLength = Fraction(1, 8)
                if lyric_fn:
                    lyr = lyric_fn(entry)
                    if lyr is not None:
                        n.lyric = lyr
                m.insert(Fraction(cur - bs, 8), n)
                cur += 1
                ni += 1
            else:
                nxt = notes_sorted[ni][0] if ni < len(notes_sorted) else be
                gap = min(nxt, be) - cur
                if gap > 0:
                    r = m21Rest()
                    r.quarterLength = Fraction(gap, 8)
                    m.insert(Fraction(cur - bs, 8), r)
                    cur += gap

        part.append(m)

    ms = part.getElementsByClass(stream.Measure)
    if ms:
        ms[-1].rightBarline = bar.Barline("final")
    return part


def _build_part_v2(name, notes_sorted, n_bars, ts_sequence,
                   labels_dict=None, lyric_fn=None):
    """Build a part with variable time signatures (V2 / Final).

    notes_sorted: list of tuples, first element is grid position,
                  second is pitch class.
    ts_sequence: list of type numbers (1-7), applied cyclically.
    """
    part = stream.Part()
    part.partName = name
    ni = 0
    prev_ts_str = None

    for b in range(n_bars):
        ts_idx = get_ts_for_bar(b, ts_sequence)
        td = TS_DEFS[ts_idx]
        ts_str = td["ts"]
        unit_ql = td["unit_ql"]
        is_tup = td["is_tuplet"]

        m = stream.Measure(number=b + 1)

        # Time signature when it changes
        if ts_str != prev_ts_str:
            m.append(meter.TimeSignature(ts_str))
            if prev_ts_str is None:
                m.append(clef.TrebleClef())
            prev_ts_str = ts_str

        bs = b * BAR

        # Text labels
        if labels_dict:
            for lp, lt in labels_dict.items():
                if bs <= lp < bs + BAR:
                    te = expressions.TextExpression(lt)
                    te.placement = "above"
                    m.insert((lp - bs) * unit_ql, te)

        # Collect 12 slots
        slots = []
        for g in range(BAR):
            gpos = bs + g
            if ni < len(notes_sorted) and notes_sorted[ni][0] == gpos:
                slots.append(notes_sorted[ni])
                ni += 1
            else:
                slots.append(None)

        offset = Fraction(0)

        if not is_tup:
            # Non-tuplet bar
            i = 0
            while i < BAR:
                if slots[i] is not None:
                    entry = slots[i]
                    n = note.Note(PC_TO_MUSIC21[entry[1]])
                    n.quarterLength = unit_ql
                    if lyric_fn:
                        lyr = lyric_fn(entry)
                        if lyr is not None:
                            n.lyric = lyr
                    m.insert(offset, n)
                    offset += unit_ql
                    i += 1
                else:
                    count = 0
                    while i < BAR and slots[i] is None:
                        count += 1
                        i += 1
                    r = m21Rest()
                    r.quarterLength = count * unit_ql
                    m.insert(offset, r)
                    offset += count * unit_ql
        else:
            # Tuplet bar: groups of 3
            tw = td["tup_written"]
            ta = td["tup_actual"]
            tn = td["tup_normal"]

            for g_start in range(0, BAR, 3):
                group = slots[g_start:g_start + 3]

                if all(s is None for s in group):
                    r = m21Rest()
                    r.quarterLength = 3 * unit_ql
                    m.insert(offset, r)
                    offset += 3 * unit_ql
                    continue

                elements = []
                j = 0
                while j < 3:
                    if group[j] is not None:
                        entry = group[j]
                        n = note.Note(PC_TO_MUSIC21[entry[1]])
                        n.quarterLength = unit_ql
                        if lyric_fn:
                            lyr = lyric_fn(entry)
                            if lyr is not None:
                                n.lyric = lyr
                        elements.append(n)
                        j += 1
                    else:
                        rcount = 0
                        while j < 3 and group[j] is None:
                            rcount += 1
                            j += 1
                        r = m21Rest()
                        r.quarterLength = rcount * unit_ql
                        elements.append(r)

                for idx, el in enumerate(elements):
                    tup = m21duration.Tuplet(ta, tn, tw)
                    tup.bracket = True
                    if idx == 0:
                        tup.type = 'start'
                    if idx == len(elements) - 1:
                        tup.type = 'stop'
                    el.duration.tuplets = (tup,)
                    m.insert(offset, el)
                    offset += el.quarterLength

        part.append(m)

    ms = part.getElementsByClass(stream.Measure)
    if ms:
        ms[-1].rightBarline = bar.Barline("final")
    return part


# ─── Export functions ─────────────────────────────────────────────────────

def export_stage4(s4, output_dir="."):
    """Export Stage 4 Full Score (uniform 3/8)."""
    filename = os.path.join(output_dir, "zeitnetz_stage4_score.musicxml")
    sc = _make_score("Full Score — Zeitnetz + Sound Families")

    # Zeitnetz staff
    zn_labels = {pos: label for label, pos in s4.row_start_pos.items()}
    zn_sorted = [(ev.pos, ev.pc, ev.dur) for ev in s4.zn_events]
    zn_part = _build_part_uniform(
        "Zeitnetz", zn_sorted, s4.n_bars, zn_labels,
        lyric_fn=lambda e: str(e[2])
    )
    sc.append(zn_part)

    # Build per-staff note lists
    staff_notes = {}
    staff_labels = {}
    for s in range(1, s4.n_staves + 1):
        staff_notes[s] = []
        staff_labels[s] = {}

    for fn, entries in s4.fam_entries.items():
        if not entries:
            continue
        s = s4.staff_assign.get(fn, 1)
        if s not in staff_notes:
            staff_notes[s] = []
            staff_labels[s] = {}
        for i, entry in enumerate(entries):
            staff_notes[s].append((entry.pos, entry.pc, entry.dur))
            if i == 0:
                staff_labels[s][entry.pos] = f"F{fn}"

    for s in staff_notes:
        staff_notes[s].sort()

    for s in range(1, s4.n_staves + 1):
        p = _build_part_uniform(
            f"Staff {s}", staff_notes.get(s, []), s4.n_bars,
            staff_labels.get(s, {}),
            lyric_fn=lambda e: str(e[2])
        )
        sc.append(p)

    sc.write("musicxml", fp=filename)
    return filename


def export_v2(s4, ts_sequence, output_dir="."):
    """Export Zeitnetz V2 (variable time signatures)."""
    filename = os.path.join(output_dir, "zeitnetz_v2.musicxml")
    sc = _make_score("Zeitnetz Version 2 — Variable Time Signatures")

    # Zeitnetz staff
    zn_labels = {pos: label for label, pos in s4.row_start_pos.items()}
    zn_sorted = [(ev.pos, ev.pc, ev.dur) for ev in s4.zn_events]
    zn_part = _build_part_v2(
        "Zeitnetz", zn_sorted, s4.n_bars, ts_sequence, zn_labels,
        lyric_fn=lambda e: str(e[2])
    )
    sc.append(zn_part)

    # Build per-staff note lists
    staff_notes = {}
    staff_labels = {}
    for s in range(1, s4.n_staves + 1):
        staff_notes[s] = []
        staff_labels[s] = {}

    for fn, entries in s4.fam_entries.items():
        if not entries:
            continue
        s = s4.staff_assign.get(fn, 1)
        if s not in staff_notes:
            staff_notes[s] = []
            staff_labels[s] = {}
        for i, entry in enumerate(entries):
            staff_notes[s].append((entry.pos, entry.pc, entry.dur))
            if i == 0:
                staff_labels[s][entry.pos] = f"F{fn}"

    for s in staff_notes:
        staff_notes[s].sort()

    for s in range(1, s4.n_staves + 1):
        p = _build_part_v2(
            f"Staff {s}", staff_notes.get(s, []), s4.n_bars, ts_sequence,
            staff_labels.get(s, {}),
            lyric_fn=lambda e: str(e[2])
        )
        sc.append(p)

    sc.write("musicxml", fp=filename)
    return filename


def export_final(s5, families, ts_sequence, output_dir="."):
    """Export Zeitnetz Final (duration-as-count, variable TS)."""
    filename = os.path.join(output_dir, "zeitnetz_final.musicxml")
    sc = _make_score("Zeitnetz Final — Duration as Count")

    # Zeitnetz staff (only up to n_bars)
    zn_labels = {pos: label for label, pos in s5.row_start_pos.items()}
    max_pos = s5.n_bars * BAR
    zn_sorted = [(ev.pos, ev.pc, ev.dur) for ev in s5.zn_events if ev.pos < max_pos]
    zn_part = _build_part_v2(
        "Zeitnetz", zn_sorted, s5.n_bars, ts_sequence, zn_labels,
        lyric_fn=lambda e: str(e[2])
    )
    sc.append(zn_part)

    # Build per-staff note lists with F.E labels
    staff_notes = {}
    staff_labels = {}
    for s in range(1, s5.n_staves + 1):
        staff_notes[s] = []
        staff_labels[s] = {}

    # Build a lookup for family entry labels
    entry_labels = {}  # (pos, pc) -> "F.E" label
    for fn, entries in s5.final_entries.items():
        if not entries:
            continue
        s = s5.staff_assign.get(fn, 1)
        if s not in staff_notes:
            staff_notes[s] = []
            staff_labels[s] = {}
        for i, entry in enumerate(entries):
            label = f"{fn}.{i + 1}"
            staff_notes[s].append((entry.pos, entry.pc, entry.dur, label))
            if i == 0:
                staff_labels[s][entry.pos] = f"F{fn}"

    for s in staff_notes:
        staff_notes[s].sort()

    for s in range(1, s5.n_staves + 1):
        p = _build_part_v2(
            f"Staff {s}", staff_notes.get(s, []), s5.n_bars, ts_sequence,
            staff_labels.get(s, {}),
            lyric_fn=lambda e: e[3] if len(e) > 3 else None
        )
        sc.append(p)

    sc.write("musicxml", fp=filename)
    return filename
