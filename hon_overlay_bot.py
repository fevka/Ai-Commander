print("--- SISTEM BASLATILIYOR (V29 DUAL BOX) ---")
print("1. Kutuphaneler yukleniyor...")

import easyocr
import mss
import cv2
import numpy as np
import tkinter as tk
from threading import Thread
import time
import pyttsx3
import winsound
import re
import os
import ctypes
import pyautogui

# --- AYARLAR & RENKLER ---
C_BG = "#0b0c10"
C_PANEL = "#1f2833"
C_ACCENT = "#66fcf1"
C_TEXT = "#c5c6c7"
C_GREEN = "#45a29e"
C_RED = "#ff2e63"
C_GOLD = "#ffd700"
C_BLUE = "#4169e1" 
C_ALERT = "#ff0000"
C_MANA_LOW = "#00ff00"

# MACRO RENKLER
C_RUNE = "#00ffff" # Cyan
C_RUNE_BG = "#002222" # Koyu Cyan Arka Plan
C_STACK = "#ff00ff" # Magenta
C_STACK_BG = "#220022" # Koyu Magenta Arka Plan

# --- TUS KODLARI ---
VK_F10 = 0x79

# --- KOORDİNAT SİSTEMİ (4K) ---
COMMON_BOXES = {
    "MY_HP":   {"top": 2065, "left": 1800, "width": 200, "height": 45},
    "MY_MANA": {"top": 2115, "left": 1800, "width": 200, "height": 45},
    "CD":      {"top": 1938, "left": 2080, "width": 70,  "height": 50},
    "MANA":    {"top": 1990, "left": 2120, "width": 60,  "height": 35},
    "TIMER":   {"top": 5,    "left": 1880, "width": 90,  "height": 45}
}

TARGET_LAYOUTS = {
    "Right": { 
        "HP":   {"top": 2074, "left": 3270, "width": 140, "height": 35},
        "MANA": {"top": 2107, "left": 3270, "width": 140, "height": 35},
        "NAME": {"top": 1860, "left": 3490, "width": 150, "height": 45},
        "TYPE": {"top": 1900, "left": 3490, "width": 200, "height": 45}
    },
    "Left": { 
        "HP":   {"top": 2074, "left": 124, "width": 140, "height": 35},
        "MANA": {"top": 2107, "left": 124, "width": 140, "height": 35},
        "NAME": {"top": 1860, "left": 340, "width": 150, "height": 45},
        "TYPE": {"top": 1900, "left": 340, "width": 150, "height": 40}
    }
}

HERO_LIST = [
    "Andromeda", "Arachna", "Armadon", "Balphagore", "Behemoth", "Blacksmith", 
    "Blood Hunter", "Bombardier", "Bubbles", "Chaplain", "Chipper", "Corrupted Disciple", 
    "Dark Lady", "Deadwood", "Defiler", "Doctor Repulsor", "Electrician", "Emerald Warden", 
    "Empath", "Engineer", "Fayde", "Flint Beastwood", "Forsaken Archer", "Flux", 
    "Gauntlet", "Gemini", "Glacius", "Grinex", "Gunblade", "Hammerstorm", 
    "Hellbringer", "Jeraziah", "Kinesis", "Legionnaire", "Maliken", "Moon Queen", 
    "Moraxus", "Nomad", "Nymphora", "Ophelia", "Pandamonium", "Parasite", 
    "Pebbles", "Plague Rider", "Pollywog Priest", "Puppet Master", "Ravenor", 
    "Riftwalker", "Sand Wraith", "Scout", "Shadowblade", "Silhouette", "Slither", 
    "Soul Reaper", "Succubus", "Swiftblade", "Tempest", "Thunderbringer", "Torturer", 
    "Valkyrie", "War Beast", "Witch Slayer", "Wildsoul", "Wretched Hag"
]

stats = {
    "my_hp_cur": 0, "my_hp_max": 0, "my_mana": 0,
    "target_hp": 0, "target_mana": 0,
    "target_name": "No Target",
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
    # AYRI MESAJLAR
    "rune_msg": "-",
    "stack_msg": "-"
}

