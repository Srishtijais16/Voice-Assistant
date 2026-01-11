import webbrowser
import os
import voice_engine
import json
import tkinter as tk
from tkinter import messagebox
import llm_agent
import re

# Safety Filters
BLOCKED_KEYWORDS = ["porn", "malware", "virus", "darkweb"]
PROTECTED_PATHS = ["C:\\Windows", "C:\\System32", "C:\\Program Files"]

def speak(text: str):
    voice_engine.speak(text)

def open_website(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    
    # Safety Check for Restricted Sites
    if any(word in url.lower() for word in BLOCKED_KEYWORDS):
        speak("I cannot open that website. It is on my restricted list for your safety.")
        return

    try:
        webbrowser.open(url)
    except:
        speak("I had some trouble opening the browser.")

def open_explorer():
    os.system("explorer")

def open_app(app_name: str):
    os.system(f"start {app_name}")

def delete_file_safely(file_path: str):
    """Prevents system file deletion and triggers a GUI confirmation."""
    if any(p.lower() in file_path.lower() for p in PROTECTED_PATHS):
        speak("I am sorry, but I cannot delete system files. That would damage your computer.")
        return

    # Popup Confirmation
    root = tk.Tk()
    root.withdraw()
    confirmed = messagebox.askokcancel("Jarvis Confirmation", f"Warning: Do you want to delete this file?\n\n{file_path}")
    root.destroy()

    if confirmed:
        try:
            os.remove(file_path)
            speak("The file has been deleted.")
        except Exception as e:
            speak(f"Error deleting file: {str(e)}")
    else:
        speak("Understood. The file will not be deleted.")

def create_coding_project(description: str):
    """Builds a multi-file coding project."""
    speak("Building your project now. Just a second.")
    
    # Ask LLM for JSON structure
    prompt = f"Build project: {description}. Provide ONLY a JSON object: {{'folder_name': '...', 'files': [{{'file_name': '...', 'content': '...'}}]}}"
    
    try:
        raw_output = llm_agent.get_llm_response(prompt, is_json=True)
        # Strip backticks if present
        json_clean = re.sub(r"```json|```", "", raw_output).strip()
        data = json.loads(json_clean)
        
        folder = data.get('folder_name', 'My_Project')
        if not os.path.exists(folder):
            os.makedirs(folder)

        for f_data in data.get('files', []):
            p = os.path.join(folder, f_data['file_name'])
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(f_data['content'])
        
        speak(f"Project built successfully in the {folder} folder.")
        os.system(f"explorer {folder}")
    except Exception as e:
        print(f"Error building project: {e}")
        speak("I encountered an error while generating the project files.")