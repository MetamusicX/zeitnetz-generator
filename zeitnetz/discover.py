"""Discovery mode — test random input combinations for viability.

Generates random 12-tone rows, permutation patterns, and duration lists,
then runs viability tests to find working combinations.
"""

import random
from zeitnetz.pitch import pc_name
from zeitnetz.validate import validate_inputs, test_viability


def random_pitch_row(rng=None):
    """Generate a random 12-tone row."""
    rng = rng or random
    row = list(range(12))
    rng.shuffle(row)
    return row


def random_perm_pattern(rng=None):
    """Generate a random permutation pattern (permutation of 0–11)."""
    rng = rng or random
    perm = list(range(12))
    rng.shuffle(perm)
    return perm


def random_duration_list(rng=None):
    """Generate a random duration list (13 integers).
    First value may be negative (initial rest), rest are small positive."""
    rng = rng or random
    first = rng.randint(-15, -1)
    rest = [rng.randint(1, 10) for _ in range(12)]
    onsets = [abs(first)]
    for j in range(11):
        onsets.append(onsets[-1] + rest[j])
    if max(onsets) >= 144:
        scale = 140 / max(onsets)
        rest = [max(1, int(d * scale)) for d in rest]
    return [first] + rest


def find_valid_duration_list(perm_pattern, rng=None, max_attempts=500):
    """Find a duration list that produces no collisions for the given perm pattern.

    Strategy: build the concat, then find 12 sorted positions in 0–143
    that map to all 12 distinct addresses (0–11). Derive durations from
    the gaps between positions.

    Returns a duration list or None if not found.
    """
    from zeitnetz.stages.stage1_rows import build_permutation_matrix
    rng = rng or random

    matrix = build_permutation_matrix(perm_pattern)
    concat = [val for row in matrix for val in row]

    # Group positions by their address value
    positions_by_value = {v: [] for v in range(12)}
    for i, v in enumerate(concat):
        positions_by_value[v].append(i)

    for _ in range(max_attempts):
        # Pick one random position for each address value (0–11)
        chosen = []
        for v in range(12):
            chosen.append(rng.choice(positions_by_value[v]))

        # Sort to get valid ascending onsets
        chosen.sort()

        # Check all values are distinct (they should be by construction)
        values = [concat[p] for p in chosen]
        if len(set(values)) != 12:
            continue

        # Derive duration list: first = -chosen[0], rest = gaps
        first = -chosen[0]
        rest = [chosen[i+1] - chosen[i] for i in range(11)]
        # Need a 13th value (doesn't affect Stage 1, just padding)
        rest.append(rng.randint(1, 10))

        if all(d > 0 for d in rest[:11]):
            return [first] + rest

    return None


def discover(n_trials=100, seed=None, min_families=30, max_cycles=10,
             verbose=True):
    """Run discovery: test random input combinations.

    Strategy: for each random pitch row + permutation, try multiple
    duration lists (since most failures are Stage 1 collisions caused
    by bad duration values). This dramatically increases hit rate.

    Parameters
    ----------
    n_trials : int
        Number of row/perm combinations to test (each tries up to
        50 duration lists).
    seed : int or None
        Random seed for reproducibility.
    min_families : int
        Minimum number of families to consider a result interesting.
    max_cycles : int
        Maximum cycles to allow in viability test.
    verbose : bool
        Print progress to stdout.

    Returns
    -------
    results : list of dicts with viable combinations, sorted by
              n_families descending.
    """
    rng = random.Random(seed)
    results = []
    viable_count = 0
    stage1_pass = 0

    for trial in range(n_trials):
        pitch_row = random_pitch_row(rng)
        perm_pattern = random_perm_pattern(rng)

        # Find a valid duration list (no Stage 1 collision)
        duration_list = find_valid_duration_list(perm_pattern, rng)
        if duration_list is None:
            continue

        stage1_pass += 1

        try:
            v = test_viability(pitch_row, perm_pattern, duration_list,
                               max_cycles=max_cycles)
        except (ValueError, IndexError):
            continue

        if not v["stage1_ok"]:
            continue

        if v["viable"] and v["n_families"] >= min_families:
            viable_count += 1
            result = {
                "trial": trial,
                "pitch_row": pitch_row,
                "perm_pattern": perm_pattern,
                "duration_list": duration_list,
                "n_families": v["n_families"],
                "n_same_pitch": v["n_same_pitch"],
                "n_cycles_needed": v["n_cycles_needed"],
                "families_per_row": v["families_per_row"],
            }
            results.append(result)

            if verbose:
                row_str = " ".join(pc_name(p) for p in pitch_row)
                print(
                    f"  Trial {trial:4d}: {v['n_families']} families, "
                    f"{v['n_cycles_needed']} cycles | {row_str}"
                )

        if verbose and (trial + 1) % 25 == 0:
            print(f"  ... {trial + 1}/{n_trials} tested, "
                  f"{viable_count} viable, {stage1_pass} passed Stage 1")

    # Sort by most families
    results.sort(key=lambda r: -r["n_families"])

    if verbose:
        print(f"\n  Discovery complete: {viable_count}/{n_trials} viable "
              f"(>= {min_families} families)")
        if results:
            best = results[0]
            print(f"  Best: {best['n_families']} families, "
                  f"{best['n_cycles_needed']} cycles")
            print(f"    Row: {' '.join(pc_name(p) for p in best['pitch_row'])}")
            print(f"    Perm: {best['perm_pattern']}")
            print(f"    Durs: {best['duration_list']}")

    return results
