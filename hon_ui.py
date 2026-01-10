# hon_ui.py
import tkinter as tk
import time
import math
import ctypes
from hon_config import CONFIG

class ModernButton(tk.Frame):
    def __init__(self, parent, text, color, command, width=200, height=50):
        super().__init__(parent, bg=CONFIG["COLORS"]["BG"], width=width, height=height)
        self.command = command
        self.color = color
        self.pack_propagate(False)
        self.lbl = tk.Label(self, text=text, bg=CONFIG["COLORS"]["PANEL"], fg=color, font=("Segoe UI", 10, "bold"))
        self.lbl.pack(fill="both", expand=True, padx=2, pady=2)
        self.lbl.bind("<Enter>", self.on_enter)
        self.lbl.bind("<Leave>", self.on_leave)
        self.lbl.bind("<Button-1>", self.on_click)
        self.config(bg=color)
    def on_enter(self, e): self.lbl.config(bg=self.color, fg="black")
    def on_leave(self, e): self.lbl.config(bg=CONFIG["COLORS"]["PANEL"], fg=self.color)
    def on_click(self, e): self.command()

class CleanHudItem(tk.Frame):
    """GENIS VE AYARLI TASARIM"""
    def __init__(self, parent, title, active_color):
        w = CONFIG["UI"]["BOX_W"]
        h = CONFIG["UI"]["BOX_H"]
        super().__init__(parent, bg=CONFIG["COLORS"]["BG"], width=w, height=h)
        self.pack_propagate(False) 
        
        self.active_color = active_color
        
        # 1. BASLIK
        self.lbl_title = tk.Label(self, text=title, font=CONFIG["UI"]["FONT_LABEL"], fg=CONFIG["COLORS"]["TEXT_DIM"], bg=CONFIG["COLORS"]["BG"])
        self.lbl_title.pack(side="top", pady=(5, 2)) 
        
        # 2. DEGER (RAKAM)
        self.lbl_value = tk.Label(self, text="-", font=CONFIG["UI"]["FONT_NUM_NORM"], fg="white", bg=CONFIG["COLORS"]["BG"])
        self.lbl_value.pack(side="top", expand=True) 
        
        # 3. GLOW BAR
        self.bar = tk.Frame(self, bg=CONFIG["COLORS"]["BG"], height=CONFIG["UI"]["BAR_THICKNESS"])
        self.bar.pack(side="bottom", fill="x", pady=(0, 5))

    def update_value(self, text, pulse=False):
        if pulse:
            # Aksiyon Zamani
            self.lbl_value.config(text=text, font=CONFIG["UI"]["FONT_NUM_ACTION"], fg=self.active_color)
            self.lbl_title.config(fg="white") 
            self.bar.config(bg=self.active_color) 
        else:
            # Normal Zaman
            self.lbl_value.config(text=text, font=CONFIG["UI"]["FONT_NUM_NORM"], fg="white")
            self.lbl_title.config(fg=CONFIG["COLORS"]["TEXT_DIM"])
            self.bar.config(bg=CONFIG["COLORS"]["BG"])

