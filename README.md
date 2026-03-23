# Zeitnetz Generator

A generalized algorithmic time-grid generator for music composition, based on the system used by Helmut Lachenmann in *Mouvement (– vor der Erstarrung)* as analyzed by Luís Antunes Pena.

The generator takes a **12-tone row**, **permutation pattern**, and **duration list** as input and produces a complete multi-stage compositional scaffold as MusicXML scores.

## Installation

Requires Python 3.9+ and [music21](https://web.mit.edu/music21/).

```bash
pip install music21
```

## Usage

### Generate (full pipeline)

```bash
# Default inputs (Lachenmann's Mouvement)
python -m zeitnetz generate --output-dir ./output

# Custom inputs
python -m zeitnetz generate \
  --pitches "0 1 2 3 4 5 6 7 8 9 10 11" \
  --perm "1 5 0 6 2 7 11 8 3 10 4 9" \
  --durations "-11 6 9 7 6 6 4 3 10 6 3 1 10" \
  --output-dir ./output

# With auto-generated time signatures
python -m zeitnetz generate --auto-ts --output-dir ./output

# With custom time signature sequence
python -m zeitnetz generate --ts-sequence "7 6 5 4 3 2 1 1 2 3 4 5 6 7" --output-dir ./output
```

### Validate (check inputs before generating)

```bash
python -m zeitnetz validate \
  --pitches "cis h c gis a dis fis e d ais f g" \
  --perm "1 5 0 6 2 7 11 8 3 10 4 9" \
  --durations "-11 6 9 7 6 6 4 3 10 6 3 1 10"
```

If inputs fail, the validator suggests repairs (rotations, transpositions).

### Discover (find viable input combinations)

```bash
# Test 100 random combinations
python -m zeitnetz discover --trials 100 --seed 42

# Find combinations with many families
python -m zeitnetz discover --trials 200 --min-families 50
```

## Pipeline Stages

| Stage | Description | Output |
|-------|-------------|--------|
| 1 | Row Generation — permutation matrix, onsets, rhythm row | Internal |
| 2 | Zeitnetz V1 — 12 rows via circular scanning | Internal |
| 3 | Klangfamilien — sound families (dynamic count) | Internal |
| 4 | Full Score — cyclic Zeitnetz + families, uniform 3/8 | `zeitnetz_stage4_score.musicxml` |
| V2 | Variable time signatures (7 types, cyclic sequence) | `zeitnetz_v2.musicxml` |
| Final | Duration-as-count transformation | `zeitnetz_final.musicxml` |

## Time Signature Types

| Type | Time Sig | Unit | Tuplet |
|------|----------|------|--------|
| 1 | 3/8 | 32nd note | No |
| 2 | 4/8 | 16th-note triplet | Yes (3:2) |
| 3 | 3/4 | 16th note | No |
| 4 | 4/4 | 8th-note triplet | Yes (3:2) |
| 5 | 3/2 | 8th note | No |
| 6 | 4/2 | quarter-note triplet | Yes (3:2) |
| 7 | 12/4 | quarter note | No |

## Input Parameters

| Parameter | Format | Example |
|-----------|--------|---------|
| Pitch row | 12 pitch classes (0–11 or German names) | `cis h c gis a dis fis e d ais f g` |
| Permutation | 12 integers (0-indexed permutation of 0–11) | `1 5 0 6 2 7 11 8 3 10 4 9` |
| Durations | 13 integers (first may be negative) | `-11 6 9 7 6 6 4 3 10 6 3 1 10` |

## Architecture

```
zeitnetz/
  cli.py              — Command-line interface (generate, validate, discover)
  constants.py         — Fixed system constants
  pitch.py             — Pitch class utilities
  validate.py          — Input validation + repair suggestions
  discover.py          — Discovery mode (random search)
  stages/
    stage1_rows.py     — Permutation matrix + rhythm row
    stage2_zeitnetz_v1.py — Circular scanning
    stage3_families.py — Sound family derivation (dynamic count)
    stage4_score.py    — Full score computation
    stage5_final.py    — Duration-as-count transformation
  core/
    zeitnetz_grid.py   — Shared grid construction + cyclic extension
    family_scan.py     — Sequential activation scan
    time_signatures.py — 7 TS types + sequence generation
    staff_assignment.py — Round-robin + greedy assignment
  export/
    musicxml.py        — MusicXML generation via music21
```

## References

- Pena, Luís Antunes. *Lachenmann: Mouvement (– vor der Erstarrung). Eine analytische Betrachtung.* Diplomarbeit, Universität für Musik und darstellende Kunst Graz, 2004.
- Cavallotti, Pietro. *Differenzen. Poststrukturalismus und Neue Musik.* Schliengen: Edition Argus, 2006.

## License

Research and educational use.
