# hon_utils.py
import re
import cv2
import numpy as np
import ctypes
from hon_config import CONFIG

def get_scaled_boxes():
    user32_local = ctypes.windll.user32
    screen_w = user32_local.GetSystemMetrics(0)
    screen_h = user32_local.GetSystemMetrics(1)
    
    rx = screen_w / CONFIG["REF_W"]
    ry = screen_h / CONFIG["REF_H"]

    print(f"--- EKRAN ALGILANDI: {screen_w}x{screen_h} (Oran: x{rx:.2f}, y{ry:.2f}) ---")

    def s(val, axis):
        return int(val * rx) if axis == 'x' else int(val * ry)

    common = {
        "MY_HP":   {"top": s(2065,'y'), "left": s(1780,'x'), "width": s(280,'x'), "height": s(45,'y')},
        "MY_MANA": {"top": s(2115,'y'), "left": s(1780,'x'), "width": s(280,'x'), "height": s(45,'y')},
        "CD":      {"top": s(1938,'y'), "left": s(2080,'x'), "width": s(70,'x'),  "height": s(50,'y')},
        "MANA":    {"top": s(1990,'y'), "left": s(2120,'x'), "width": s(60,'x'),  "height": s(35,'y')},
        "TIMER":   {"top": s(5,'y'),    "left": s(1880,'x'), "width": s(90,'x'),  "height": s(45,'y')}
    }

    target = {
        "Right": { 
            "HP":   {"top": s(2074,'y'), "left": s(3250,'x'), "width": s(190,'x'), "height": s(35,'y')},
            "MANA": {"top": s(2107,'y'), "left": s(3250,'x'), "width": s(190,'x'), "height": s(35,'y')},
            "NAME": {"top": s(1860,'y'), "left": s(3490,'x'), "width": s(150,'x'), "height": s(45,'y')},
            "TYPE": {"top": s(1900,'y'), "left": s(3490,'x'), "width": s(200,'x'), "height": s(45,'y')},
        },
        "Left": { 
            "HP":   {"top": s(2074,'y'), "left": s(100,'x'),  "width": s(190,'x'), "height": s(35,'y')},
            "MANA": {"top": s(2107,'y'), "left": s(100,'x'),  "width": s(190,'x'), "height": s(35,'y')},
            "NAME": {"top": s(1860,'y'), "left": s(340,'x'),  "width": s(150,'x'), "height": s(45,'y')},
            "TYPE": {"top": s(1900,'y'), "left": s(340,'x'),  "width": s(150,'x'), "height": s(40,'y')}
        }
    }
    return common, target

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
    nums = re.findall(r'\d+', text)
    try:
        if len(nums) >= 2:
            curr = int(nums[0])
            maxx = int(nums[1])
            percent = (curr / maxx) * 100 if maxx > 0 else 0
            return curr, maxx, percent
        elif len(nums) == 1:
            raw_val = nums[0]
            if len(raw_val) >= 7:
                mid = len(raw_val) // 2
                curr = int(raw_val[:mid])
                maxx = int(raw_val[mid:])
                percent = (curr / maxx) * 100 if maxx > 0 else 0
                return curr, maxx, percent
            else:
                return int(raw_val), 0, 100
    except: pass
    return 0, 0, 0

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

def get_ulti_damage(stats_dict, mana_text):
    if stats_dict["my_hero"] != "Legionnaire": return 0 
    cost = smart_clean_number(mana_text)
    if 110 <= cost <= 130: return 300
    if 150 <= cost <= 170: return 450
    if 190 <= cost <= 210: return 600
    return 0

def read_area(sct, monitor, mode="text", reader_obj=None):
    try:
        mon = {k: int(v) for k, v in monitor.items()}
        img = np.array(sct.grab(mon))
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        
        if mode == "timer":
             _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        elif mode == "cd":
            gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            gray = cv2.bitwise_not(gray)
            _, gray = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
        elif mode == "mana":
             _, gray = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)
        elif mode == "name":
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            _, gray = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)
        elif mode == "hp":
            _, gray = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY)
        else:
             _, gray = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)
        
        result = reader_obj.readtext(gray, detail=0)
        return " ".join(result) if result else ""
    except: return ""

def check_target_validity(name_read, type_read, my_faction):
    if my_faction == "Legion" and "legion" in type_read.lower(): return False
    if my_faction == "Hellbourne" and "hellbourne" in type_read.lower(): return False
    return True