import sys
import os
import threading
from PyQt6 import QtWidgets, QtCore
from app.supervisor import SASSupervisor
from hud.hud_window import SASHUDWindow

def cli_input_thread(supervisor: SASSupervisor, app: QtWidgets.QApplication):
    """Allows typing commands or typing 'v' in terminal alongside the HUD."""
    print("\n" + "="*60)
    print("      🤖 SAS (SMART AUTONOMOUS SYSTEM) — ACTIVE HUD MODE")
    print("="*60)
    print(" • Type 'v' or 'voice' to speak (VAD auto-detects speech end).")
    print(" • Or type any text command (e.g. 'what time is it', 'open chrome').")
    print(" • Or use touchless gestures (Thumbs Up to wake AeroMouse).")
    print(" • Type 'exit' to quit.")
    print("="*60 + "\n")

    while supervisor._running:
        try:
            cmd = input("SAS-Console > ").strip()
            if not cmd:
                continue

            if cmd.lower() in ["exit", "quit", "q"]:
                supervisor.stop()
                QtCore.QMetaObject.invokeMethod(app, "quit", QtCore.Qt.ConnectionType.QueuedConnection)
                break
            elif cmd.lower() in ["v", "voice"]:
                supervisor.listen_and_process()
            else:
                supervisor.execute_text_command(cmd)
        except (EOFError, KeyboardInterrupt):
            supervisor.stop()
            QtCore.QMetaObject.invokeMethod(app, "quit", QtCore.Qt.ConnectionType.QueuedConnection)
            break

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("SAS Smart Autonomous System")
    
    # Initialize unified supervisor
    supervisor = SASSupervisor(enable_gestures=True)
    supervisor.start()

    # Create & display the transparent floating HUD
    hud = SASHUDWindow(bus=supervisor.bus)
    hud.show()

    # Start CLI input loop in background thread
    threading.Thread(
        target=cli_input_thread,
        args=(supervisor, app),
        daemon=True
    ).start()

    # Execute Qt event loop
    exit_code = app.exec()
    supervisor.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
