# ARCHITECTURE AUDIT & TECHNICAL ROADMAP
## Project: SAS (Smart Autonomous System) & AeroMouse Virtual Controller
**Platform:** Windows 10 / 11 | **Language:** Python 3.13 | **Date:** October 26, 2026

---

## 1. EXECUTIVE SUMMARY

An end-to-end technical audit was conducted on the SAS (Smart Autonomous System) codebase located at `C:\projects\GestureControlApp`. 
The repository currently implements a working proof-of-concept (MVP) combining:
1. **AeroMouse:** MediaPipe Tasks (`HandLandmarker`) + OpenCV touchless gesture controller with custom Hand Locking.
2. **SAS Agent:** Google Gemini (`gemini-3.5-flash-lite`) with Automatic Function Calling (AFC) executing Windows OS actions (applications, volume, web, emails).
3. **Voice Engine:** `sounddevice` + `wave` audio capture and Microsoft Edge-TTS neural speech output via Windows MCI.

While individual components are functional, they currently operate in decoupled silos (separate CLI process vs. System Tray process) without an event-driven core, lacking wake-word listening, screen context, confirmation security boundaries, and a unified HUD.

---

## 2. EXISTING ARCHITECTURE REVIEW

```
[System Tray (main_ui.py)] ──── spawns CLI ────> [CLI (sas_assistant.py)]
         │                                                │
    (threading)                                      (blocking I/O)
         ▼                                                ▼
[GestureWorker]                                   [SASBrain (Gemini)]
   ├── CameraManager (OpenCV)                        ├── Tools (email, system)
   ├── GestureEngine (MediaPipe)                     └── VoiceEngine (edge-tts)
   └── ActionController (pynput)
```

### Component Breakdown
| Module | Location | Primary Responsibilities | Current Implementation Mechanism |
| :--- | :--- | :--- | :--- |
| **System Tray UI** | `main_ui.py` | Windows Tray icon, background supervisor | `pystray`, `Pillow`, subprocess launcher |
| **Gesture Worker** | `core/gesture_worker.py` | Background loop for vision tracking | `threading.Thread`, polling loop with `time.sleep` |
| **Camera Manager** | `core/camera_manager.py` | Video capture & horizontal flip | `cv2.VideoCapture(0)` |
| **Gesture Engine** | `core/gesture_engine.py` | Hand landmark detection & gesture rules | `mediapipe.tasks.python.vision.HandLandmarker` |
| **Action Controller** | `core/action_controller.py`| Mouse coordinate mapping & smoothing | `pynput.mouse.Controller`, `pynput.keyboard` |
| **Agent Core** | `agent/brain.py` | LLM reasoning & tool routing | Google GenAI SDK (`gemini-3.5-flash-lite`), AFC |
| **Voice Engine** | `agent/voice_engine.py` | Speech recording & TTS output | `sounddevice`, `edge-tts`, `ctypes` (`mciSendStringW`) |
| **System Tools** | `agent/tools/` | Email, apps, volume, web search | `subprocess`, `webbrowser`, `ctypes`, `smtplib` |

---

## 3. CONFIRMED ARCHITECTURAL WEAKNESSES & EVIDENCE

### Issue 1: Process Disconnection (Zero Inter-Process Communication)
- **Evidence:** `main_ui.py` spawns `sas_assistant.py` via `subprocess.Popen("start cmd /k python sas_assistant.py", shell=True)`.
- **Impact:** The vision system and the voice/agent system exist in isolated memory spaces. A voice command like *"Pause hand gestures"* or a gesture like a wave cannot notify the conversational agent.

### Issue 2: Polling & Latency Bottlenecks in Vision Loop
- **Evidence:** `GestureWorker.run()` uses `time.sleep(0.01)` (Active) and `time.sleep(0.1)` (Sleeping) in `core/gesture_worker.py`. 
- **Impact:** Polling with arbitrary sleep leads to phase latency (missed webcam frames or processing stale buffers). MediaPipe is run in single synchronous image mode (`detector.detect(mp_image)`), blocking the camera loop on CPU.

### Issue 3: Hand-Locking Instability Under Fast Motion
- **Evidence:** `core/gesture_engine.py` checks `handedness = detection_result.handedness[idx][0].category_name`.
- **Impact:** MediaPipe occasionally flips handedness predictions (labeling a Right hand as Left) when the hand rotates or moves rapidly across the boundary, causing momentary dropped tracking or false locks.

### Issue 4: Blocking Audio Capture Without Voice Activity Detection (VAD)
- **Evidence:** `voice_engine.record_audio()` blocks for an unconditional 5 seconds (`sd.rec(int(duration_sec * self.sample_rate)) ... sd.wait()`).
- **Impact:** A 1-word command ("Volume up") requires a mandatory 5-second wait before Gemini begins processing. There is no streaming audio buffer or silence detection.

### Issue 5: Synchronous TTS Playback in Worker
- **Evidence:** `mciSendStringW(f'play {alias} wait', None, 0, None)` in `agent/voice_engine.py`.
- **Impact:** The `wait` flag freezes the calling thread until the entire audio clip finishes playing. While SAS speaks, user input cannot interrupt playback.

### Issue 6: Unprotected Tool Execution & Lack of Confirmation Policies
- **Evidence:** `agent/brain.py` registers raw Python functions into Gemini's tool list without schema boundary validation or confirmation prompts.
- **Impact:** High-impact actions (`lock_workstation`, arbitrary shell spawns, external email dispatch) execute autonomously on model hallucination without safety confirmation or idempotency checks.

