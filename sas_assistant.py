import os
import sys
import threading
from agent.brain import SASBrain
from agent.voice_engine import VoiceEngine

def banner():
    print("\n" + "="*60)
    print("      🤖 SAS - Smart Autonomous System (AI Desktop Agent)")
    print("="*60)
    print(" Commands you can try:")
    print("  • 'Send an email to user@test.com saying hello'")
    print("  • 'Open Chrome' / 'Open Notepad' / 'Open Calculator'")
    print("  • 'Play Shape of You on YouTube'")
    print("  • 'Search Google for latest technology news'")
    print("  • 'Increase volume' / 'Mute volume'")
    print("  • 'What time is it right now?'")
    print("  • 'Lock my computer'")
    print("-" * 60)
    print(" Options:")
    print("  • Type your command and press ENTER.")
    print("  • Type 'voice' or 'v' then ENTER to speak into your microphone.")
    print("  • Type 'exit' to quit.")
    print("="*60 + "\n")

def main():
    try:
        brain = SASBrain()
        voice = VoiceEngine()
    except Exception as e:
        print(f"Initialization error: {e}")
        return

    banner()
    voice.speak("Greetings! SAS is online and ready to assist you.")

    while True:
        try:
            user_input = input("User > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q']:
                voice.speak("Goodbye! Shutting down SAS.")
                print("SAS terminated.")
                break

            # Voice command mode
            if user_input.lower() in ['v', 'voice']:
                print("\n🎤 Recording from microphone for 5 seconds... Speak now!")
                wav_file = voice.record_audio(duration_sec=5)
                if not wav_file:
                    print("Could not record audio.")
                    continue
                    
                print("🧠 Transcribing your voice with Gemini...")
                transcribed_text = brain.transcribe_audio(wav_file)
                
                # Cleanup temp file
                if os.path.exists(wav_file):
                    try: os.remove(wav_file)
                    except: pass
                    
                if not transcribed_text:
                    print("Could not understand audio. Please try again.")
                    voice.speak("Sorry, I could not understand what you said.")
                    continue
                    
                print(f"Heard: '{transcribed_text}'")
                user_input = transcribed_text

            # Execute via SAS Brain
            reply = brain.process_command(user_input)
            print(f"\nSAS > {reply}\n")
            
            # Speak reply in background so user doesn't wait
            threading.Thread(target=voice.speak, args=(reply,), daemon=True).start()

        except KeyboardInterrupt:
            print("\nExiting SAS...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
