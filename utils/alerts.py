"""Alert utilities for audio notifications."""
import threading

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    print(" playsound module not available. Audio alerts disabled.")
    PLAYSOUND_AVAILABLE = False
    playsound = None


def play_alert(file_path: str):
    """Play alert sound in a separate thread (non-blocking)."""
    if not PLAYSOUND_AVAILABLE or not playsound:
        print(f" Alert disabled (would play: {file_path})")
        return
    
    try:
        threading.Thread(target=playsound, args=(file_path,), daemon=True).start()
        print(f" Playing alert: {file_path}")
    except Exception as e:
        print(f" Failed to play alert {file_path}: {e}")


def play_pii_alert(file_path: str):
    """Play PII detection alert."""
    play_alert(file_path)


def play_policy_alert(file_path: str):
    """Play policy violation alert."""
    play_alert(file_path)
