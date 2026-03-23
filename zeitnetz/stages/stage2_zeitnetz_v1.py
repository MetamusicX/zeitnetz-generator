"""Stage 2 — Zeitnetz Version 1 (circular scanning).

Concatenates all 12 rhythm-row permutations into one 144-element circular tape.
A cursor scans forward to locate each target pitch class; the step count
becomes the duration in 32nd-note units.

OM patch: "2 - Zeitnetz Version 1"
"""

from dataclasses import dataclass


@dataclass
class VoiceData:
    voice_index: int
    pitch_perm: list
    rhythm_perm: list
    initial_rest_32nds: int
    notes: list  # [(pc, dur_32), ...]


def run(s1):
    """Execute Stage 2: circular scanning on the 144-element rhythm tape.
    Returns a list of 12 VoiceData objects."""
    # Build 144-element tapes from all 12 permutations
    rhythm_tape = []
    pitch_targets = []
    for k in range(12):
        rhythm_tape.extend(s1.rhythm_perms[k])
        pitch_targets.extend(s1.pitch_perms[k])

    tape_len = len(rhythm_tape)  # 144

    # Scan the rhythm tape for every target pitch class
    cursor = 0
    flat = []
    for i in range(tape_len):
        target_pc = pitch_targets[i]
        count = 0
        scan = cursor
        while True:
            scan = (scan + 1) % tape_len
            count += 1
            if rhythm_tape[scan] == target_pc:
                break
        flat.append(count)
        cursor = scan

    # flat[0] = initial rest; flat[1:] grouped in 12s = per-row durations
    initial_rest = flat[0]

    voices = []
    for k in range(12):
        start = 1 + k * 12
        durs = flat[start: start + 12]

        # Last row may be 1 short — compute missing 12th duration
        if len(durs) < 12:
            target_pc = pitch_targets[(k * 12 + len(durs)) % tape_len]
            count = 0
            scan = cursor
            while True:
                scan = (scan + 1) % tape_len
                count += 1
                if rhythm_tape[scan] == target_pc:
                    break
            durs.append(count)
            cursor = scan

        pitches = s1.pitch_perms[k]
        notes = [(pitches[i], durs[i]) for i in range(12)]

        voices.append(VoiceData(
            voice_index=k,
            pitch_perm=pitches,
            rhythm_perm=s1.rhythm_perms[k],
            initial_rest_32nds=initial_rest if k == 0 else 0,
            notes=notes,
        ))

    return voices