class OverlayApp:
    def __init__(self, root, stats, sound_mgr, ui_queue):
        self.root = root
        self.stats = stats
        self.sound_mgr = sound_mgr
        self.ui_queue = ui_queue
        self.hud_initialized = False 
        
        self.root.title("HoN AI COMMAND")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg=CONFIG["COLORS"]["BG"])
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w, h = 800, 600 
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.root.geometry(f"800x600+{x}+{y}")

        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        
        self.is_pinned = False
        self.is_compact = False
        
        self.show_setup_screen()
        self.update_ui_loop()
        self.check_focus_loop()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def check_focus_loop(self):
        try:
            if self.is_pinned:
                self.root.deiconify()
            else:
                user32 = ctypes.windll.user32
                hwnd = user32.GetForegroundWindow()
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                active_title = buff.value
                
                if "Heroes of Newerth" in active_title or "HoN AI" in active_title:
                    self.root.deiconify()
                else:
                    self.root.withdraw()
        except: pass
        self.root.after(500, self.check_focus_loop)

    def show_setup_screen(self):
        self.hud_initialized = False
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="HoN TACTICAL AI", font=("Impact", 24), bg=CONFIG["COLORS"]["BG"], fg=CONFIG["COLORS"]["ACCENT"]).pack(pady=(20,5))
        
        container = tk.Frame(self.root, bg=CONFIG["COLORS"]["BG"])
        container.pack(expand=True, fill="both", padx=30)
        
        f_left = tk.Frame(container, bg=CONFIG["COLORS"]["BG"])
        f_left.pack(side="left", fill="both", expand=True, padx=5)
        self.btn_legion = ModernButton(f_left, "LEGION", CONFIG["COLORS"]["GREEN"], lambda: self.select_faction("Legion"))
        self.btn_legion.pack(pady=5)
        self.btn_hell = ModernButton(f_left, "HELLBOURNE", CONFIG["COLORS"]["RED"], lambda: self.select_faction("Hellbourne"))
        self.btn_hell.pack(pady=5)

        f_center = tk.Frame(container, bg=CONFIG["COLORS"]["BG"])
        f_center.pack(side="left", fill="both", expand=True, padx=5)
        self.btn_legio_hero = ModernButton(f_center, "LEGIONNAIRE", CONFIG["COLORS"]["GOLD"], lambda: self.select_hero("Legionnaire"))
        self.btn_legio_hero.pack(pady=5)
        self.btn_other_hero = ModernButton(f_center, "OTHER HERO", "gray", lambda: self.select_hero("Other"))
        self.btn_other_hero.pack(pady=5)

        f_right = tk.Frame(container, bg=CONFIG["COLORS"]["BG"])
        f_right.pack(side="left", fill="both", expand=True, padx=5)
        self.btn_ui_right = ModernButton(f_right, "RIGHT UI", CONFIG["COLORS"]["BLUE"], lambda: self.select_ui("Right"))
        self.btn_ui_right.pack(pady=5)
        self.btn_ui_left = ModernButton(f_right, "LEFT UI", "gray", lambda: self.select_ui("Left"))
        self.btn_ui_left.pack(pady=5)

        self.btn_launch = tk.Button(self.root, text="INITIALIZE SYSTEM", font=("Segoe UI", 12, "bold"), 
                                    bg="#222", fg="gray", state="disabled", command=self.launch_overlay,
                                    bd=0, padx=30, pady=20)
        self.btn_launch.pack(pady=20)
        tk.Button(self.root, text="EXIT", command=self.root.destroy, bg="#300", fg="red").pack(side="bottom", fill="x")

    def select_faction(self, f):
        self.stats["my_faction"] = f
        self.check_ready()
    def select_hero(self, h):
        self.stats["my_hero"] = h
        self.check_ready()
    def select_ui(self, side):
        self.stats["ui_side"] = side
        self.check_ready()
    def check_ready(self):
        self.btn_launch.config(state="normal", bg=CONFIG["COLORS"]["ACCENT"], fg="black")

    def launch_overlay(self):
        self.root.geometry("600x480+100+100") 
        self.show_hud_screen()

    def show_hud_screen(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.attributes("-alpha", 0.90)
        
        # --- HEADER ---
        self.header = tk.Frame(self.root, bg="#1a1a1a")
        self.header.pack(fill="x")
        mode_color = CONFIG["COLORS"]["GOLD"] if self.stats["my_hero"] == "Legionnaire" else "gray"
        tk.Label(self.header, text=f"{self.stats['my_faction'].upper()} | {self.stats['my_hero'].upper()}", font=("Arial", 7), fg=mode_color, bg="#1a1a1a").pack(side="left", padx=10)
        tk.Button(self.header, text="✕", font=("Arial", 9), bg="#1a1a1a", fg="#ff5555", bd=0, command=self.root.destroy).pack(side="right", padx=5)
        
        self.content_frame = tk.Frame(self.root, bg=CONFIG["COLORS"]["BG"])
        self.content_frame.pack(fill="both", expand=True)
        
        # 1. PLAYER & TIMER
        self.details_frame = tk.Frame(self.content_frame, bg=CONFIG["COLORS"]["BG"])
        self.details_frame.pack(fill="both", pady=(10, 5))

        self.lbl_my = tk.Label(self.details_frame, text="INIT...", font=("Consolas", 10, "bold"), fg=CONFIG["COLORS"]["ACCENT"], bg=CONFIG["COLORS"]["BG"])
        self.lbl_my.pack(pady=2)

        self.lbl_warning = tk.Label(self.details_frame, text="", font=("Arial", 12, "bold"), fg=CONFIG["COLORS"]["WARNING_TEXT"], bg=CONFIG["COLORS"]["BG"])
        self.lbl_warning.pack(pady=0)
        
        self.lbl_timer = tk.Label(self.details_frame, text="--:--", font=("Consolas", 14, "bold"), fg="white", bg=CONFIG["COLORS"]["BG"])
        self.lbl_timer.pack(pady=(2, 0))

        # --- KONGOR ETIKETI EKLENDI ---
        self.lbl_kongor = tk.Label(self.details_frame, text="", font=("Segoe UI", 12, "bold"), fg=CONFIG["COLORS"]["GOLD"], bg=CONFIG["COLORS"]["BG"])
        self.lbl_kongor.pack(pady=(0, 5))

        # 2. RUNE & STACK
        self.macro_frame = tk.Frame(self.content_frame, bg=CONFIG["COLORS"]["BG"])
        self.macro_frame.pack(fill="x", pady=20)
        
        self.macro_container = tk.Frame(self.macro_frame, bg=CONFIG["COLORS"]["BG"])
        self.macro_container.pack(anchor="center")

        # RUNE (SOL)
        self.item_rune = CleanHudItem(self.macro_container, "RUNE", CONFIG["COLORS"]["RUNE"])
        self.item_rune.pack(side="left", padx=40) 
        
        # AYRAC
        separator = tk.Frame(self.macro_container, bg="#333333", width=1, height=60)
        separator.pack(side="left", padx=20, fill="y")

        # STACK (SAG)
        self.item_stack = CleanHudItem(self.macro_container, "STACK", CONFIG["COLORS"]["STACK"])
        self.item_stack.pack(side="left", padx=40) 

        # 3. ADVICE & TARGET
        self.lbl_advice = tk.Label(self.content_frame, text="IDLE", font=("Arial", 16, "bold"), fg="gray", bg=CONFIG["COLORS"]["BG"])
        self.lbl_advice.pack(pady=(20, 10))
        
        self.lbl_target = tk.Label(self.content_frame, text="", font=("Consolas", 10), fg="white", bg=CONFIG["COLORS"]["BG"])
        self.lbl_target.pack(side="bottom", pady=10)
        
        self.hud_initialized = True

    def toggle_mode(self):
        pass 

    def update_ui_loop(self):
        if self.hud_initialized:
            try:
                while not self.ui_queue.empty():
                    msg_type, msg_val = self.ui_queue.get_nowait()
                    if msg_type == "sound":
                        self.sound_mgr.play_event(msg_val, text_to_speak=msg_val)
                
                pulse_val = abs(math.sin(time.time() * 8))
                
                # HP Warning
                hp_color = CONFIG["COLORS"]["ACCENT"]
                warn_txt = ""
                if self.stats.get("danger_mode", False):
                    hp_color = CONFIG["COLORS"]["RED"] if pulse_val > 0.5 else "white"
                    warn_txt = "⚠ LOW HP ⚠" if pulse_val > 0.5 else ""
                
                self.lbl_my.config(text=f"HP: {self.stats['my_hp_cur']}/{self.stats['my_hp_max']} | MP: {self.stats['my_mana']}", fg=hp_color)
                self.lbl_warning.config(text=warn_txt)
                self.lbl_timer.config(text=f"{self.stats['game_time_str']}")
                
                # Rune & Stack
                r_txt = self.stats["rune_msg"]
                is_rune = (r_txt == "SPAWN" or (str(r_txt).isdigit() and int(r_txt) <= 5))
                self.item_rune.update_value(r_txt, pulse=(is_rune and pulse_val > 0.5))

                s_txt = self.stats["stack_msg"]
                is_stack = (s_txt == "PULL" or (str(s_txt).isdigit() and int(s_txt) <= 5))
                self.item_stack.update_value(s_txt, pulse=(is_stack and pulse_val > 0.5))

                self.lbl_advice.config(text=self.stats["advice"], fg=self.stats["advice_color"])
                
                # Target Info
                if self.stats["target_hp"] != -1:
                    self.lbl_target.config(text=f"Target: {self.stats['target_name']} | HP: {self.stats['target_hp']}")
                else:
                    self.lbl_target.config(text="") 

                # --- KONGOR MANTIGI (Geri Geldi) ---
                if self.stats["kongor_time"] > 0:
                    rem = self.stats["kongor_time"] - time.time()
                    if rem > 0:
                        m, s = divmod(int(rem), 60)
                        self.lbl_kongor.config(text=f"KONGOR: {m:02d}:{s:02d}", fg=CONFIG["COLORS"]["GOLD"])
                    else:
                        self.lbl_kongor.config(text="KONGOR SPAWN!", fg="green")
                else:
                    self.lbl_kongor.config(text="")

            except Exception as e:
                print(f"UI Error: {e}")
            
        self.root.after(100, self.update_ui_loop)