engine = pyttsx3.init()
engine.setProperty('rate', 150)
print("3. Yapay Zeka (OCR) yukleniyor...")
reader = easyocr.Reader(['en'], gpu=False)
user32 = ctypes.windll.user32

# --- FONKSIYONLAR ---
def check_key_press():
    if user32.GetAsyncKeyState(VK_F10) & 0x8000: return True
    return False

def play_alert_sound():
    sound_file = "execute.wav"
    if os.path.exists(sound_file):
        winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        engine.say("Execute")
        engine.runAndWait()

def auto_type_kongor_time(timestamp):
    try:
        t_str = time.strftime("%H:%M", time.localtime(timestamp))
        time.sleep(0.1)
        pyautogui.press('enter')
        time.sleep(0.1)
        pyautogui.write(f"/team Kongor Down! Respawn: {t_str}")
        time.sleep(0.1)
        pyautogui.press('enter')
    except: pass

def smart_clean_number(text):
    if not text: return 0
    text = text.replace("O", "0").replace("o", "0").replace("l", "1").replace("S", "5")
    text = text.replace(".", "").replace(",", "")
    if "/" in text: text = text.split("/")[0]
    numbers = re.findall(r'\d+', text)
    if numbers: return int(numbers[0])
    return 0

def parse_hp_bar(text):
    if not text: return 0, 0, 0
    text = text.replace("O", "0").replace("o", "0").replace("l", "1").replace("S", "5")
    text = text.replace(".", "").replace(",", "")
    try:
        if "/" in text:
            parts = text.split("/")
            curr = int(''.join(filter(str.isdigit, parts[0])))
            maxx = int(''.join(filter(str.isdigit, parts[1])))
            percent = (curr / maxx) * 100 if maxx > 0 else 0
            return curr, maxx, percent
        else:
            curr = int(''.join(filter(str.isdigit, text)))
            return curr, 0, 100
    except: return 0, 0, 0

def parse_game_time(text):
    if not text: return 0, 0
    text = text.replace(".", ":").replace(" ", ":").replace("O", "0").replace("o", "0")
    try:
        if ":" in text:
            parts = text.split(":")
            mins = int(''.join(filter(str.isdigit, parts[0])))
            secs = int(''.join(filter(str.isdigit, parts[1])))
            return mins, secs
        return 0, 0
    except: return 0, 0

def get_ulti_damage(mana_text):
    if stats["my_hero"] != "Legionnaire": return 0 
    cost = smart_clean_number(mana_text)
    if 110 <= cost <= 130: return 300
    if 150 <= cost <= 170: return 450
    if 190 <= cost <= 210: return 600
    return 0

def read_area(sct, monitor, mode="text"):
    try:
        img = np.array(sct.grab(monitor))
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        
        if mode == "timer":
             _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        if mode == "name": gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        elif mode == "cd": _, gray = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
        elif mode == "mana": _, gray = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)
        elif mode != "timer": _, gray = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)
        
        result = reader.readtext(gray, detail=0)
        return " ".join(result) if result else ""
    except: return ""

def get_active_window_title():
    try:
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except: return ""

def check_target_validity(name_read, type_read, my_faction):
    if not name_read or len(name_read) < 2: return False
    is_hero = False
    for hero in HERO_LIST:
        if hero.lower() in name_read.lower():
            is_hero = True
            break
    if not is_hero: return False
    if my_faction == "Legion" and "legion" in type_read.lower(): return False
    if my_faction == "Hellbourne" and "hellbourne" in type_read.lower(): return False
    return True

