import os
import numpy as np
from pydub import AudioSegment
from scipy.io import wavfile

def convert_to_8bit(input_path, output_path=None, bitrate="8k"):
    """
    Converts an audio file to an 8-bit chiptune style.
    
    Args:
        input_path (str): Path to input file.
        output_path (str): Path to save output. If None, appends '_8bit'.
        bitrate (str): Target sample rate for the 'lo-fi' effect (e.g., '8000', '11025').
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
    # 8000Hz is very 'phone' or 'gameboy' like. 
    # 11025Hz is a bit better but still retro.
    target_sample_rate = 8000 
    
    # We use set_frame_rate which handles resampling. 
    # To get a grittier sound, we could just drop samples, but this is safer.
    audio = audio.set_frame_rate(target_sample_rate)
    
    # 2. Convert to Mono (Gameboys were often mono or limited stereo)
    audio = audio.set_channels(1)

    # 3. Bitcrush (Quantization)
    # Get raw samples as numpy array
    # pydub samples are usually 16-bit ints (signed)
    samples = np.array(audio.get_array_of_samples())
    
    # Reduce bit depth to 8-bit
    # 16-bit range is -32768 to 32767. 
    # 8-bit range is 256 values.
    # Factor to reduce 16-bit to 8-bit resolution: 256
    # We integer divide by 256 to drop the lower bits, then multiply back 
    # to scale it up to 16-bit volume levels (but with 8-bit steps).
    
    quantization_factor = 256 
    
    # Standard bitcrush:
    # (sample // factor) * factor
    # This 'steps' the audio.
    
    quantized_samples = (samples // quantization_factor) * quantization_factor
    
    # Create new AudioSegment from the processed samples
    # We need to ensure the data type is correct (int16)
    new_audio = audio._spawn(quantized_samples.astype(np.int16).tobytes())
    new_audio = new_audio.set_frame_rate(target_sample_rate)

    # 4. Export
    # Boosting volume a bit can help with the 'crunch' perception
    new_audio = new_audio + 3 
    
    print(f"Exporting to {output_path}...")
    new_audio.export(output_path, format="mp3", bitrate="64k") # Low bitrate mp3 for extra artifacts? Maybe standard 128k.
    
    return output_path
