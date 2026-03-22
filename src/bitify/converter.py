import os
import numpy as np
from pydub import AudioSegment
from scipy.io import wavfile
from scipy import signal

def apply_chiptune_filter(samples, sample_rate):
    """
    Applies DSP techniques to make audio sound like a retro game console.
    """
    # 1. Normalize and Squash (Compression)
    # We want to push the signal toward the limits to simulate square-ish waves
    samples = samples.astype(np.float32)
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples /= max_val
    
    # Apply a hard clipper/sigmoid to 'square' the waves
    # This adds harmonic distortion characteristic of 8-bit chips
    samples = np.tanh(samples * 1.5) 
    
    # 2. Resonant Low-Pass Filter (The 'Handheld Speaker' effect)
    # Most retro chips cut off around 4kHz-6kHz
    nyquist = sample_rate / 2
    cutoff = 5000 / nyquist
    b, a = signal.butter(4, cutoff, btype='low', analog=False)
    samples = signal.lfilter(b, a, samples)

    # 3. Quantization (8-bit)
    # We map the -1.0 to 1.0 range to 256 discrete levels
    # Then we map it back to 16-bit integers for pydub
    samples = np.round(samples * 127) # 8-bit signed range (-127 to 127)
    samples = samples * (32767 / 127) # Scale back to 16-bit range
    
    return samples.astype(np.int16)

def convert_to_8bit(input_path, output_path=None, bitrate="8k"):
    """
    Converts an audio file to an 8-bit chiptune style.
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_8bit.mp3"

    # Load audio
    try:
        audio = AudioSegment.from_file(input_path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

    # 1. Downsample (Low-Fi effect)
    target_sample_rate = 8000 
    audio = audio.set_frame_rate(target_sample_rate)
    audio = audio.set_channels(1)

    # 2. Extract samples and apply the Chiptune DSP pipeline
    samples = np.array(audio.get_array_of_samples())
    processed_samples = apply_chiptune_filter(samples, target_sample_rate)
    
    # 3. Rebuild AudioSegment
    new_audio = audio._spawn(processed_samples.tobytes())
    new_audio = new_audio.set_frame_rate(target_sample_rate)

    # 4. Final Polish
    # Boosting volume a bit can help with the 'crunch' perception
    new_audio = new_audio + 6 
    
    print(f"Exporting to {output_path}...")
    new_audio.export(output_path, format="mp3", bitrate="64k")
    
    return output_path