# --- BOT DONGUSU ---
def bot_loop():
    print("-> Bot Motoru Aktif")
    with mss.mss() as sct:
        last_speak_time = 0
        while True:
            try:
                target_layout = TARGET_LAYOUTS[stats["ui_side"]]
                
                # 1. MY STATS
                my_hp_text = read_area(sct, COMMON_BOXES["MY_HP"])
                curr, maxx, perc = parse_hp_bar(my_hp_text)
                stats["my_hp_cur"] = curr
                stats["my_hp_max"] = maxx
                stats["danger_mode"] = True if (0 < perc < 25) else False
                stats["my_mana"] = smart_clean_number(read_area(sct, COMMON_BOXES["MY_MANA"], mode="mana"))
                
                # 2. TARGET
                stats["target_hp"] = smart_clean_number(read_area(sct, target_layout["HP"]))
                t_mana = smart_clean_number(read_area(sct, target_layout["MANA"], mode="mana"))
                stats["target_mana"] = t_mana
                
                stats["mana_alert"] = True if (0 < t_mana < 80) else False

                raw_name = read_area(sct, target_layout["NAME"], mode="name")
                raw_type = read_area(sct, target_layout["TYPE"], mode="text")
                
                if len(raw_name) < 2: 
                    stats["target_name"] = "NO TARGET"
                    valid_enemy = False
                    stats["mana_alert"] = False
                else:
                    stats["target_name"] = raw_name
                    valid_enemy = check_target_validity(raw_name, raw_type, stats["my_faction"])

                # 3. TIMER & DUAL MACRO CALCULATION
                time_text = read_area(sct, COMMON_BOXES["TIMER"], mode="timer")
                mins, secs = parse_game_time(time_text)
                stats["game_time_str"] = f"{mins:02d}:{secs:02d}"
                
                total_secs = mins * 60 + secs
                
                # RUNE HESABI (Bagimsiz)
                stats["rune_msg"] = "-"
                if total_secs > 0:
                    mod_rune = total_secs % 120
                    if mod_rune >= 110: # Son 10 sn
                        stats["rune_msg"] = f"{120 - mod_rune}"
                    elif mod_rune < 5: # Ilk 5 sn
                        stats["rune_msg"] = "SPAWN"

                # STACK HESABI (Bagimsiz)
                stats["stack_msg"] = "-"
                if total_secs > 0:
                    if 43 <= secs < 53:
                        stats["stack_msg"] = f"{53 - secs}"
                    elif 53 <= secs <= 55:
                        stats["stack_msg"] = "PULL"

                # 4. ULTI
                cd_val = smart_clean_number(read_area(sct, COMMON_BOXES["CD"], mode="cd"))
                if cd_val > 0 and cd_val < 200:
                    stats["ulti_status"] = f"CD ({cd_val}s)"
                    stats["advice"] = "WAIT"
                    stats["advice_color"] = "#555555"
                else:
                    mana_text = read_area(sct, COMMON_BOXES["MANA"])
                    dmg = get_ulti_damage(mana_text)
                    if stats["my_hero"] == "Legionnaire" and dmg > 0:
                        stats["ulti_status"] = f"READY [{dmg}]"
                        if not valid_enemy:
                            stats["advice"] = "INVALID"
                            stats["advice_color"] = "#555555"
                        elif stats["my_mana"] < smart_clean_number(mana_text):
                            stats["advice"] = "MANA"
                            stats["advice_color"] = "#0000ff"
                        elif 0 < stats["target_hp"] < dmg:
                            stats["advice"] = "EXECUTE!"
                            stats["advice_color"] = "#00ff00"
                            if time.time() - last_speak_time > 3:
                                play_alert_sound()
                                last_speak_time = time.time()
                        elif stats["target_hp"] > 0:
                             stats["advice"] = "HOLD"
                             stats["advice_color"] = "#ff3333"
                        else:
                             stats["advice"] = "IDLE"
                             stats["advice_color"] = "#555555"
                    else:
                        stats["ulti_status"] = "READY"
                        stats["advice"] = "MONITORING"
                        stats["advice_color"] = "#444444"
                
                # 5. KONGOR
                if check_key_press():
                    kt = time.time() + 600
                    stats["kongor_time"] = kt
                    winsound.Beep(1000, 100)
                    Thread(target=auto_type_kongor_time, args=(kt,)).start()

            except: pass
            time.sleep(0.1)

