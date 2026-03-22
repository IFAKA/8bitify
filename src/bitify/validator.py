"""
Chiptune Authenticity Validator
================================
Measures the actual audio properties of a processed file against known 
chiptune / 8-bit hardware constraints. Returns a score 0-100.

Metrics:
  1. Sample Rate  — must be <= 11025Hz (NES: 11025, GB: 8192)
  2. Bit depth quantization — unique amplitude levels should be <= 256
  3. High-frequency suppression — energy above 3.5kHz relative to below it must be < 5%
  4. Waveform saturation — ratio of samples at or near clipping limits (square-wave shape)
  5. Dynamic range compression — difference between max and RMS should be low (< 12dB)
"""

import sys
import numpy as np
from scipy.io import wavfile
from scipy import signal
from pydub import AudioSegment
import tempfile
import os


def load_as_wav_array(filepath):
    """Load any audio file into a mono numpy int16 array with its sample rate."""
    audio = AudioSegment.from_file(filepath)
    audio = audio.set_channels(1)
    sr = audio.frame_rate
    samples = np.array(audio.get_array_of_samples(), dtype=np.int16)
    return sr, samples


def measure_sample_rate(sr):
    """
    Chiptune constraint: sample rate <= 11025 Hz.
    Score: 100 if <= 8000, scaled down to 0 at >= 44100.
    """
    if sr <= 8000:
        return 100, sr
    if sr >= 44100:
        return 0, sr
    # linear interpolation between 8000 and 44100
    score = 100 * (1 - (sr - 8000) / (44100 - 8000))
    return round(score, 1), sr


def measure_quantization(samples):
    """
    8-bit hardware has max 256 discrete amplitude levels.
    We normalize samples to -128..127 and count unique values.
    Score: 100 if <= 256, 0 if >= 65536 (16-bit full range).
    """
    # Normalize int16 range (-32768..32767) to int8-ish range
    normalized = (samples / 256.0).astype(np.int16)
    unique_levels = len(np.unique(normalized))

    if unique_levels <= 256:
        score = 100
    elif unique_levels >= 32768:
        score = 0
    else:
        score = 100 * (1 - (unique_levels - 256) / (32768 - 256))
    return round(score, 1), unique_levels


def measure_hf_suppression(samples, sr):
    """
    Retro chips cut off near Nyquist (4kHz at 8kHz sr).
    We measure energy ratio above 3.5kHz vs total energy.
    Score: 100 if < 1%, 0 if > 20%.
    """
    cutoff_hz = 3500
    nyquist = sr / 2

    if cutoff_hz >= nyquist:
        # Sample rate is already low enough, full score
        return 100, 0.0

    samples_f = samples.astype(np.float64)
    freqs, psd = signal.welch(samples_f, fs=sr, nperseg=min(1024, len(samples_f)))

    hf_mask = freqs >= cutoff_hz
    total_energy = np.sum(psd)
    hf_energy = np.sum(psd[hf_mask])

    if total_energy == 0:
        return 100, 0.0

    hf_ratio_pct = (hf_energy / total_energy) * 100

    if hf_ratio_pct <= 1.0:
        score = 100
    elif hf_ratio_pct >= 20.0:
        score = 0
    else:
        score = 100 * (1 - (hf_ratio_pct - 1.0) / (20.0 - 1.0))
    return round(score, 1), round(hf_ratio_pct, 2)


def measure_waveform_saturation(samples):
    """
    Square waves spend most of their time at max/min amplitude.
    We check what fraction of samples are in the outer 20% of the amplitude range.
    Score: 100 if > 60% saturated, 0 if < 5%.
    """
    peak = np.max(np.abs(samples))
    if peak == 0:
        return 0, 0.0
    normalized = np.abs(samples.astype(np.float64)) / peak
    saturated_ratio = np.mean(normalized >= 0.80) * 100

    if saturated_ratio >= 60.0:
        score = 100
    elif saturated_ratio <= 5.0:
        score = 0
    else:
        score = 100 * (saturated_ratio - 5.0) / (60.0 - 5.0)
    return round(score, 1), round(saturated_ratio, 2)


