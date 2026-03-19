import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import pyautogui


# Path to the hand landmarker model
MODEL_PATH = "hand_landmarker.task"


# Hand connections
HAND_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 5], [5, 6], [6, 7], [7, 8],
    [0, 9], [9, 10], [10, 11], [11, 12],
    [0, 13], [13, 14], [14, 15], [15, 16],
    [0, 17], [17, 18], [18, 19], [19, 20],
    [5, 9], [9, 13], [13, 17]
]


# Gesture Control Settings
last_action_time = 0
cooldown = 1

gesture = None
prev_gesture = None
gesture_frames = 0
required_frames = 5   # stability threshold

last_triggered_gesture = None  # prevents spam


# Initialize MediaPipe
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    running_mode=vision.RunningMode.IMAGE
)

hands = vision.HandLandmarker.create_from_options(options)


# Webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot access webcam")
    exit()

cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)

print("Webcam is running. Press 'q' to quit.")


while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

    results = hands.detect(mp_image)

    gesture = None  # reset every frame

    if results.hand_landmarks:
        h, w, c = frame.shape

        for hand_landmarks in results.hand_landmarks:

            # Draw landmarks
            for id, lm in enumerate(hand_landmarks):
                cx = int(lm.x * w)
                cy = int(lm.y * h)

                if id == 0:
                    cv2.circle(frame, (cx, cy), 10, (255, 0, 0), cv2.FILLED)

            # Draw skeleton
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection

                x0, y0 = int(hand_landmarks[start_idx].x * w), int(hand_landmarks[start_idx].y * h)
                x1, y1 = int(hand_landmarks[end_idx].x * w), int(hand_landmarks[end_idx].y * h)

                cv2.line(frame, (x0, y0), (x1, y1), (0, 255, 0), 2)


            # Gesture Detection (LESS STRICT)

            threshold = 0.015   # smaller threshold = easier detection

            tips = [8, 12, 16, 20]
            knuckles = [5, 9, 13, 17]

            fingers_closed = sum(
                hand_landmarks[t].y > hand_landmarks[k].y + threshold
                for t, k in zip(tips, knuckles)
            )

            fingers_open = sum(
                hand_landmarks[t].y < hand_landmarks[k].y - threshold
                for t, k in zip(tips, knuckles)
            )

            # FINAL LOGIC (LESS STRICT)
            if fingers_closed >= 2:
                gesture = "Fist"

            elif fingers_open >= 3:
                gesture = "Open Hand"


    # Stability Check

    if gesture == prev_gesture:
        gesture_frames += 1
    else:
        gesture_frames = 0

    prev_gesture = gesture

    # Reset trigger when gesture disappears
    if gesture is None:
        last_triggered_gesture = None


    # Trigger Actions

    current_time = time.time()

    if (
        gesture and
        gesture_frames > required_frames and
        gesture != last_triggered_gesture and
        current_time - last_action_time > cooldown
    ):
        if gesture == "Fist":
            pyautogui.press("space")  # Play/Pause
            print("FIST TRIGGERED")

        elif gesture == "Open Hand":
            pyautogui.press("m")      # Mute/Unmute
            print("OPEN HAND TRIGGERED")

        last_action_time = current_time
        last_triggered_gesture = gesture


    # Display Gesture

    if gesture:
        cv2.putText(frame, gesture, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 255), 2)

    # Show frame
    cv2.imshow("Hand Tracking", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
