import time
import pyautogui
from core.config import Config
from core.gesture_classifier import GestureResult


pyautogui.FAILSAFE = False


# Gesture to key mapping
KEYMAP = {
    "Fist":        "space",       # Play / Pause
    "Open Hand":   "m",           # Mute toggle
    "Thumbs Up":   "volumeup",    # Volume up
    "Thumbs Down": "volumedown",  # Volume down
    "Peace":       "nexttrack",   # Next track
    "Point":       "prevtrack",   # Previous track
}


class ActionHandler:

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._last_fired = {}

    def handle(self, result: GestureResult):
        if result.name is None:
            return None
        return self._fire_key(result.name)

    def reset(self):
        self._last_fired = {}

    def _fire_key(self, gesture_name: str):
        key = KEYMAP.get(gesture_name)
        if key is None:
            return None

        now = time.monotonic()
        last = self._last_fired.get(gesture_name, 0.0)

        # Skip if still in cooldown window
        if now - last < self.cfg.COOLDOWN_SECONDS:
            return None

        self._last_fired[gesture_name] = now
        pyautogui.press(key)
        print(f"{gesture_name.upper()} TRIGGERED -> {key}")
        return f"{gesture_name} -> {key}"