# hon_bot.py
import easyocr
import mss
import time
import pyautogui
from threading import Thread
import ctypes
import winsound
from hon_config import CONFIG, HERO_LIST, VK_F11
import hon_utils

def auto_type_kongor_time(timestamp):
    try:
        t_str = time.strftime("%H:%M", time.localtime(timestamp))
        msg = f"Kongor Down! Respawn: {t_str}"
        pyautogui.keyDown('enter')
        time.sleep(0.15) 
        pyautogui.keyUp('enter')
        time.sleep(0.3) 
        pyautogui.write(msg, interval=0.05)
        time.sleep(0.3) 
        pyautogui.press('enter')
    except: pass

def bot_loop(stats, ui_queue):
    print("-> Bot Motoru Aktif")
    print("3. Yapay Zeka (OCR) yukleniyor...")
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Koordinatlari al
    COMMON_BOXES, TARGET_LAYOUTS = hon_utils.get_scaled_boxes()

    with mss.mss() as sct:
        while True:
            try:
                target_layout = TARGET_LAYOUTS[stats["ui_side"]]
                
                # 1. MY STATS
                my_hp_text = hon_utils.read_area(sct, COMMON_BOXES["MY_HP"], reader_obj=reader)
                curr, maxx, perc = hon_utils.parse_hp_bar(my_hp_text)
                stats["my_hp_cur"] = curr
                stats["my_hp_max"] = maxx
                stats["danger_mode"] = True if (0 < perc < 25) else False
                stats["my_mana"] = hon_utils.smart_clean_number(hon_utils.read_area(sct, COMMON_BOXES["MY_MANA"], mode="mana", reader_obj=reader))
                
                # 2. TARGET
                raw_name = hon_utils.read_area(sct, target_layout["NAME"], mode="name", reader_obj=reader)
                
                if len(raw_name) > 2:
                    t_hp = hon_utils.smart_clean_number(hon_utils.read_area(sct, target_layout["HP"], mode="hp", reader_obj=reader))
                    
                    if t_hp > 0:
                        stats["target_name"] = raw_name
                        stats["target_hp"] = t_hp
                        t_mana = hon_utils.smart_clean_number(hon_utils.read_area(sct, target_layout["MANA"], mode="mana", reader_obj=reader))
                        stats["target_mana"] = t_mana
                        stats["mana_alert"] = True if (0 < t_mana < 80) else False
                        
                        raw_type = hon_utils.read_area(sct, target_layout["TYPE"], mode="text", reader_obj=reader)
                        valid_enemy = hon_utils.check_target_validity(raw_name, raw_type, stats["my_faction"])
                    else:
                        stats["target_name"] = raw_name + " (HP?)"
                        stats["target_hp"] = -1
                        valid_enemy = False
                else:
                    stats["target_name"] = "NO TARGET"
                    stats["target_hp"] = -1
                    stats["target_mana"] = -1
                    stats["mana_alert"] = False
                    valid_enemy = False

                # 3. TIMER
                time_text = hon_utils.read_area(sct, COMMON_BOXES["TIMER"], mode="timer", reader_obj=reader)
                mins, secs = hon_utils.parse_game_time(time_text)
                if mins > 0 or secs > 0:
                    current_total_secs = mins * 60 + secs
                    stats["internal_time_base"] = current_total_secs
                    stats["internal_time_sys"] = time.time()
                
                elapsed = time.time() - stats["internal_time_sys"]
                predicted_seconds = int(stats["internal_time_base"] + elapsed)
                p_min, p_sec = divmod(predicted_seconds, 60)
                stats["game_time_str"] = f"{p_min:02d}:{p_sec:02d}"
                
                # RUNE LOGIC
                stats["rune_msg"] = "-"
                if predicted_seconds > 0:
                    mod_rune = predicted_seconds % 120
                    if mod_rune >= 110: 
                        stats["rune_msg"] = f"{120 - mod_rune}"
                    elif mod_rune < 5: 
                        stats["rune_msg"] = "SPAWN"

                # STACK LOGIC
                current_secs_in_min = predicted_seconds % 60
                stats["stack_msg"] = "-"
                if 45 <= current_secs_in_min < 54:
                    stats["stack_msg"] = f"{54 - current_secs_in_min}"
                elif 54 <= current_secs_in_min <= 56:
                    stats["stack_msg"] = "PULL"

                # 4. ULTI & SOUND
                cd_val = hon_utils.smart_clean_number(hon_utils.read_area(sct, COMMON_BOXES["CD"], mode="cd", reader_obj=reader))
                
                if cd_val > 0 and cd_val < 300:
                    stats["ulti_status"] = f"CD ({cd_val}s)"
                    stats["advice"] = "WAIT"
                    stats["advice_color"] = "#555555"
                else:
                    mana_text = hon_utils.read_area(sct, COMMON_BOXES["MANA"], reader_obj=reader)
                    dmg = hon_utils.get_ulti_damage(stats, mana_text)
                    if stats["my_hero"] == "Legionnaire" and dmg > 0:
                        stats["ulti_status"] = f"READY [{dmg}]"
                        if not valid_enemy:
                            stats["advice"] = "INVALID"
                            stats["advice_color"] = "#555555"
                        elif stats["my_mana"] < hon_utils.smart_clean_number(mana_text):
                            stats["advice"] = "MANA"
                            stats["advice_color"] = CONFIG["COLORS"]["BLUE"]
                        elif 0 < stats["target_hp"] < dmg:
                            stats["advice"] = "EXECUTE!"
                            stats["advice_color"] = CONFIG["COLORS"]["MANA_LOW"]
                            ui_queue.put(("sound", "EXECUTE"))
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
                if stats.get("kongor_trigger", False):
                    stats["kongor_trigger"] = False
                    kt = time.time() + 600
                    stats["kongor_time"] = kt
                    Thread(target=auto_type_kongor_time, args=(kt,)).start()

            except Exception as e:
                print(f"Bot Loop Hatasi: {e}")
            
            time.sleep(0.1)

def key_listener_loop(stats):
    user32 = ctypes.windll.user32
    while True:
        if user32.GetAsyncKeyState(VK_F11) & 0x8000:
            stats["kongor_trigger"] = True
            winsound.Beep(1000, 100)
            time.sleep(0.5) 
        time.sleep(0.01)