"""
Chiptune Synthesis Processor
============================
Converts audio stems to authentic chiptune by:
1. Detecting pitches with librosa.pyin
2. Quantizing to musical notes (semitones)
3. Synthesizing discrete notes with appropriate waveforms
4. Applying per-note ADSR envelopes
"""

import numpy as np
from pydub import AudioSegment
import scipy.signal
import librosa
import logging


def make_adsr_envelope(n, sr, attack=0.005, decay=0.05, sustain=0.7, release=0.02):
    """Create per-note ADSR envelope (Attack, Decay, Sustain, Release)."""
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    s = n - a - d - r

    env = np.concatenate([
        np.linspace(0, 1, max(a, 1)),
        np.linspace(1, sustain, max(d, 1)),
        np.full(max(s, 0), sustain),
        np.linspace(sustain, 0, max(r, 1))
    ])
    return env[:n]


def pyin_to_note_events(y, sr, fmin, fmax, hop_length=512, min_duration=0.05):
    """
    Extract note events from audio using librosa.pyin.
    Returns list of (start_s, duration_s, freq_hz).
    """
    try:
        f0, voiced, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz(fmin), fmax=librosa.note_to_hz(fmax),
            sr=sr, hop_length=hop_length
        )
    except Exception as e:
        logging.warning(f"pyin failed: {e}, returning empty notes")
        return []

    notes = []
    prev_midi = None
    start_frame = None
    frame_dur = hop_length / sr

    for i, (hz, v) in enumerate(zip(f0, voiced)):
        if not v or np.isnan(hz):
            midi = None
        else:
            midi = int(round(librosa.hz_to_midi(hz)))

        if midi != prev_midi:
            # Emit previous note if it existed
            if prev_midi is not None and start_frame is not None:
                dur_frames = i - start_frame
                duration = dur_frames * frame_dur
                if duration >= min_duration:
                    freq = librosa.midi_to_hz(prev_midi)
                    notes.append((start_frame * frame_dur, duration, freq))
            # Start new note
            start_frame = i if midi is not None else None
            prev_midi = midi

    # Emit final note
    if prev_midi is not None and start_frame is not None:
        dur_frames = len(f0) - start_frame
        duration = dur_frames * frame_dur
        if duration >= min_duration:
            freq = librosa.midi_to_hz(prev_midi)
            notes.append((start_frame * frame_dur, duration, freq))

    return notes


def synthesize_note(freq_hz, duration_s, sr, waveform='square', duty=0.25, amplitude=0.7):
    """Synthesize a single note with ADSR envelope."""
    n_samples = int(duration_s * sr)
    if n_samples < 1:
        return np.array([0], dtype=np.float32)

    t = np.linspace(0, duration_s, n_samples, endpoint=False)

    if waveform == 'square':
        wave = scipy.signal.square(2 * np.pi * freq_hz * t, duty=duty)
    elif waveform == 'triangle':
        wave = scipy.signal.sawtooth(2 * np.pi * freq_hz * t, width=0.5)
    elif waveform == 'sine':
        wave = np.sin(2 * np.pi * freq_hz * t)
    else:
        wave = scipy.signal.square(2 * np.pi * freq_hz * t, duty=duty)

    # Apply ADSR envelope
    env = make_adsr_envelope(n_samples, sr, attack=0.005, decay=0.05, sustain=0.7, release=0.02)

    return (wave * env * amplitude).astype(np.float32)


def process_stem(filepath, stem_type):
    """Convert a stem to chiptune by pitch detection + synthesis."""
    audio = AudioSegment.from_file(filepath)
    sr = 8000
    audio = audio.set_frame_rate(sr).set_channels(1)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    original_length = len(samples)

    # Normalize to -1..1 range
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples /= max_val

    # Process based on stem type
    if stem_type == "vocals":
        # Silence vocals (chiptune typically doesn't have vocals)
        output = np.zeros(original_length, dtype=np.float32)

    elif stem_type == "other":
        # Melody/harmony: detect pitch and synthesize as square wave
        notes = pyin_to_note_events(samples, sr, 'C2', 'C7')
        output = np.zeros(original_length, dtype=np.float32)
        for start_s, dur_s, freq in notes:
            start_idx = int(start_s * sr)
            end_idx = int((start_s + dur_s) * sr)
            end_idx = min(end_idx, original_length)  # Clamp to output length
            if start_idx >= original_length:
                continue
            note_wave = synthesize_note(freq, dur_s, sr, waveform='square', duty=0.25)
            available_samples = end_idx - start_idx
            output[start_idx:end_idx] = np.maximum(output[start_idx:end_idx],
                                                   note_wave[:available_samples])

    elif stem_type == "bass":
        # Bass: detect pitch and synthesize as 4-bit triangle wave
        notes = pyin_to_note_events(samples, sr, 'C1', 'C4')
        output = np.zeros(original_length, dtype=np.float32)
        for start_s, dur_s, freq in notes:
            start_idx = int(start_s * sr)
            end_idx = int((start_s + dur_s) * sr)
            end_idx = min(end_idx, original_length)  # Clamp to output length
            if start_idx >= original_length:
                continue
            note_wave = synthesize_note(freq, dur_s, sr, waveform='triangle')
            # 4-bit quantize the triangle wave (NES triangle channel effect)
            note_wave = np.round(note_wave * 7.5) / 7.5
            available_samples = end_idx - start_idx
            output[start_idx:end_idx] = np.maximum(output[start_idx:end_idx],
                                                   note_wave[:available_samples])

    elif stem_type == "drums":
        # Drums: detect onsets and synthesize noise bursts
        try:
            onsets = librosa.onset.onset_detect(y=samples, sr=sr)
            onset_times = librosa.frames_to_time(onsets, sr=sr)
        except Exception as e:
            logging.warning(f"Onset detection failed: {e}, using empty drum output")
            onset_times = []

        output = np.zeros(original_length, dtype=np.float32)

        for onset_time in onset_times:
            # Create a short noise burst with exponential decay
            burst_dur = 0.15
            burst_samples = int(burst_dur * sr)
            noise = np.random.choice([-1.0, 1.0], size=burst_samples)
            decay = np.exp(-np.linspace(0, 8, burst_samples))
            drum_hit = (noise * decay * 0.8).astype(np.float32)

            start_idx = int(onset_time * sr)
            end_idx = min(start_idx + burst_samples, original_length)
            if start_idx >= original_length:
                continue
            available_samples = end_idx - start_idx
            output[start_idx:end_idx] = np.maximum(output[start_idx:end_idx],
                                                   drum_hit[:available_samples])
    else:
        output = samples

    # Ensure output is in int16 range and clip to [-1, 1], maintaining original length
    output = np.clip(output, -1.0, 1.0)
    output = (output * 32767).astype(np.int16)

    # Ensure exact output length matches input
    if len(output) < original_length:
        output = np.pad(output, (0, original_length - len(output)), mode='constant')
    elif len(output) > original_length:
        output = output[:original_length]

    return audio._spawn(output.tobytes()).set_frame_rate(sr)
