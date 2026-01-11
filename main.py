import os
import re
import threading
from dotenv import load_dotenv

# load_dotenv must be at the top level
load_dotenv()

import tkinter as tk
import customtkinter as ctk
import voice_engine
import llm_agent

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Jarvis AI - Personalized Assistant")
        self.geometry("500x650")
        ctk.set_appearance_mode("dark")
        
        # Modern UI Elements
        self.header = ctk.CTkLabel(self, text="JARVIS OS", font=("Poppins", 32, "bold"), text_color="#00F5D4")
        self.header.pack(pady=25)

        self.status = ctk.CTkLabel(self, text="System Online", text_color="gray", font=("Lato", 14))
        self.status.pack(pady=2)

        self.chat_display = ctk.CTkTextbox(self, width=440, height=350, font=("Lato", 16), corner_radius=15)
        self.chat_display.pack(pady=15, padx=20)
        self.chat_display.configure(state="disabled")

        self.mic_btn = ctk.CTkButton(self, text="Tap to Speak", command=self.start_interaction,
                                     fg_color="#1f538d", hover_color="#14375e", height=55, font=("Poppins", 18, "bold"))
        self.mic_btn.pack(pady=10)

        self.stop_btn = ctk.CTkButton(self, text="Stop Talking", command=self.handle_stop,
                                      fg_color="#912c2c", hover_color="#5e1919", height=40)
        self.stop_btn.pack(pady=5)

    def append_chat(self, sender, text="", is_new_block=False):
        """Helper to update the chat display. Fixes the missing 'You' text bug."""
        self.chat_display.configure(state="normal")
        if is_new_block:
            # Insert the sender label AND the text in the same line
            self.chat_display.insert("end", f"\n{sender}: {text}")
        else:
            # Just append the text (used for word-by-word display)
            self.chat_display.insert("end", text)
        
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def handle_stop(self):
        """Triggers the stop command and updates the UI status."""
        voice_engine.stop_speaking()
        self.status.configure(text="Speech Stopped", text_color="#FFB703")

    def start_interaction(self):
        self.mic_btn.configure(state="disabled")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        self.status.configure(text="Listening...", text_color="#00F5D4")
        query = voice_engine.listen()
        
        if not query:
            self.status.configure(text="System Ready", text_color="gray")
            self.mic_btn.configure(state="normal")
            return

        # Correctly display what you said in the 'You:' area
        self.append_chat("You", f"{query}\n", is_new_block=True)
        self.status.configure(text="Thinking...", text_color="#4169E1")
        
        response = llm_agent.get_llm_response(query)
        
        # Filter commands out of speech
        spoken_response = re.sub(r"\[COMMAND:.*?\]", "", response).strip()
        
        if spoken_response:
            self.status.configure(text="Speaking...", text_color="#00F5D4")
            # Create the 'Jarvis:' label first
            self.append_chat("Jarvis", text="", is_new_block=True)
            
            # Callback to append words one-by-one as they are spoken
            def on_word(word):
                self.append_chat("", word + " ")

            voice_engine.speak(spoken_response, on_word_callback=on_word)

        # Trigger desktop automation tasks
        llm_agent.process_command(response)
        
        self.status.configure(text="System Ready", text_color="gray")
        self.mic_btn.configure(state="normal")

if __name__ == "__main__":
    app = JarvisApp()
    # Initial Greeting
    threading.Thread(target=lambda: voice_engine.speak("System initialized. Jarvis is ready.")).start()
    app.mainloop()