---

## 4. RECOMMENDED TARGET ARCHITECTURE

The target architecture transitions SAS into a modular, **Event-Driven Multimodal Assistant** with clear separation of concerns:

```
                          ┌───────────────────────────┐
                          │   SAS Application Core    │
                          │   (Supervisor Lifecycle)  │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│  Perception Layer   │      │   Event Bus Core    │      │  Automation Layer   │
│ ├── Vision Worker   │◄────►│ ├── Typed Events    │◄────►│ ├── Action Executor │
│ ├── Audio / Wake    │      │ ├── Bounded Queues  │      │ ├── Safety Policy   │
│ └── Screen Context  │      │ └── Audit Logger    │      │ └── Tool Registry   │
└─────────────────────┘      └──────────┬──────────┘      └─────────────────────┘
                                        │
           ┌────────────────────────────┴────────────────────────────┐
           ▼                                                         ▼
┌─────────────────────┐                                   ┌─────────────────────┐
│     Agent Brain     │                                   │      HUD / UI       │
│ ├── Gemini 3.5 LLM  │                                   │ ├── Floating Widget │
│ ├── Tool Routing    │                                   │ ├── Status Feedback │
│ └── Memory Context  │                                   │ └── System Tray     │
└─────────────────────┘                                   └─────────────────────┘
```

### Key Architectural Pillars:
1. **Typed Event Bus (`core/event_bus.py`):**
   - Decoupled Publish/Subscribe pattern.
   - Bounded queues preventing high-frequency vision/audio backpressure.
   - Standardized event types: `VisionEvent`, `AudioEvent`, `AgentEvent`, `SystemEvent`.
2. **Dedicated Action Executor with Safety Policy (`security/policy_engine.py`):**
   - Read-only actions (time, status): Immediate execution.
   - Safe interactive actions (volume, launch app): Verified execution.
   - Consequential actions (send email, delete files, lock PC): Staged with visual/voice confirmation.
3. **Screen-Aware Intelligence Subsystem (`perception/screen_context.py`):**
   - Active window detection, UI Automation text retrieval, regional screen capture, and visual reasoning.
4. **Local Wake-Word & VAD Engine (`perception/audio_worker.py`):**
   - Real-time energy/silence VAD endpointing (ends recording when user finishes speaking).
   - Pluggable wake-word detector ("Hey SAS").
5. **Modern Transparent Desktop HUD (`hud/`):**
   - Built on Qt6 (`PyQt6`), transparent frameless window with glowing accents, live audio waveforms, gesture status, and action verification pills.

---

## 5. COMPATIBILITY & SYSTEM CONSTRAINTS

| Dependency | Verified Version | Environment Constraint |
| :--- | :--- | :--- |
| **Python** | `3.13.14 (x64)` | Windows 10/11 standard environment (`venv`). |
| **Google GenAI** | `google-genai 2.33.0` | Model `gemini-3.5-flash-lite` verified working with user API key. |
| **MediaPipe** | `mediapipe 0.10.35` | Tasks API HandLandmarker (`core/hand_landmarker.task`). |
| **GUI Framework** | `PyQt6 6.11.0` | Pre-installed and verified functional (`QtWidgets OK`). |
| **Audio I/O** | `sounddevice 0.5.6` | PortAudio bundled binaries functional for input. |
| **Speech Engine** | `edge-tts 7.3.1` | Neural speech generation verified functional. |

---

## 6. PRIORITIZED IMPLEMENTATION PLAN

- [x] **Phase 1: Repository Audit & Technical Baseline**
  - Complete code inspection, environment validation, and architectural audit (`docs/ARCHITECTURE_AUDIT.md`).
- [ ] **Phase 2: Event-Driven Core & Supervisor**
  - Implement `core/events.py` (Typed Event definitions).
  - Implement `core/event_bus.py` (Thread-safe, bounded publish-subscribe bus).
  - Implement `app/supervisor.py` (Unified application lifecycle manager).
- [ ] **Phase 3: AeroMouse Upgrades & Smoothing**
  - Implement adaptive landmark smoothing (One Euro Filter / dynamic alpha).
  - Enhance Hand Locking with spatial bounding box persistence.
  - Implement pointer dead zones and pinch hysteresis.
- [ ] **Phase 4: Audio Engine with VAD & Streaming**
  - Implement Energy/Silence Voice Activity Detection (VAD) to eliminate 5-second static delays.
  - Integrate interruptible non-blocking TTS audio player.
  - Implement offline wake-word detector pipeline.
- [ ] **Phase 5: Screen-Aware Perception Engine**
  - Implement `perception/screen_context.py` (Active window info, desktop screenshot capture, regional OCR).
  - Add screen-grounded tools to Gemini tool registry ("Summarize active screen", "Inspect error").
- [ ] **Phase 6: Secure Tool Registry & Policy Engine**
  - Refactor tools into `agent/tool_registry.py` with typed schemas, timeout safeguards, and permission levels.
  - Add execution outcome verification (confirming window opened, confirming volume changed).
- [ ] **Phase 7: Futuristic Transparent Desktop HUD**
  - Implement PyQt6 floating HUD widget (`hud/hud_window.py`) with sleek glassmorphism, telemetry, waveform visualization, and tray integration.
- [ ] **Phase 8: End-to-End Testing & Hardening**
  - Unit and integration tests for events, gestures, tool validation, and error recovery.
