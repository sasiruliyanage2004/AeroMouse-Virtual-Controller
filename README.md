# 🖐️ AeroMouse - AI Virtual Mouse & Gesture Controller

AeroMouse is a lightweight, background-running Windows desktop application that allows you to control your PC entirely through hand gestures using your webcam. Built with Python, OpenCV, and Google's MediaPipe Tasks API, it provides a seamless touchless experience.

## ✨ Features

- **Background Execution:** Runs silently in the Windows System Tray without annoying terminal windows.
- **Wake/Sleep State Machine:** Put the app to sleep and wake it up using a simple "Thumbs Up" gesture to save CPU and prevent accidental clicks.
- **Smart Gesture Recognition:**
  - **Move Cursor:** Point with your index finger.
  - **Left Click:** Pinch your index finger and thumb together.
  - **Scroll:** Point with both index and middle fingers (V-shape) and move up/down.
  - **Minimize Active Window:** Make a fist.
  - **Maximize Window:** Show an open hand (all fingers extended).

## 🛠️ Tech Stack

- **Python 3.10+**
- **MediaPipe Tasks API** (Hand Landmarker)
- **OpenCV** (Camera handling)
- **pynput** (Mouse & Keyboard automation)
- **pystray & Pillow** (System Tray UI)

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/AeroMouse.git
   cd AeroMouse
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the MediaPipe Model:**
   Download the `hand_landmarker.task` file from Google and place it inside the `core/` directory. (If it is not already there).

5. **Run the App:**
   ```bash
   python main_ui.py
   ```
   *The app will start in the background and a blue icon will appear in your system tray.*

## 🎮 Usage Guide

1. When you start the app, it is initially in **SLEEP** mode.
2. Show a **Thumbs Up** 👍 to the camera for 2 seconds to **WAKE** the app. A Windows notification will confirm it is Active.
3. Control your PC using the gestures listed in the Features section.
4. Show a **Thumbs Up** 👍 again for 2 seconds to put the app back to **SLEEP**.
5. To exit, right-click the system tray icon and click "Exit".
