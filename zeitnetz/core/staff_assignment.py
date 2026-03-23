"""Staff assignment algorithms for family staves."""


def round_robin(n_families, n_staves=12):
    """Assign families to staves using round-robin.
    Family N (1-based) -> staff ((N-1) % n_staves) + 1.
    Returns dict mapping family_number -> staff_number (1-based)."""
    return {fn: ((fn - 1) % n_staves) + 1 for fn in range(1, n_families + 1)}


def greedy_assign(family_spans):
    """Assign families to staves minimising the total number of staves.

    Uses the classic greedy interval scheduling algorithm:
    sort by start, assign to first available staff.

    Parameters
    ----------
    family_spans : list of (family_number, start_pos, end_pos)

    Returns
    -------
    assignment : dict mapping family_number -> staff_number (1-based)
    n_staves : int
    """
    sorted_spans = sorted(family_spans, key=lambda x: x[1])

    staff_ends = []  # end position of last family on each staff
    assignment = {}

    for fn, start, end in sorted_spans:
        placed = False
        for si in range(len(staff_ends)):
            if start > staff_ends[si]:  # no overlap
                staff_ends[si] = end
                assignment[fn] = si + 1
                placed = True
                break
        if not placed:
            staff_ends.append(end)
            assignment[fn] = len(staff_ends)

    return assignment, len(staff_ends)
