import numpy as np
from pydub import AudioSegment
from .converter import apply_chiptune_filter

def process_stem(filepath, stem_type):
    audio = AudioSegment.from_file(filepath)
    sample_rate = 8000
    audio = audio.set_frame_rate(sample_rate).set_channels(1)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples /= max_val

    if stem_type == "drums":
        samples = np.sign(samples) * np.abs(samples)**0.5
        samples = np.round(samples * 15) * (32767 / 15)
        samples = samples.astype(np.int16)
    elif stem_type == "bass":
        samples = np.tanh(samples * 3.0) 
        samples = np.round(samples * 31) * (32767 / 31)
        samples = samples.astype(np.int16)
    elif stem_type == "other":
        samples = apply_chiptune_filter(samples, sample_rate)
    elif stem_type == "vocals":
        samples = np.zeros_like(samples).astype(np.int16)
        
    return audio._spawn(samples.tobytes()).set_frame_rate(sample_rate)
