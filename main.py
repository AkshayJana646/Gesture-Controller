import argparse
import cv2

from core.config import Config
from core.detector import GestureDetector


def run_gui():
    from gui.app import GestureApp
    app = GestureApp()
    app.mainloop()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gesture Controller")
    parser.add_argument("--headless", action="store_true",
                        help="Run without the Tkinter GUI")
    args = parser.parse_args()

    run_gui()
