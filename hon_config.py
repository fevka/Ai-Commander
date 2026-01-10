# hon_config.py

CONFIG = {
    "VERSION": "v4.3 Precision Fix",
    "REF_W": 3840,
    "REF_H": 2160,
    "UI": {
        # --- GENISLIK AYARI (Buyutuldu) ---
        "BOX_W": 180,           # 140 -> 180 yapildi (Sag/Sol bosluk eklendi)
        "BOX_H": 90,            
        
        # --- FONTLAR (Kucultuldu ve Esitlendi) ---
        "FONT_LABEL": ("Segoe UI", 10, "bold"),       # Baslik (Ayni kaldi)
        
        # Rakamlar artik cok daha kucuk (Istegin uzerine)
        "FONT_NUM_NORM": ("Segoe UI", 10, "bold"),    # Normalde 10 punto
        "FONT_NUM_ACTION": ("Segoe UI", 11, "bold"),  # Pulse zamani 11 punto
        
        "BAR_THICKNESS": 4
    },
    "COLORS": {
        "BG": "#0b0c10",       
        "PANEL": "#1f2833",    
        "ACCENT": "#66fcf1",   
        "TEXT_DIM": "#666666",
        "TEXT_BRIGHT": "#ffffff", 
        
        # Ozel Renkler
        "RUNE": "#00ffff",     
        "STACK": "#d500f9",    
        "WARNING_TEXT": "#ff3333",
        
        "GREEN": "#45a29e",
        "RED": "#ff2e63",
        "GOLD": "#ffd700",
        "BLUE": "#4169e1",
        "MANA_LOW": "#00ff00"
    },
    "SOUND": {
        "ENABLED": True,
        "RATE": 150,
        "EXECUTE_FILE": "execute.wav"
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

VK_F11 = 0x7A