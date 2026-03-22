# Bitify package
import sys

try:
    import audioop
except ImportError:
    try:
        import audioop_lts
        sys.modules['audioop'] = audioop_lts
        sys.modules['pyaudioop'] = audioop_lts
    except ImportError:
        pass
