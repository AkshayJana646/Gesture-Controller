from dataclasses import dataclass, field


@dataclass
class Config:

    # Camera
    CAMERA_INDEX: int = 0
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480

    # MediaPipe model
    MODEL_PATH: str = "hand_landmarker.task"
    NUM_HANDS: int = 2
    MIN_DETECTION_CONFIDENCE: float = 0.6

    # Gesture stability
    REQUIRED_FRAMES: int = 6

    # Cooldown
    COOLDOWN_SECONDS: float = 0.3

    # Gesture thresholds
    FINGER_THRESHOLD: float = 0.02
    CLOSED_FINGERS_MIN: int = 3
    OPEN_FINGERS_MIN: int = 3
    VOLUME_SENSITIVITY: int = 15

    # Display
    WINDOW_TITLE: str = "Gesture Controller"
    LANDMARK_COLOR: tuple = (255, 180, 0)
    SKELETON_COLOR: tuple = (0, 220, 90)
    GESTURE_TEXT_COLOR: tuple = (0, 60, 255)

    # Hand skeleton connections
    HAND_CONNECTIONS: list = field(default_factory=lambda: [
        [0, 1], [1, 2], [2, 3], [3, 4],
        [0, 5], [5, 6], [6, 7], [7, 8],
        [0, 9], [9, 10], [10, 11], [11, 12],
        [0, 13], [13, 14], [14, 15], [15, 16],
        [0, 17], [17, 18], [18, 19], [19, 20],
        [5, 9], [9, 13], [13, 17],
    ])