import numpy as np
from scipy import signal


def apply_chiptune_filter(samples, sample_rate):
    """
    Pure DSP: transforms raw audio samples into authentic 8-bit chiptune sound.

    Stages:
      1. Normalize + tanh saturation  → square-wave character (NES pulse channels)
      2. Resonant low-pass filter      → retro handheld speaker roll-off (~5 kHz)
      3. 8-bit quantization            → 256 discrete amplitude levels
    """
    samples = samples.astype(np.float32)

    # 1. Normalize & saturate
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples /= max_val
    samples = np.tanh(samples * 6.0)
    samples = np.clip(samples, -1.0, 1.0)

    # 2. Low-pass filter (retro chip roll-off ~5 kHz)
    nyquist = sample_rate / 2
    cutoff = min(5000.0 / nyquist, 0.99)
    b, a = signal.butter(4, cutoff, btype='low', analog=False)
    samples = signal.lfilter(b, a, samples)

    # Re-normalize after filtering
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples /= max_val

    # 3. 8-bit quantization (scale to 16-bit storage for pydub)
    samples = np.round(samples * 127) * (32767 / 127)

    return samples.astype(np.int16)