def measure_dynamic_range(samples):
    """
    8-bit chips have very compressed audio — little dynamic range.
    We measure crest factor (peak dB - RMS dB). Lower is more chiptune.
    Score: 100 if crest <= 6dB (fully squashed), 0 if > 20dB (very dynamic).
    """
    samples_f = samples.astype(np.float64)
    rms = np.sqrt(np.mean(samples_f ** 2))
    peak = np.max(np.abs(samples_f))
    if rms == 0:
        return 0, 99.0
    crest_db = 20 * np.log10(peak / rms)

    if crest_db <= 6.0:
        score = 100
    elif crest_db >= 20.0:
        score = 0
    else:
        score = 100 * (1 - (crest_db - 6.0) / (20.0 - 6.0))
    return round(score, 1), round(crest_db, 2)


def validate(filepath):
    """Run all measurements and return a report dict."""
    sr, samples = load_as_wav_array(filepath)

    sr_score, sr_val = measure_sample_rate(sr)
    quant_score, unique_levels = measure_quantization(samples)
    hf_score, hf_pct = measure_hf_suppression(samples, sr)
    sat_score, sat_pct = measure_waveform_saturation(samples)
    dr_score, crest_db = measure_dynamic_range(samples)

    weights = {
        "sample_rate":    (sr_score,    0.25),
        "quantization":   (quant_score, 0.20),
        "hf_suppression": (hf_score,    0.25),
        "waveform_sat":   (sat_score,   0.20),
        "dynamic_range":  (dr_score,    0.10),
    }

    total = sum(s * w for s, w in weights.values())

    return {
        "file": filepath,
        "sample_rate_hz":       sr_val,
        "unique_amplitude_levels": unique_levels,
        "hf_energy_above_3500hz_pct": hf_pct,
        "waveform_saturation_pct":    sat_pct,
        "crest_factor_db":            crest_db,
        "scores": {
            "sample_rate":    sr_score,
            "quantization":   quant_score,
            "hf_suppression": hf_score,
            "waveform_sat":   sat_score,
            "dynamic_range":  dr_score,
        },
        "chiptune_score": round(total, 1),
    }


def print_report(report):
    score = report["chiptune_score"]
    if score >= 80:
        verdict = "✅ AUTHENTIC CHIPTUNE"
    elif score >= 55:
        verdict = "⚠️  CHIPTUNE-LIKE (passable)"
    else:
        verdict = "❌ NOT CHIPTUNE (sounds wrong)"

    print()
    print("=" * 52)
    print("  🎮 CHIPTUNE AUTHENTICITY REPORT")
    print("=" * 52)
    print(f"  File      : {os.path.basename(report['file'])}")
    print(f"  Verdict   : {verdict}")
    print(f"  SCORE     : {score}/100")
    print("-" * 52)
    print(f"  Sample Rate     : {report['sample_rate_hz']} Hz          [{report['scores']['sample_rate']}/100]")
    print(f"  Amplitude Levels: {report['unique_amplitude_levels']} unique         [{report['scores']['quantization']}/100]")
    print(f"  HF Energy >3.5k : {report['hf_energy_above_3500hz_pct']}%         [{report['scores']['hf_suppression']}/100]")
    print(f"  Waveform Sat.   : {report['waveform_saturation_pct']}% at peak     [{report['scores']['waveform_sat']}/100]")
    print(f"  Crest Factor    : {report['crest_factor_db']} dB          [{report['scores']['dynamic_range']}/100]")
    print("=" * 52)
    print()
    return score


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m bitify.validator <audio_file>")
        sys.exit(1)
    report = validate(sys.argv[1])
    score = print_report(report)
    sys.exit(0 if score >= 55 else 1)
