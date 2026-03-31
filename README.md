# ✋ Gesture Controller

Control your computer using **hand gestures through your webcam** — no keyboard or mouse required.

![Python](https://img.shields.io/badge/Python-3.10+-blue)  
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-green)  
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange)

---

## Overview

Gesture Controller is a real-time computer vision application that detects hand gestures and maps them to system actions like controlling music playback and volume.

It uses **MediaPipe for hand tracking**, **OpenCV for webcam processing**, and **PyAutoGUI for system control**.

---

## Gestures

| Gesture | Action |
|--------|--------|
| ✊ Fist | Play / Pause |
| ✋ Open Hand | Mute |
| 👍 Thumbs Up | Volume Up |
| 👎 Thumbs Down | Volume Down |
| ✌️ Peace | Next Track |
| ☝️ Point | Previous Track |

---

## Features

- Real-time hand tracking (~30 FPS)
- Gesture stability filtering
- Per-gesture cooldown to prevent repeated triggers
- Optional fullscreen GUI with live camera feed
- Headless mode support

---

## Tech Stack

- **Python**
- **MediaPipe**
- **OpenCV**
- **PyAutoGUI**
- **Tkinter**

---

## Project Structure

```
Gesture-Controller/
│
├── main.py
├── requirements.txt
├── hand_landmarker.task
│
├── core/
│   ├── config.py
│   ├── detector.py
│   ├── gesture_classifier.py
│   └── action_handler.py
│
└── gui/
    └── app.py
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/AkshayJana646/Gesture-Controller.git
cd Gesture-Controller
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**
```bash
venv\Scripts\activate
```

**Mac/Linux**
```bash
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Download the MediaPipe model

```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task" -OutFile "hand_landmarker.task"
```

---

### 5. Run the application

GUI mode:

```bash
python main.py
```

Headless mode:

```bash
python main.py --headless
```

---

## Configuration

Settings can be modified in `core/config.py`.

| Setting | Description |
|-------|-------------|
| `CAMERA_INDEX` | Webcam device index |
| `COOLDOWN_SECONDS` | Time between repeated gesture actions |
| `REQUIRED_FRAMES` | Frames needed to confirm a gesture |
| `FINGER_THRESHOLD` | Finger detection sensitivity |
