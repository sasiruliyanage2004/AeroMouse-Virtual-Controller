# 🤖 SAS - Smart Autonomous System & AI Virtual Controller

**SAS** is a next-generation AI Desktop Assistant and Virtual Controller for Windows. It combines **touchless hand gesture control** with an **autonomous LLM Agent (powered by Google Gemini)** capable of controlling your entire PC through voice and natural language commands.

---

## 🌟 Core Features

### 1. 🧠 SAS Autonomous AI Desktop Agent
Talk or type to SAS in natural language. Powered by Google Gemini with **Automatic Tool Calling (Function Calling)**:
- **Email Automation:** Tell SAS *"Send an email to john@example.com about meeting updates"*, and it composes and sends/drafts the email automatically.
- **Application Launcher:** Open any app (*"Open Chrome"*, *"Open Notepad"*, *"Launch VS Code"*, *"Open Calculator"*).
- **Web & YouTube Control:** Search Google (*"Search for latest AI news"*) or play music directly (*"Play Shape of You on YouTube"*).
- **System Controls:** Adjust PC volume (*"Volume up"*, *"Mute"*), check date/time (*"What time is it?"*), lock workstation (*"Lock my PC"*).
- **Natural Voice Feedback:** SAS speaks back with high-fidelity, human-like AI voice using Microsoft Edge-TTS neural speech.

### 2. 🖐️ AeroMouse - Touchless Hand Gesture Controller
Control your PC mouse and windows without touching any hardware:
- **Move Cursor:** Point with your index finger.
- **Left Click:** Pinch your index finger and thumb together.
- **Scroll:** Point with index and middle fingers (V-shape) and move up/down.
- **Window Management:** Fist to Minimize, Open Palm to Maximize.
- **Smart Hand Locking:** Waking up locks onto that specific hand, completely ignoring other hands in frame.
- **Silent System Tray Mode:** Runs quietly in the Windows System Tray with status notifications.

---

## 🛠️ Tech Stack

- **AI Brain & Reasoner:** Google Gemini (`gemini-3.5-flash-lite` with Tool Calling)
- **Neural Voice Engine:** `edge-tts` (Microsoft Neural TTS) & `sounddevice`
- **Computer Vision:** Google MediaPipe Tasks API (Hand Landmarker) & OpenCV
- **OS Automation:** `pynput`, `subprocess`, `ctypes` (Native Windows API)
- **System Tray UI:** `pystray` & `Pillow`

---

## 🚀 Getting Started

### 1. Installation
Clone the repository and install requirements:
```bash
git clone https://github.com/sasiruliyanage2004/AeroMouse-Virtual-Controller.git
cd AeroMouse-Virtual-Controller
pip install -r requirements.txt
```

### 2. Setup Gemini API Key
Add your Gemini API Key in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run SAS Assistant
To interact with SAS directly via voice or text:
```bash
python sas_assistant.py
```
*Press `V` and Enter to record your voice for 5 seconds, or type any command.*

### 4. Run Full System (Gesture Mouse + Tray Icon + SAS)
```bash
python main_ui.py
```
*A tray icon will appear. Right-click it anytime to open SAS or exit.*
