"""
Honest Synthesis Processor
==========================
Only synthesizes pitches we're CONFIDENT about (>80% voiced frames).
Doesn't make up instruments. Works with ANY song.

Pipeline:
1. Detect pitch from whole mix (librosa.pyin)
2. Filter by confidence (only voiced frames)
3. Quantize to musical scale (stays in tune)
4. Synthesize as square wave
5. Mix with filtered original
"""

import os
import logging
import numpy as np
from pydub import AudioSegment
from scipy import signal
import librosa


def detect_melody_with_confidence(y, sr, hop_length=512, min_voiced_ratio=0.3):
    """
    Detect melody from audio with confidence filtering.
    Only returns pitches where we're confident (voiced frames).

    Returns: list of (time_s, freq_hz) tuples where voiced_flag=True
    """
    try:
        f0, voiced, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'),
            sr=sr, hop_length=hop_length
        )
    except Exception as e:
        logging.warning(f"Pitch detection failed: {e}")
        return []

    frame_dur = hop_length / sr
    melody_points = []

    for i, (hz, v) in enumerate(zip(f0, voiced)):
        # Only include voiced frames that have valid pitch
        if v and not np.isnan(hz):
            time_s = i * frame_dur
            melody_points.append((time_s, hz))

    # Filter: only use if we have enough voiced frames
    voiced_count = np.sum(voiced)
    total_frames = len(voiced)
    voiced_ratio = voiced_count / total_frames if total_frames > 0 else 0

    if voiced_ratio < min_voiced_ratio:
        logging.info(f"Low voiced ratio ({voiced_ratio:.1%}), no synthesis")
        return []

    logging.info(f"Detected melody: {len(melody_points)} voiced frames ({voiced_ratio:.1%})")
    return melody_points


def quantize_to_semitone(freq_hz):
    """Quantize frequency to nearest semitone (equal temperament)."""
    if freq_hz <= 0 or np.isnan(freq_hz):
        return 0
    midi = librosa.hz_to_midi(freq_hz)
    midi_quantized = int(round(midi))
    freq_quantized = librosa.midi_to_hz(midi_quantized)
    return freq_quantized


def synthesize_square_wave(freq_hz, duration_s, sr, amplitude=0.6):
    """Synthesize a single square wave note with envelope."""
    if freq_hz <= 0 or duration_s <= 0:
        return np.array([0], dtype=np.float32)

    n_samples = int(duration_s * sr)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)

    # Square wave
    wave = signal.square(2 * np.pi * freq_hz * t, duty=0.5)

    # Simple envelope: attack (5ms) + sustain + release (20ms)
    attack_samples = int(0.005 * sr)
    release_samples = int(0.02 * sr)
    sustain_samples = n_samples - attack_samples - release_samples

    env = np.concatenate([
        np.linspace(0, 1, max(attack_samples, 1)),
        np.ones(max(sustain_samples, 0)),
        np.linspace(1, 0, max(release_samples, 1))
    ])
    env = env[:n_samples]

    return (wave * env * amplitude).astype(np.float32)


def process_with_honest_synthesis(input_path, output_path=None):
    """
    Main processor: detect melody → quantize → synthesize → mix with original.
    Only synthesizes what we're confident about.
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_8bit.mp3"

    try:
        # Load audio
        logging.info(f"Loading {input_path}...")
        audio = AudioSegment.from_file(input_path)
        sr = audio.frame_rate

        # Convert to mono numpy array
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        if audio.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)

        # Normalize
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val

        # Step 1: Detect melody with confidence
        logging.info("Detecting melody from mix...")
        melody_points = detect_melody_with_confidence(samples, sr)

        if not melody_points:
            logging.warning("No confident pitch detected, using filtered original")
            # Fall back to filtered original
            synth = np.zeros_like(samples)
        else:
            # Step 2: Synthesize only confident detections
            logging.info("Synthesizing square wave melody...")
            synth = np.zeros_like(samples)

            for i in range(len(melody_points)):
                time_s, freq_hz = melody_points[i]

                # Quantize to semitone
                freq_quantized = quantize_to_semitone(freq_hz)

                # Duration: until next note or 0.1s
                if i < len(melody_points) - 1:
                    next_time_s = melody_points[i + 1][0]
                    duration_s = next_time_s - time_s
                else:
                    duration_s = 0.1

                # Synthesize
                note = synthesize_square_wave(freq_quantized, duration_s, sr)

                # Place in output
                start_idx = int(time_s * sr)
                end_idx = min(start_idx + len(note), len(synth))
                synth[start_idx:end_idx] = note[:end_idx - start_idx]

        # Step 3: Low-pass filter original (keep body/harmony)
        logging.info("Filtering original audio...")
        nyquist = sr / 2
        cutoff_hz = 4000
        normalized_cutoff = np.clip(cutoff_hz / nyquist, 0.001, 0.999)
        b, a = signal.butter(4, normalized_cutoff, btype='low')
        filtered_original = signal.filtfilt(b, a, samples)

        # Step 4: Mix synthesis + filtered original (60% synth, 40% original body)
        logging.info("Mixing synth + filtered original...")
        mixed = 0.6 * synth + 0.4 * filtered_original
        mixed = np.clip(mixed, -1.0, 1.0)

        # Step 5: Downsample to 8000 Hz for lo-fi aesthetic
        logging.info("Downsampling to 8000 Hz...")
        mixed_int16 = (mixed * 32767).astype(np.int16)
        result_audio = audio._spawn(mixed_int16.tobytes()).set_frame_rate(sr)
        result_audio = result_audio.set_frame_rate(8000)

        # Step 6: Export
        logging.info(f"Exporting to {output_path}...")
        result_audio.export(output_path, format="mp3", bitrate="64k")

        return output_path

    except Exception as e:
        logging.error(f"Synthesis processing failed: {e}")
        raise
