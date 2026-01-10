# main.py
import tkinter as tk
import queue
import time
from threading import Thread
import pyttsx3
import winsound
import os
from hon_config import CONFIG
import hon_bot
import hon_ui

# --- SHARED STATE (ORTAK VERI HAVUZU) ---
stats = {
    "my_hp_cur": 0, "my_hp_max": 0, "my_mana": 0,
    "target_hp": -1, "target_mana": -1,
    "target_name": "NO TARGET",
    "ulti_status": "READY",
    "advice": "IDLE",
    "advice_color": "gray",
    "my_faction": "Legion",     
    "my_hero": "Legionnaire",
    "ui_side": "Right", 
    "kongor_time": 0,
    "danger_mode": False,
    "game_time_str": "00:00",
    "mana_alert": False,
    "rune_msg": "-",
    "stack_msg": "-",
    "internal_time_base": 0,
    "internal_time_sys": 0,
    "kongor_trigger": False
}

ui_queue = queue.Queue()

class SoundManager:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', CONFIG["SOUND"]["RATE"])
        self.last_played = {}

    def play_event(self, event_name, text_to_speak=None):
        now = time.time()
        if event_name in self.last_played and now - self.last_played[event_name] < 3.0:
            return
        self.last_played[event_name] = now
        
        if event_name == "EXECUTE" and os.path.exists(CONFIG["SOUND"]["EXECUTE_FILE"]):
            winsound.PlaySound(CONFIG["SOUND"]["EXECUTE_FILE"], winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif text_to_speak:
            Thread(target=self._speak_thread, args=(text_to_speak,)).start()

    def _speak_thread(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except: pass

if __name__ == "__main__":
    sound_mgr = SoundManager()

    t_key = Thread(target=hon_bot.key_listener_loop, args=(stats,))
    t_key.daemon = True
    t_key.start()

    t_bot = Thread(target=hon_bot.bot_loop, args=(stats, ui_queue))
    t_bot.daemon = True
    t_bot.start()
    
    root = tk.Tk()
    app = hon_ui.OverlayApp(root, stats, sound_mgr, ui_queue)
    root.mainloop()