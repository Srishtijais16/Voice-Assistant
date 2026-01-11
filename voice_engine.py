import speech_recognition as sr
import pyttsx3
import threading
import time
import pythoncom  # Critical for Windows COM threading

is_speaking = False
current_engine = None  # Global reference to stop the active engine

def speak(text, on_word_callback=None):
    """
    Speaks text in a dedicated thread.
    Synchronizes text display with audio using the 'started-word' event.
    """
    global is_speaking
    if not text or text.strip() == "":
        return
    
    def run_speech():
        global is_speaking, current_engine
        # Initialize COM for the new thread (Required for Windows/SAPI5)
        pythoncom.CoInitialize()
        try:
            is_speaking = True
            # Force re-initialization inside the thread for the correct audio context
            current_engine = pyttsx3.init('sapi5')
            
            # Explicitly set properties to ensure audio is audible
            current_engine.setProperty('rate', 170)
            current_engine.setProperty('volume', 1.0) # Max volume
            
            if on_word_callback:
                def on_word(name, location, length):
                    # Check if we should stop speaking midway
                    if not is_speaking:
                        current_engine.stop()
                        return
                    
                    # Extract the word based on the character location in the string
                    word = text[location:location+length]
                    on_word_callback(word)
                
                # Connect the sync event
                cb_id = current_engine.connect('started-word', on_word)
                current_engine.say(text)
                current_engine.runAndWait()
                current_engine.disconnect(cb_id)
            else:
                current_engine.say(text)
                current_engine.runAndWait()
                
        except Exception as e:
            print(f"Speech Engine Error: {e}")
        finally:
            is_speaking = False
            current_engine = None  # Clear reference after speaking
            pythoncom.CoUninitialize()

    # Daemon thread ensures the voice engine doesn't block the app from closing
    t = threading.Thread(target=run_speech, daemon=True)
    t.start()

def stop_speaking():
    """Immediately kills any active speech."""
    global current_engine, is_speaking
    # Set the flag first so the callback can catch it even if .stop() is slow
    is_speaking = False
    if current_engine:
        try:
            # Signaling the engine to stop its current loop
            current_engine.stop()
            print("Jarvis: Speech interrupted.")
        except Exception as e:
            print(f"Error while stopping speech: {e}")

def get_active_mic_index():
    """Identifies the best available input device, avoiding output-only devices."""
    try:
        mics = sr.Microphone.list_microphone_names()
        # Step 1: Specifically look for "Microphone" or "Headset"
        for i, name in enumerate(mics):
            lower_name = name.lower()
            if "mic" in lower_name or "headset" in lower_name:
                print(f"System: Found Input Device -> {name}")
                return i
        
        # Step 2: Fallback to any external device
        for i, name in enumerate(mics):
            if "bluetooth" in name.lower() or "usb" in name.lower():
                return i
    except Exception as e:
        print(f"Hardware Scan Error: {e}")
    
    return None # Default system mic

def listen():
    """Listens for voice with an intelligent fallback mechanism."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    # Start with a sensitive threshold
    recognizer.energy_threshold = 300 
    
    device_idx = get_active_mic_index()

    def capture(idx):
        try:
            # We use a short timeout for initialization to check if the device works
            with sr.Microphone(device_index=idx) as source:
                print(f"System: Adjusting noise for device {idx}...")
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                print("Jarvis: Listening...")
                # timeout=None means it waits forever for you to start talking
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=12)
                print("Jarvis: Processing Speech...")
                return recognizer.recognize_google(audio).lower()
        except Exception as e:
            print(f"Device {idx} Failure: {e}")
            return None

    # Try your Headset/Mic first
    query = capture(device_idx)
    
    # If the headset failed (NoneType error fix), try the default system mic
    if query is None and device_idx is not None:
        print("System: Primary device failed. Falling back to default microphone.")
        query = capture(None)
        
    return query if query else ""