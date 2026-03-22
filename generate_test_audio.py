import sys
try:
    import audioop_lts
    sys.modules['audioop'] = audioop_lts
    sys.modules['pyaudioop'] = audioop_lts
except ImportError:
    pass

from pydub import AudioSegment
from pydub.generators import Sine
import os

def create_test_audio(filename="test_audio.mp3"):
    # Create a simple melody
    tone1 = Sine(440).to_audio_segment(duration=500)
    tone2 = Sine(550).to_audio_segment(duration=500)
    tone3 = Sine(660).to_audio_segment(duration=500)
    
    audio = tone1 + tone2 + tone3
    
    print(f"Generating {filename}...")
    audio.export(filename, format="mp3")

if __name__ == "__main__":
    create_test_audio()
