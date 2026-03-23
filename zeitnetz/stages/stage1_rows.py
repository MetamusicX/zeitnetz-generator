"""Stage 1 — Row Generation.

Builds the permutation matrix, computes onsets, derives the rhythm row,
and generates all 12 pitch and rhythm permutations.

OM patch: "1-erzeugt-reihe"
"""

from dataclasses import dataclass, field
from zeitnetz.pitch import pc_name


@dataclass
class Stage1Result:
    pitch_row: list
    rhythm_row: list
    perm_matrix: list
    onsets: list
    pitch_perms: list
    rhythm_perms: list


def build_permutation_matrix(perm_pattern):
    """Build a 12x12 permutation matrix.
    Row 0 = identity [0..11].
    Row k = Row k-1 re-indexed by perm_pattern."""
    matrix = [list(range(12))]
    for k in range(1, 12):
        prev = matrix[k - 1]
        matrix.append([prev[perm_pattern[i]] for i in range(12)])
    return matrix


def compute_onsets(duration_list):
    """Cumulative onset positions in the flattened matrix.
    duration_list[0] may be negative (rest); its absolute value is the first onset.
    Returns 12 integers."""
    onsets = [abs(duration_list[0])]
    for j in range(1, 12):
        onsets.append(onsets[-1] + duration_list[j])
    return onsets


def derive_rhythm_row(pitch_row, perm_matrix, onsets):
    """Flatten the permutation matrix and use onsets to place pitches.
    Raises ValueError on collision or incomplete fill."""
    concat = [val for row in perm_matrix for val in row]
    rhythm_row = [None] * 12
    for i in range(12):
        if onsets[i] >= len(concat):
            raise ValueError(
                f"Onset {onsets[i]} exceeds matrix size {len(concat)}. "
                f"Duration list may be too large."
            )
        address = concat[onsets[i]]
        if rhythm_row[address] is not None:
            raise ValueError(
                f"Collision at slot {address}: "
                f"{pc_name(rhythm_row[address])} vs {pc_name(pitch_row[i])}"
            )
        rhythm_row[address] = pitch_row[i]
    if None in rhythm_row:
        missing = [j for j, x in enumerate(rhythm_row) if x is None]
        raise ValueError(f"Rhythm row incomplete — empty slots: {missing}")
    return rhythm_row


def generate_permutations(source_row, perm_matrix):
    """Apply all 12 matrix rows to source_row -> 12 permutations."""
    return [
        [source_row[perm_matrix[k][i]] for i in range(12)]
        for k in range(12)
    ]


def run(pitch_row, perm_pattern, duration_list):
    """Execute Stage 1 and return a Stage1Result."""
    matrix = build_permutation_matrix(perm_pattern)
    onsets = compute_onsets(duration_list)
    rhythm_row = derive_rhythm_row(pitch_row, matrix, onsets)
    pitch_perms = generate_permutations(pitch_row, matrix)
    rhythm_perms = generate_permutations(rhythm_row, matrix)
    return Stage1Result(
        pitch_row=pitch_row,
        rhythm_row=rhythm_row,
        perm_matrix=matrix,
        onsets=onsets,
        pitch_perms=pitch_perms,
        rhythm_perms=rhythm_perms,
    )
