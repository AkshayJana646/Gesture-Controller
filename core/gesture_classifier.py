from dataclasses import dataclass
from core.config import Config

FINGER_TIPS = [8, 12, 16, 20]
FINGER_PIPS = [6, 10, 14, 18]
FINGER_MCPS = [5,  9, 13, 17]


@dataclass
class GestureResult:
    name: str | None
    pinch_y: float | None = None


class GestureClassifier:

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def classify(self, landmarks) -> GestureResult:
        lm = landmarks
        fingers = self._extended_fingers(lm)
        n_open = sum(fingers)
        thumb_up = self._thumb_up(lm)
        thumb_down = self._thumb_down(lm)

        # Thumbs up — thumb up, all fingers curled
        if thumb_up and n_open == 0:
            return GestureResult(name="Thumbs Up")

        # Thumbs down — thumb down, all fingers curled
        if thumb_down and n_open == 0:
            return GestureResult(name="Thumbs Down")

        # Open hand — most fingers extended
        if n_open >= self.cfg.OPEN_FINGERS_MIN:
            return GestureResult(name="Open Hand")

        # Fist — most fingers curled
        fingers_closed = self._closed_count(lm)
        if fingers_closed >= self.cfg.CLOSED_FINGERS_MIN:
            return GestureResult(name="Fist")

        # Peace sign — index and middle up, ring and pinky down
        if fingers == [True, True, False, False]:
            return GestureResult(name="Peace")

        # Point — only index finger up
        if fingers == [True, False, False, False]:
            return GestureResult(name="Point")

        return GestureResult(name=None)

    def _extended_fingers(self, lm) -> list[bool]:
        t = self.cfg.FINGER_THRESHOLD
        return [
            lm[tip].y < lm[pip].y - t
            for tip, pip in zip(FINGER_TIPS, FINGER_PIPS)
        ]

    def _closed_count(self, lm) -> int:
        t = self.cfg.FINGER_THRESHOLD
        return sum(
            lm[tip].y > lm[mcp].y + t
            for tip, mcp in zip(FINGER_TIPS, FINGER_MCPS)
        )

    def _thumb_up(self, lm) -> bool:
        return lm[4].y < lm[2].y - 0.06

    def _thumb_down(self, lm) -> bool:
        return lm[4].y > lm[2].y + 0.06