# --- UI ---
class ModernButton(tk.Frame):
    def __init__(self, parent, text, color, command, width=200, height=50):
        super().__init__(parent, bg=C_BG, width=width, height=height)
        self.command = command
        self.color = color
        self.text = text
        self.pack_propagate(False)
        self.lbl = tk.Label(self, text=text, bg=C_PANEL, fg=color, font=("Segoe UI", 12, "bold"))
        self.lbl.pack(fill="both", expand=True, padx=2, pady=2)
        self.lbl.bind("<Enter>", self.on_enter)
        self.lbl.bind("<Leave>", self.on_leave)
        self.lbl.bind("<Button-1>", self.on_click)
        self.config(bg=color)
    def on_enter(self, e): self.lbl.config(bg=self.color, fg="black")
    def on_leave(self, e): self.lbl.config(bg=C_PANEL, fg=self.color)
    def on_click(self, e): self.command()

class OverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HoN AI COMMAND")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg=C_BG)
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w, h = 800, 600 
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        
        self.is_compact = False
        self.show_setup_screen()
        self.check_focus_loop()
        self.blink_state = False

    def check_focus_loop(self):
        try:
            active_title = get_active_window_title()
            if "Heroes of Newerth" in active_title or "HoN AI" in active_title:
                self.root.deiconify()
            else:
                self.root.withdraw()
        except: pass
        self.root.after(500, self.check_focus_loop)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def show_setup_screen(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="HoN TACTICAL AI", font=("Impact", 32), bg=C_BG, fg=C_ACCENT).pack(pady=(20,5))
        tk.Label(self.root, text="SYSTEM CONFIGURATION", font=("Segoe UI", 10, "bold"), bg=C_BG, fg="#777").pack(pady=(0,20))

        container = tk.Frame(self.root, bg=C_BG)
        container.pack(expand=True, fill="both", padx=30)

        # LEFT COL: FACTION
        f_left = tk.Frame(container, bg=C_BG)
        f_left.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(f_left, text="FACTION", font=("Segoe UI", 12), bg=C_BG, fg="white").pack(pady=5)
        self.btn_legion = ModernButton(f_left, "LEGION", C_GREEN, lambda: self.select_faction("Legion"))
        self.btn_legion.pack(pady=5)
        self.btn_hell = ModernButton(f_left, "HELLBOURNE", C_RED, lambda: self.select_faction("Hellbourne"))
        self.btn_hell.pack(pady=5)

        # CENTER COL: HERO
        f_center = tk.Frame(container, bg=C_BG)
        f_center.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(f_center, text="HERO MODE", font=("Segoe UI", 12), bg=C_BG, fg="white").pack(pady=5)
        self.btn_legio_hero = ModernButton(f_center, "LEGIONNAIRE", C_GOLD, lambda: self.select_hero("Legionnaire"))
        self.btn_legio_hero.pack(pady=5)
        self.btn_other_hero = ModernButton(f_center, "OTHER HERO", "gray", lambda: self.select_hero("Other"))
        self.btn_other_hero.pack(pady=5)

        # SAG: UI
        f_right = tk.Frame(container, bg=C_BG)
        f_right.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(f_right, text="TARGET PANEL", font=("Segoe UI", 12), bg=C_BG, fg="white").pack(pady=5)
        self.btn_ui_right = ModernButton(f_right, "RIGHT (STD)", C_BLUE, lambda: self.select_ui("Right"))
        self.btn_ui_right.pack(pady=5)
        self.btn_ui_left = ModernButton(f_right, "LEFT (SWAP)", "gray", lambda: self.select_ui("Left"))
        self.btn_ui_left.pack(pady=5)

        self.lbl_status = tk.Label(self.root, text="STATUS: AWAITING INPUT", font=("Consolas", 11), bg=C_BG, fg="#555")
        self.lbl_status.pack(pady=(10, 5))

        self.btn_launch = tk.Button(self.root, text="INITIALIZE SYSTEM", font=("Segoe UI", 14, "bold"), 
                                    bg="#222", fg="gray", state="disabled", command=self.launch_overlay,
                                    bd=0, padx=30, pady=10)
        self.btn_launch.pack(pady=10)
        
        exit_btn = tk.Button(self.root, text="SHUTDOWN SYSTEM", font=("Segoe UI", 10, "bold"),
                             bg="#200000", fg="#ff5555", activebackground="#ff0000", activeforeground="white",
                             bd=0, cursor="hand2", command=self.root.destroy)
        exit_btn.pack(side="bottom", fill="x", ipady=8)

    def select_faction(self, f):
        stats["my_faction"] = f
        self.btn_legion.lbl.config(bg=C_PANEL if f=="Hellbourne" else C_GREEN, fg=C_GREEN if f=="Hellbourne" else "black")
        self.btn_hell.lbl.config(bg=C_PANEL if f=="Legion" else C_RED, fg=C_RED if f=="Legion" else "black")
        self.check_ready()

    def select_hero(self, h):
        stats["my_hero"] = h
        self.btn_legio_hero.lbl.config(bg=C_PANEL if h=="Other" else C_GOLD, fg=C_GOLD if h=="Other" else "black")
        self.btn_other_hero.lbl.config(bg=C_PANEL if h=="Legionnaire" else "gray", fg="gray" if h=="Legionnaire" else "black")
        self.check_ready()

    def select_ui(self, side):
        stats["ui_side"] = side
        self.btn_ui_right.lbl.config(bg=C_PANEL if side=="Left" else C_BLUE, fg=C_BLUE if side=="Left" else "black")
        self.btn_ui_left.lbl.config(bg=C_PANEL if side=="Right" else C_BLUE, fg=C_BLUE if side=="Right" else "black")
        self.check_ready()

    def check_ready(self):
        ready_text = f"READY: {stats.get('my_faction','?')} | {stats.get('my_hero','?')} | UI:{stats.get('ui_side','?')}"
        self.lbl_status.config(text=ready_text, fg=C_ACCENT)
        self.btn_launch.config(state="normal", bg=C_ACCENT, fg="black")

    def launch_overlay(self):
        self.root.geometry("600x420+100+100")
        self.show_hud_screen()

    def show_hud_screen(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.attributes("-alpha", 0.90)
        
        self.header = tk.Frame(self.root, bg="#1a1a1a")
        self.header.pack(fill="x", ipady=5)
        
        mode_color = C_GOLD if stats["my_hero"] == "Legionnaire" else "gray"
        self.lbl_title = tk.Label(self.header, text=f"{stats['my_faction'].upper()} | {stats['my_hero'].upper()}", 
                 font=("Arial", 10, "bold"), fg=mode_color, bg="#1a1a1a")
        self.lbl_title.pack(side="left", padx=15)

        tk.Button(self.header, text="✕", font=("Arial", 12), bg="#1a1a1a", fg="#ff5555", bd=0, 
                  activebackground="red", activeforeground="white", cursor="hand2", 
                  command=self.root.destroy).pack(side="right", padx=5)
        self.btn_mode = tk.Button(self.header, text="—", font=("Arial", 12, "bold"), bg="#1a1a1a", fg="white", bd=0, 
                                  activebackground="#333", cursor="hand2", command=self.toggle_mode)
        self.btn_mode.pack(side="right", padx=5)

        self.content_frame = tk.Frame(self.root, bg=C_BG)
        self.content_frame.pack(fill="both", expand=True)

        self.details_frame = tk.Frame(self.content_frame, bg=C_BG)
        self.details_frame.pack(fill="both")

        self.info_frame = tk.Frame(self.details_frame, bg=C_BG)
        self.info_frame.pack(pady=5)
        
        self.lbl_timer = tk.Label(self.info_frame, text="TIME: --:--", font=("Consolas", 12), fg="white", bg=C_BG)
        self.lbl_timer.pack(side="left", padx=10)
        
        self.lbl_kongor = tk.Label(self.info_frame, text="", font=("Consolas", 12), fg="#ffcc00", bg=C_BG)
        self.lbl_kongor.pack(side="right", padx=10)

        self.lbl_my = tk.Label(self.details_frame, text="PLAYER: ---", font=("Consolas", 14), fg=C_ACCENT, bg=C_BG)
        self.lbl_my.pack(pady=5)
        self.lbl_ulti = tk.Label(self.details_frame, text="...", font=("Verdana", 12), fg="gray", bg=C_BG)
        self.lbl_ulti.pack(pady=5)
        
        # --- MACRO KUTULARI (YAN YANA) ---
        self.macro_frame = tk.Frame(self.content_frame, bg=C_BG)
        self.macro_frame.pack(fill="x", padx=20, pady=5)
        
        # RUNE BOX
        self.rune_box = tk.Frame(self.macro_frame, bg=C_RUNE_BG, highlightbackground=C_RUNE, highlightthickness=2)
        self.rune_box.pack(side="left", fill="x", expand=True, padx=5)
        tk.Label(self.rune_box, text="RUNE", font=("Arial", 8), fg=C_RUNE, bg=C_RUNE_BG).pack()
        self.lbl_rune = tk.Label(self.rune_box, text="-", font=("Impact", 16), fg="white", bg=C_RUNE_BG)
        self.lbl_rune.pack()

        # STACK BOX
        self.stack_box = tk.Frame(self.macro_frame, bg=C_STACK_BG, highlightbackground=C_STACK, highlightthickness=2)
        self.stack_box.pack(side="right", fill="x", expand=True, padx=5)
        tk.Label(self.stack_box, text="STACK", font=("Arial", 8), fg=C_STACK, bg=C_STACK_BG).pack()
        self.lbl_stack = tk.Label(self.stack_box, text="-", font=("Impact", 16), fg="white", bg=C_STACK_BG)
        self.lbl_stack.pack()

        self.lbl_advice = tk.Label(self.content_frame, text="IDLE", font=("Arial", 42, "bold"), fg="gray", bg=C_BG)
        self.lbl_advice.pack(pady=10)

        self.lbl_tname = tk.Label(self.details_frame, text="...", font=("Verdana", 12), fg="white", bg=C_BG)
        self.lbl_tname.pack()
        self.lbl_target = tk.Label(self.details_frame, text="Target Info", font=("Consolas", 14), fg="orange", bg=C_BG)
        self.lbl_target.pack(pady=(0, 20))

        self.update_ui_loop()

    def toggle_mode(self):
        if self.is_compact:
            self.is_compact = False
            self.root.geometry("600x420")
            self.details_frame.pack(before=self.macro_frame, fill="both")
            self.btn_mode.config(text="—")
        else:
            self.is_compact = True
            self.root.geometry("400x180")
            self.details_frame.pack_forget()
            self.btn_mode.config(text="+")

    def update_ui_loop(self):
        try:
            self.lbl_my.config(text=f"HP: {stats['my_hp_cur']}/{stats['my_hp_max']} | MP: {stats['my_mana']}")
            self.lbl_target.config(text=f"HP: {stats['target_hp']} | MP: {stats['target_mana']}")
            self.lbl_tname.config(text=f"{stats['target_name']}")
            self.lbl_ulti.config(text=stats["ulti_status"])
            self.lbl_timer.config(text=f"TIME: {stats['game_time_str']}")
            
            if stats["danger_mode"]:
                self.blink_state = not self.blink_state
                bg = C_ALERT if self.blink_state else C_BG
                self.content_frame.config(bg=bg)
                self.lbl_advice.config(text="LOW HP! RUN!", fg="white", bg=bg)
            else:
                self.content_frame.config(bg=C_BG)
                self.lbl_advice.config(text=stats["advice"], fg=stats["advice_color"], bg=C_BG)

            if stats["mana_alert"] and not stats["danger_mode"] and "EXECUTE" not in stats["advice"]:
                 self.lbl_target.config(fg=C_MANA_LOW, text=f"HP: {stats['target_hp']} | NO MANA!")
            else:
                 self.lbl_target.config(fg="orange")

            rem = stats["kongor_time"] - time.time()
            if rem > 0:
                m, s = divmod(int(rem), 60)
                self.lbl_kongor.config(text=f"R:{m:02d}:{s:02d}")
            else:
                self.lbl_kongor.config(text="")

            # --- DUAL BOX UPDATE ---
            self.lbl_rune.config(text=stats["rune_msg"])
            self.lbl_stack.config(text=stats["stack_msg"])

            self.root.after(100, self.update_ui_loop)
        except: pass

if __name__ == "__main__":
    t = Thread(target=bot_loop)
    t.daemon = True
    t.start()
    
    root = tk.Tk()
    app = OverlayApp(root)
    root.mainloop()