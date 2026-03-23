"""Input validation, viability testing, and repair suggestions.

Three levels:
1. validate_inputs() — check syntax (types, ranges, completeness)
2. test_viability() — run Stages 1–3, then dry-run Stage 4 scan
3. suggest_repairs() — try rotations/transpositions to fix failing inputs
"""

from zeitnetz.pitch import pc_name
from zeitnetz.constants import MAX_CYCLES


def validate_inputs(pitch_row, perm_pattern, duration_list):
    """Check basic input validity.

    Returns dict with:
      valid: bool
      errors: list of str
      warnings: list of str
    """
    errors = []
    warnings = []

    # Pitch row
    if len(pitch_row) != 12:
        errors.append(f"Pitch row must have 12 values, got {len(pitch_row)}")
    elif set(pitch_row) != set(range(12)):
        errors.append("Pitch row must contain each class 0–11 exactly once")

    # Permutation pattern
    if len(perm_pattern) != 12:
        errors.append(f"Permutation must have 12 values, got {len(perm_pattern)}")
    elif set(perm_pattern) != set(range(12)):
        errors.append("Permutation must be a valid permutation of 0–11")
    else:
        # Check for identity permutation
        if perm_pattern == list(range(12)):
            warnings.append("Identity permutation: all matrix rows will be identical")
        # Check for very short cycles
        seen = set()
        current = list(range(12))
        cycle_len = 0
        for _ in range(12):
            current = [current[perm_pattern[i]] for i in range(12)]
            cycle_len += 1
            t = tuple(current)
            if t == tuple(range(12)):
                break
        if cycle_len < 6:
            warnings.append(
                f"Permutation cycle length is {cycle_len} "
                f"(short cycles may produce degenerate matrices)"
            )

    # Duration list
    if len(duration_list) != 13:
        errors.append(f"Duration list must have 13 values, got {len(duration_list)}")
    else:
        if 0 in duration_list[1:]:
            errors.append("Duration list contains zero values (positions 1–12)")
        if any(abs(d) > 100 for d in duration_list):
            warnings.append("Duration list contains very large values (>100)")
        # Check that onsets don't exceed matrix size
        onsets = [abs(duration_list[0])]
        for j in range(1, 12):
            onsets.append(onsets[-1] + duration_list[j])
        if any(o >= 144 for o in onsets):
            errors.append(
                f"Onset {max(onsets)} exceeds matrix size 144. "
                f"Duration values are too large."
            )

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def test_viability(pitch_row, perm_pattern, duration_list, max_cycles=None):
    """Run a full viability test: Stages 1-3, then dry-run Stage 4 scan.

    Returns dict with:
      viable: bool
      n_families: int
      n_same_pitch: int (families where start_pc == end_pc)
      n_cycles_needed: int (0 = no extra cycles, -1 = not viable)
      n_activated: int
      stage1_ok: bool
      stage1_error: str or None
      families_per_row: dict (row -> count)
      details: str (human-readable summary)
    """
    from zeitnetz.stages import stage1_rows, stage2_zeitnetz_v1, stage3_families
    from zeitnetz.core.zeitnetz_grid import build_row_templates, build_grid_until_families_done

    if max_cycles is None:
        max_cycles = MAX_CYCLES

    result = {
        "viable": False,
        "n_families": 0,
        "n_same_pitch": 0,
        "n_cycles_needed": -1,
        "n_activated": 0,
        "stage1_ok": False,
        "stage1_error": None,
        "families_per_row": {},
        "details": "",
    }

    # Stage 1
    try:
        s1 = stage1_rows.run(pitch_row, perm_pattern, duration_list)
        result["stage1_ok"] = True
    except ValueError as e:
        result["stage1_error"] = str(e)
        result["details"] = f"Stage 1 failed: {e}"
        return result

    # Stage 2
    s2 = stage2_zeitnetz_v1.run(s1)

    # Stage 3
    s3_1, families = stage3_families.run(s1)

    n_families = len(families)
    result["n_families"] = n_families

    # Families per row
    from zeitnetz.constants import FAMILY_ROW_ORDER
    for rf in s3_1:
        result["families_per_row"][rf.row_index] = len(rf.pitches)

    # Same-pitch families
    same_pitch = [f for f in families if f.start_pc == f.end_pc]
    result["n_same_pitch"] = len(same_pitch)

    if n_families == 0:
        result["details"] = "No families generated — check inputs"
        return result

    # Dry-run Stage 4 scan
    templates = build_row_templates(s2)
    events, _, _, n_cycles, done = build_grid_until_families_done(
        templates, families, max_cycles=max_cycles
    )
    if done:
        result["viable"] = True
        result["n_cycles_needed"] = n_cycles
        result["n_activated"] = n_families

    # Build details string
    lines = [
        f"Families: {n_families}",
        f"Same-pitch families: {len(same_pitch)}",
    ]
    if same_pitch:
        sp_names = ", ".join(
            f"F{f.family}({pc_name(f.start_pc)})" for f in same_pitch
        )
        lines.append(f"  ({sp_names})")

    for ri in FAMILY_ROW_ORDER:
        count = result["families_per_row"].get(ri, 0)
        lines.append(f"  Row {ri:2d}: {count} families")

    if result["viable"]:
        lines.append(
            f"Viable: YES — {n_families} families, "
            f"{result['n_cycles_needed']} extra cycle(s) needed"
        )
    else:
        lines.append(
            f"Viable: NO — only {result['n_activated']}/{n_families} families "
            f"activated after {max_cycles} cycles"
        )

    result["details"] = "\n".join(lines)
    return result


def suggest_repairs(pitch_row, perm_pattern, duration_list, max_attempts=24):
    """Try rotations and transpositions to find working inputs.

    Tests:
    1. Rotations of the duration list (shift by 1–12)
    2. Transpositions of the pitch row (shift all PCs by 1–11)

    Returns a list of dicts with:
      type: "duration_rotation" or "pitch_transposition"
      offset: int
      pitch_row: list
      perm_pattern: list
      duration_list: list
      viability: dict (from test_viability)
    """
    results = []

    # Duration rotations
    for offset in range(1, 13):
        # Rotate the 12 non-negative durations (positions 1–12),
        # keeping position 0 (initial rest) fixed
        new_durs = [duration_list[0]] + [
            duration_list[1 + (i + offset) % 12] for i in range(12)
        ]
        v = test_viability(pitch_row, perm_pattern, new_durs, max_cycles=10)
        if v["viable"]:
            results.append({
                "type": "duration_rotation",
                "offset": offset,
                "pitch_row": pitch_row,
                "perm_pattern": perm_pattern,
                "duration_list": new_durs,
                "viability": v,
            })

    # Pitch transpositions
    for offset in range(1, 12):
        new_row = [(pc + offset) % 12 for pc in pitch_row]
        v = test_viability(new_row, perm_pattern, duration_list, max_cycles=10)
        if v["viable"]:
            results.append({
                "type": "pitch_transposition",
                "offset": offset,
                "pitch_row": new_row,
                "perm_pattern": perm_pattern,
                "duration_list": duration_list,
                "viability": v,
            })

    # Sort by fewest cycles needed, then most families
    results.sort(key=lambda r: (r["viability"]["n_cycles_needed"],
                                -r["viability"]["n_families"]))

    return results[:max_attempts]
