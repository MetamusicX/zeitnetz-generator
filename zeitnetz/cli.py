"""Command-line interface for the Zeitnetz Generator.

Subcommands:
  generate  — Full pipeline: all stages, export MusicXML
  validate  — Check input viability, suggest repairs if needed
  discover  — Test random input combinations
"""

import argparse
import sys
import os
from zeitnetz.pitch import pc_name, parse_pitch_input, parse_int_list


# ─── Default inputs (Lachenmann's Mouvement) ──────────────────────────────

DEFAULT_PITCHES   = "1 11 0 8 9 3 6 4 2 10 5 7"
DEFAULT_PERM      = "1 5 0 6 2 7 11 8 3 10 4 9"
DEFAULT_DURATIONS = "-11 6 9 7 6 6 4 3 10 6 3 1 10"


def _parse_common_args(args):
    """Parse pitch row, perm pattern, and duration list from CLI args."""
    pitch_row = parse_pitch_input(args.pitches)
    perm_pattern = parse_int_list(args.perm, 12, "Permutation pattern")
    duration_list = parse_int_list(args.durations, 13, "Duration list")
    return pitch_row, perm_pattern, duration_list


# ─── GENERATE ─────────────────────────────────────────────────────────────

def cmd_generate(args):
    """Full pipeline: stages 1-5 + MusicXML export."""
    from zeitnetz.stages import stage1_rows, stage2_zeitnetz_v1, stage3_families
    from zeitnetz.stages import stage4_score, stage5_final
    from zeitnetz.core.time_signatures import (
        generate_auto_ts_sequence, parse_ts_sequence, DEFAULT_TS_SEQ
    )
    from zeitnetz.constants import DEFAULT_TS_SEQ
    from zeitnetz.export.musicxml import export_stage4, export_v2, export_final
    from zeitnetz.validate import validate_inputs, test_viability

    try:
        pitch_row, perm_pattern, duration_list = _parse_common_args(args)
    except ValueError as e:
        print(f"Input error: {e}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    print("\nZeitnetz Generator — Full Pipeline")
    print(f"  Pitch row    : {' '.join(pc_name(p) for p in pitch_row)}")
    print(f"  Perm pattern : {perm_pattern}")
    print(f"  Durations    : {duration_list}")

    # Validate
    check = validate_inputs(pitch_row, perm_pattern, duration_list)
    if not check["valid"]:
        print("\nValidation FAILED:")
        for e in check["errors"]:
            print(f"  ERROR: {e}")
        sys.exit(1)
    for w in check["warnings"]:
        print(f"  WARNING: {w}")

    # Stage 1
    print("\n── Stage 1: Row Generation")
    try:
        s1 = stage1_rows.run(pitch_row, perm_pattern, duration_list)
    except ValueError as e:
        print(f"  FAILED: {e}")
        print("\n  Attempting repairs...")
        from zeitnetz.validate import suggest_repairs
        repairs = suggest_repairs(pitch_row, perm_pattern, duration_list)
        if repairs:
            best = repairs[0]
            print(f"  Suggestion: {best['type']} (offset {best['offset']})")
            print(f"    {best['viability']['n_families']} families, "
                  f"{best['viability']['n_cycles_needed']} cycles")
        else:
            print("  No viable alternatives found.")
        sys.exit(1)

    print(f"  Pitch row : {' '.join(pc_name(p) for p in s1.pitch_row)}")
    print(f"  Rhythm row: {' '.join(pc_name(p) for p in s1.rhythm_row)}")
    print(f"  Onsets    : {s1.onsets}")

    # Stage 2
    print("\n── Stage 2: Zeitnetz V1")
    s2 = stage2_zeitnetz_v1.run(s1)
    for v in s2:
        notes_str = " ".join(f"{pc_name(pc)}({d})" for pc, d in v.notes)
        print(f"  Row {v.voice_index:2d}: rest={v.initial_rest_32nds:2d}  {notes_str}")

    # Stage 3
    print("\n── Stage 3: Klangfamilien")
    s3_1, families = stage3_families.run(s1)
    n_families = len(families)
    same_pitch = [f for f in families if f.start_pc == f.end_pc]
    print(f"  {n_families} sound families derived")
    print(f"  Same-pitch families: {len(same_pitch)}")
    if same_pitch:
        for f in same_pitch:
            print(f"    F{f.family}: {pc_name(f.start_pc)}")

    from zeitnetz.constants import FAMILY_ROW_ORDER
    for rf in s3_1:
        labels = [f"{pc_name(p)}({i+1})" for i, p in enumerate(
            [fam.start_pc for fam in families if fam.row == rf.row_index]
        )]
        if labels:
            fam_start = min(f.family for f in families if f.row == rf.row_index)
            fam_end = max(f.family for f in families if f.row == rf.row_index)
            print(f"  Row {rf.row_index:2d}: F{fam_start}–F{fam_end} "
                  f"({len(rf.pitches)} families)")

    # Stage 4
    print("\n── Stage 4: Full Score")
    s4 = stage4_score.run(s2, families)
    print(f"  {s4.n_bars} bars, {s4.total_32} grid positions")
    print(f"  {s4.n_cycles} extra cycle(s)")
    print(f"  {s4.n_activated}/{n_families} families activated")
    print(f"  {s4.n_staves} staves (round-robin)")

    if not s4.all_done:
        print(f"  WARNING: Not all families completed!")
        if s4.remaining_queue:
            nxt = s4.remaining_queue[0]
            print(f"    Next unactivated: F{nxt.family} "
                  f"(needs {pc_name(nxt.start_pc)})")

    # Time signature sequence
    if args.ts_sequence:
        ts_seq = parse_ts_sequence(args.ts_sequence)
        print(f"\n  Custom TS sequence: {len(ts_seq)} entries")
    elif args.auto_ts:
        ts_seq = generate_auto_ts_sequence(s4.n_bars)
        print(f"\n  Auto-generated TS sequence: {len(ts_seq)} entries")
    else:
        ts_seq = DEFAULT_TS_SEQ
        print(f"\n  Default TS sequence (Mouvement): {len(ts_seq)} entries")

    # Stage 5 (Final)
    print("\n── Stage 5: Zeitnetz Final (duration as count)")
    s5 = stage5_final.run(s2, families, s4)
    print(f"  {s5.n_bars} bars, max grid position: {s5.max_grid_pos}")
    print(f"  {s5.n_staves} staves (greedy assignment)")
    print(f"  {s5.n_cycles} extra cycle(s) for extended grid")

    # Export MusicXML
    print("\n── Exporting MusicXML")
    f = export_stage4(s4, output_dir)
    print(f"  ✓ {f}")
    f = export_v2(s4, ts_seq, output_dir)
    print(f"  ✓ {f}")
    f = export_final(s5, families, ts_seq, output_dir)
    print(f"  ✓ {f}")

    print(f"\n✓ Done. {n_families} families, {s4.n_bars} bars (Stage 4), "
          f"{s5.n_bars} bars (Final).\n")


# ─── VALIDATE ─────────────────────────────────────────────────────────────

def cmd_validate(args):
    """Validate inputs and test viability."""
    from zeitnetz.validate import validate_inputs, test_viability, suggest_repairs

    try:
        pitch_row, perm_pattern, duration_list = _parse_common_args(args)
    except ValueError as e:
        print(f"Input error: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nZeitnetz Generator — Input Validation")
    print(f"  Pitch row    : {' '.join(pc_name(p) for p in pitch_row)}")
    print(f"  Perm pattern : {perm_pattern}")
    print(f"  Durations    : {duration_list}")

    # Syntax check
    check = validate_inputs(pitch_row, perm_pattern, duration_list)
    print(f"\n  Syntax: {'PASS' if check['valid'] else 'FAIL'}")
    for e in check["errors"]:
        print(f"    ERROR: {e}")
    for w in check["warnings"]:
        print(f"    WARNING: {w}")

    if not check["valid"]:
        sys.exit(1)

    # Viability test
    print("\n  Running viability test...")
    v = test_viability(pitch_row, perm_pattern, duration_list)
    print(f"\n{v['details']}")

    if not v["viable"]:
        print("\n  Searching for repairs...")
        repairs = suggest_repairs(pitch_row, perm_pattern, duration_list)
        if repairs:
            print(f"  Found {len(repairs)} viable alternative(s):\n")
            for i, r in enumerate(repairs[:5]):
                rv = r["viability"]
                print(f"    {i+1}. {r['type']} (offset {r['offset']}): "
                      f"{rv['n_families']} families, "
                      f"{rv['n_cycles_needed']} cycles")
                if r["type"] == "pitch_transposition":
                    print(f"       Row: {' '.join(pc_name(p) for p in r['pitch_row'])}")
                else:
                    print(f"       Durs: {r['duration_list']}")
        else:
            print("  No viable alternatives found via rotation/transposition.")

    print()


# ─── DISCOVER ─────────────────────────────────────────────────────────────

def cmd_discover(args):
    """Test random input combinations."""
    from zeitnetz.discover import discover

    print(f"\nZeitnetz Generator — Discovery Mode")
    print(f"  Trials: {args.trials}")
    print(f"  Seed: {args.seed}")
    print(f"  Min families: {args.min_families}\n")

    results = discover(
        n_trials=args.trials,
        seed=args.seed,
        min_families=args.min_families,
        verbose=True,
    )

    if results and args.show_top:
        n = min(args.show_top, len(results))
        print(f"\n  Top {n} results:")
        for i, r in enumerate(results[:n]):
            row_str = " ".join(pc_name(p) for p in r["pitch_row"])
            print(f"\n  {i+1}. {r['n_families']} families, "
                  f"{r['n_cycles_needed']} cycles, "
                  f"{r['n_same_pitch']} same-pitch")
            print(f"     Row : {row_str}")
            print(f"     Perm: {r['perm_pattern']}")
            print(f"     Durs: {r['duration_list']}")

    print()


# ─── MAIN ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Zeitnetz Generator — algorithmic time-grid composition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate
    gen = subparsers.add_parser("generate", help="Full pipeline + MusicXML export")
    gen.add_argument("--pitches", type=str, default=DEFAULT_PITCHES,
                     help="12 pitch classes (integers 0–11 or German names)")
    gen.add_argument("--perm", type=str, default=DEFAULT_PERM,
                     help="Permutation pattern (12 integers, 0-indexed)")
    gen.add_argument("--durations", type=str, default=DEFAULT_DURATIONS,
                     help="Duration list (13 integers; first may be negative)")
    gen.add_argument("--ts-sequence", type=str, default=None,
                     help="Custom time signature sequence (space-separated 1–7)")
    gen.add_argument("--auto-ts", action="store_true",
                     help="Auto-generate TS sequence based on piece length")
    gen.add_argument("--output-dir", type=str, default=".",
                     help="Output directory for MusicXML files")
    gen.set_defaults(func=cmd_generate)

    # Validate
    val = subparsers.add_parser("validate", help="Check input viability")
    val.add_argument("--pitches", type=str, default=DEFAULT_PITCHES,
                     help="12 pitch classes")
    val.add_argument("--perm", type=str, default=DEFAULT_PERM,
                     help="Permutation pattern")
    val.add_argument("--durations", type=str, default=DEFAULT_DURATIONS,
                     help="Duration list")
    val.set_defaults(func=cmd_validate)

    # Discover
    disc = subparsers.add_parser("discover", help="Test random combinations")
    disc.add_argument("--trials", type=int, default=100,
                      help="Number of random trials (default: 100)")
    disc.add_argument("--seed", type=int, default=None,
                      help="Random seed for reproducibility")
    disc.add_argument("--min-families", type=int, default=30,
                      help="Minimum families to report (default: 30)")
    disc.add_argument("--show-top", type=int, default=10,
                      help="Show top N results (default: 10)")
    disc.set_defaults(func=cmd_discover)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)
