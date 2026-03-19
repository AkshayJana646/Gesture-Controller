import threading
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from core.config import Config
from core.gesture_classifier import GestureClassifier, GestureResult
from core.action_handler import ActionHandler


class GestureDetector:

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._stop = threading.Event()
        self._thread = None

        self.running = False
        self.last_gesture = "—"
        self.last_action = "—"
        self.fps = 0.0
        self.frame = None
        self._lock = threading.Lock()

        # Components
        self._classifier = GestureClassifier(cfg)
        self._action = ActionHandler(cfg)
        self._hands = self._build_hands()

        # Stability state
        self._prev_gesture = None
        self._gesture_frames = 0
        self._last_triggered = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="GestureDetector")
        self._thread.start()
        self.running = True

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        self.running = False
        self._action.reset()

    def _loop(self):
        cap = cv2.VideoCapture(self.cfg.CAMERA_INDEX)
        if not cap.isOpened():
            print("Cannot access webcam")
            self.running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.FRAME_HEIGHT)

        print("Webcam is running. Press 'q' to quit.")

        prev_time = time.monotonic()

        try:
            while not self._stop.is_set():
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    time.sleep(0.01)
                    continue

                # Convert to RGB for MediaPipe
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_rgb.flags.writeable = False
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                results = self._hands.detect(mp_img)

                # Classify gesture from first detected hand
                raw_result = GestureResult(name=None)
                if results.hand_landmarks:
                    raw_result = self._classifier.classify(results.hand_landmarks[0])

                # Stability check
                confirmed = self._stabilise(raw_result)

                # Trigger action if gesture confirmed
                if confirmed:
                    action_desc = self._action.handle(confirmed)
                    if action_desc:
                        with self._lock:
                            self.last_action = action_desc

                # Draw landmarks and skeleton
                if results.hand_landmarks:
                    frame = self._draw(frame, results)

                # FPS counter
                now = time.monotonic()
                self.fps = 1.0 / max(now - prev_time, 1e-6)
                prev_time = now

                # Overlay gesture name, action, FPS
                frame = self._draw_hud(frame)

                with self._lock:
                    self.frame = frame.copy()

        finally:
            cap.release()
            self.running = False

    def _stabilise(self, result: GestureResult):
        name = result.name

        if name == self._prev_gesture:
            self._gesture_frames += 1
        else:
            self._gesture_frames = 1
            self._prev_gesture = name

        with self._lock:
            self.last_gesture = name or "—"

        # Reset trigger when gesture disappears
        if name is None:
            self._last_triggered = None
            return None

        # Confirm only after holding for required frames
        if self._gesture_frames >= self.cfg.REQUIRED_FRAMES and name != self._last_triggered:
            self._last_triggered = name
            return result

        return None

    def _draw(self, frame, results):
        h, w = frame.shape[:2]

        for hand_landmarks in results.hand_landmarks:

            # Draw skeleton
            for conn in self.cfg.HAND_CONNECTIONS:
                p0 = hand_landmarks[conn[0]]
                p1 = hand_landmarks[conn[1]]
                cv2.line(frame,
                    (int(p0.x * w), int(p0.y * h)),
                    (int(p1.x * w), int(p1.y * h)),
                    self.cfg.SKELETON_COLOR, 2)

            # Draw landmarks
            for i, lm in enumerate(hand_landmarks):
                cx, cy = int(lm.x * w), int(lm.y * h)
                radius = 8 if i == 0 else 4
                cv2.circle(frame, (cx, cy), radius, self.cfg.LANDMARK_COLOR, cv2.FILLED)

        return frame

    def _draw_hud(self, frame):
        with self._lock:
            gesture = self.last_gesture
            action = self.last_action

        # Gesture name top left
        cv2.putText(frame, gesture, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    self.cfg.GESTURE_TEXT_COLOR, 2)

        # Last action below gesture
        cv2.putText(frame, f"Action: {action}",
                    (16, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (200, 200, 200), 1)

        # FPS top right
        cv2.putText(frame, f"{int(self.fps)} FPS",
                    (frame.shape[1] - 90, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    (180, 180, 180), 1)

        return frame

    def _build_hands(self):
        base_options = python.BaseOptions(model_asset_path=self.cfg.MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.cfg.NUM_HANDS,
            min_hand_detection_confidence=self.cfg.MIN_DETECTION_CONFIDENCE,
            running_mode=vision.RunningMode.IMAGE,
        )
        return vision.HandLandmarker.create_from_options(options)