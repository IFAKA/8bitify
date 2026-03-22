"""
DSP-based 8-bit Chiptune Processor
===================================
Converts audio to authentic 8-bit by applying deterministic signal processing:
1. Low-pass filter (removes high frequencies)
2. Bit-crushing (8-bit quantization)
3. Saturation (crunchy tone)
4. Compression (dynamic glue)
5. Downsampling (8000 Hz for lo-fi aesthetic)

No AI synthesis, no re-generation — pure audio transformation.
"""

import os
import logging
import numpy as np
from pydub import AudioSegment
from scipy import signal


def apply_lowpass_filter(audio, cutoff_hz=4000, order=4):
    """
    Apply Butterworth low-pass filter to remove frequencies above cutoff.
    Preserves melody while removing high-frequency clutter.
    """
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    sr = audio.frame_rate

    # Normalize to -1..1
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = samples / max_val

    # Design and apply filter
    nyquist = sr / 2
    normalized_cutoff = cutoff_hz / nyquist
    normalized_cutoff = np.clip(normalized_cutoff, 0.001, 0.999)

    b, a = signal.butter(order, normalized_cutoff, btype='low')
    filtered = signal.filtfilt(b, a, samples)

    # Convert back to int16
    filtered = np.clip(filtered, -1.0, 1.0)
    filtered = (filtered * 32767).astype(np.int16)

    return audio._spawn(filtered.tobytes()).set_frame_rate(sr)


def apply_bitcrush(audio, bits=8):
    """
    Quantize audio to N-bit depth (e.g., 8-bit).
    Creates the classic "stair-step" 8-bit sound.
    """
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    sr = audio.frame_rate

    # Normalize
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = samples / max_val

    # Quantize to N bits
    levels = 2 ** bits
    quantized = np.round(samples * (levels / 2)) / (levels / 2)
    quantized = np.clip(quantized, -1.0, 1.0)

    # Back to int16
    quantized = (quantized * 32767).astype(np.int16)

    return audio._spawn(quantized.tobytes()).set_frame_rate(sr)


def apply_saturation(audio, gain=2.0, bias=0.0):
    """
    Apply soft saturation for warm, crunchy tone.
    Uses tanh() for smooth harmonic distortion.
    """
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    sr = audio.frame_rate

    # Normalize
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = samples / max_val

    # Apply gain then saturation
    saturated = np.tanh(samples * gain + bias)
    saturated = np.clip(saturated, -1.0, 1.0)

    # Back to int16
    saturated = (saturated * 32767).astype(np.int16)

    return audio._spawn(saturated.tobytes()).set_frame_rate(sr)


def apply_compression(audio, threshold=-20, ratio=4, attack_ms=5, release_ms=50):
    """
    Apply dynamic range compression.
    Brings up quiet parts, tames peaks → cohesive sound.
    """
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    sr = audio.frame_rate

    # Normalize
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = samples / max_val

    # Convert threshold from dB to linear
    threshold_linear = 10 ** (threshold / 20.0)

    # Compute envelope (RMS in small windows)
    window_size = int(sr * 0.01)  # 10ms windows
    envelope = np.zeros_like(samples)

    for i in range(0, len(samples), window_size):
        chunk = samples[i:i+window_size]
        rms = np.sqrt(np.mean(chunk ** 2))
        envelope[i:i+window_size] = rms

    # Smooth envelope with attack/release
    attack_samples = int(sr * attack_ms / 1000)
    release_samples = int(sr * release_ms / 1000)

    smoothed = np.zeros_like(envelope)
    smoothed[0] = envelope[0]
    for i in range(1, len(envelope)):
        if envelope[i] > smoothed[i-1]:
            # Attack
            alpha = 1.0 / max(attack_samples, 1)
        else:
            # Release
            alpha = 1.0 / max(release_samples, 1)
        smoothed[i] = alpha * envelope[i] + (1 - alpha) * smoothed[i-1]

    # Apply compression curve
    gain_reduction = np.ones_like(smoothed)
    above_threshold = smoothed > threshold_linear
    gain_reduction[above_threshold] = (
        threshold_linear + (smoothed[above_threshold] - threshold_linear) / ratio
    ) / smoothed[above_threshold]

    # Prevent division by zero
    gain_reduction[smoothed == 0] = 1.0

    # Apply gain reduction
    compressed = samples * gain_reduction
    compressed = np.clip(compressed, -1.0, 1.0)

    # Back to int16
    compressed = (compressed * 32767).astype(np.int16)

    return audio._spawn(compressed.tobytes()).set_frame_rate(sr)


def process_audio_dsp(input_path, output_path=None):
    """
    Main DSP processor: load → filter → bitcrush → saturate → compress → downsample → export.

    Returns: output file path
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_8bit.mp3"

    try:
        # Load
        logging.info(f"Loading {input_path}...")
        audio = AudioSegment.from_file(input_path)

        # Step 1: Low-pass filter (preserve melody, remove clutter)
        logging.info("Applying low-pass filter (4000 Hz)...")
        audio = apply_lowpass_filter(audio, cutoff_hz=4000, order=4)

        # Step 2: Bit-crush (8-bit quantization)
        logging.info("Applying 8-bit quantization...")
        audio = apply_bitcrush(audio, bits=8)

        # Step 3: Saturation (warm, crunchy tone)
        logging.info("Applying saturation...")
        audio = apply_saturation(audio, gain=2.0, bias=0.0)

        # Step 4: Compression (glue)
        logging.info("Applying compression...")
        audio = apply_compression(audio, threshold=-20, ratio=4)

        # Step 5: Downsample to 8000 Hz
        logging.info("Downsampling to 8000 Hz...")
        audio = audio.set_frame_rate(8000)

        # Export
        logging.info(f"Exporting to {output_path}...")
        audio.export(output_path, format="mp3", bitrate="64k")

        return output_path

    except Exception as e:
        logging.error(f"DSP processing failed: {e}")
        raise
