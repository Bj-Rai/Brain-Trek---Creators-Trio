import pygame
import math
import random
import json
import os
import sys
import array
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
IMAGE_DIR = os.path.join(PROJECT_DIR, "assets", "images")
SOUND_DIR = os.path.join(PROJECT_DIR, "assets", "sounds")

# ================= UTILS =================
def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, t): return a + (b - a) * t
def shade(color, d): return tuple(clamp(c + d, 0, 255) for c in color)
def hash01(n): return (math.sin(n) * 43758.5453) % 1.0
def lighten(color, amt): return tuple(min(255, c + amt) for c in color)
def darken(color, amt): return tuple(max(0, c - amt) for c in color)

def soft_shadow(surf, cx, cy, rx, ry, alpha=110):
    w, h = max(4, int(rx * 2.4)), max(4, int(ry * 2.4))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(5, 0, -1):
        f = i / 5
        a = int(alpha * (1 - f) * 0.55)
        rx2, ry2 = int(rx * (0.55 + 0.45 * f)), int(ry * (0.55 + 0.45 * f))
        pygame.draw.ellipse(s, (8, 16, 10, a), (w // 2 - rx2, h // 2 - ry2, rx2 * 2, ry2 * 2))
    surf.blit(s, (int(cx - w // 2), int(cy - h // 2)))

# ================= AUDIO =================
def make_sfx(kind):
    sr = 44100
    P = {
        "coin": [(987.77, 1318.51, 0.10, "pulse_25", 3.0, 0.25)],
        "gem": [(1318.5, 1568, .08, "pulse_25", 2, .3), (1568, 2093, .12, "triangle", 2, .4)],
        "chest": [(440, 554.37, .05, "pulse_25", 1, .25), (659.25, 880, .14, "square", 2.5, .5)],
        "hurt": [(180, 40, .10, "sawtooth", 5, .5), (120, 30, .12, "noise", 4, .5)],
        "clue": [(659.25, 659.25, .09, "triangle", 1.5, .5), (987.77, 987.77, .09, "triangle", 1.5, .5), (1318.5, 1318.5, .22, "triangle", 2, .5)],
        "quest": [(523.25, 523.25, .09, "triangle", 1.5, .5), (783.99, 783.99, .2, "triangle", 2, .5)],
        "correct": [(523.25, 523.25, .06, "square", 1.5, .5), (659.25, 659.25, .06, "square", 1.5, .5), (783.99, 783.99, .06, "square", 1.5, .5), (1046.5, 1046.5, .18, "pulse_25", 3, .25)],
        "wrong": [(330, 165, .18, "sawtooth", 2, .5), (220, 110, .2, "square", 2, .4)],
        "win": [(523.25, 523.25, .1, "square", 1, .5), (659.25, 659.25, .1, "square", 1, .5), (783.99, 783.99, .1, "square", 1, .5), (1046.5, 1046.5, .4, "triangle", 1.5, .5)],
        "fanfare": [(392, 392, .12, "square", 1, .5), (523.25, 523.25, .12, "square", 1, .5), (659.25, 659.25, .12, "square", 1, .5), (783.99, 783.99, .3, "square", 1, .5), (1046.5, 1046.5, .5, "triangle", 1.5, .5)],
        "levelup": [(523.25, 783.99, .15, "square", 1, .5), (783.99, 1046.5, .15, "square", 1, .5), (1046.5, 1318.5, .3, "triangle", 1.5, .5)],
        "gamecomplete": [(523.25, 523.25, .2, "square", 1, .5), (659.25, 659.25, .2, "square", 1, .5), (783.99, 783.99, .2, "square", 1, .5), (1046.5, 1046.5, .6, "triangle", 1, .5)],
        "open": [(90, 40, .6, "noise", 1.2, .5), (60, 30, .6, "sine", 1.2, .5)],
        "chirp": [(2600, 3400, .06, "sine", 2, .5), (3200, 2400, .07, "sine", 2, .4)],
        "click": [(800, 400, .03, "pulse_12", 6, .125)],
        "buy": [(1200, 1200, .04, "pulse_12", 2, .125), (1800, 2400, .10, "pulse_25", 4, .25)],
        "swing": [(700, 150, .09, "noise", 2.5, .5)],
        "plant": [(300, 180, .08, "sine", 2.5, .5), (500, 400, .08, "triangle", 2, .4)],
        "pop": [(600, 900, .06, "pulse_25", 3, .4)],
        "rock": [(150, 60, .12, "noise", 2.0, .5), (90, 40, .15, "sine", 2.0, .5)],
        "step_grass_a": [(260, 80, .06, "square", 3, .5)], "step_grass_b": [(280, 90, .06, "square", 3, .5)],
        "step_dirt_a": [(330, 110, .055, "noise", 3, .5)], "step_dirt_b": [(350, 120, .055, "noise", 3, .5)],
        "step_wood_a": [(520, 190, .05, "square", 3.5, .5)], "step_wood_b": [(560, 210, .05, "square", 3.5, .5)],
    }
    prof = P.get(kind, [(440, 440, .1, "square", 2, .5)])
    total = sum(int(sr * d) for _, _, d, _, _, _ in prof)
    buf = array.array("h", [0] * total * 2)
    cur = 0; phase = 0.0
    for f0, f1, dur, wt, dec, duty in prof:
        n = int(sr * dur)
        for i in range(n):
            pr = i / n
            f = lerp(f0, f1, pr)
            phase = (phase + 2 * math.pi * f / sr) % (2 * math.pi)
            env = min(1, i / max(1, int(sr * .002))) * (1 - pr) ** dec
            if wt == "square": raw = 1.0 if math.sin(phase) >= 0 else -1.0
            elif wt.startswith("pulse"): raw = 1.0 if (phase / (2 * math.pi)) < duty else -1.0
            elif wt == "sawtooth": raw = 2 * ((phase / (2 * math.pi)) % 1) - 1
            elif wt == "triangle":
                v = (phase / (2 * math.pi)) % 1; raw = 4 * v - 1 if v < .5 else 3 - 4 * v
            elif wt == "noise": raw = random.uniform(-1, 1)
            else: raw = math.sin(phase)
            s = int(14000 * env * raw)
            buf[(cur + i) * 2] = s; buf[(cur + i) * 2 + 1] = s
        cur += n
    return pygame.mixer.Sound(buffer=buf)

# Background music is now loaded from the external file "music.mp3"
# (the old code-generated BGM has been removed).
BGM_MENU = "music.mp3"
BGM_PLAY = "music2.mp3"
BGM_END  = "music3.mp3"
BGM_FILE = BGM_MENU

def make_loop(kind):
    sr = 44100; dur = {"wind": 3.0, "water": 2.0, "insect": 2.0, "cave": 4.0, "crackle": 2.0}[kind]
    n = int(sr * dur); buf = array.array("h", [0] * n * 2); last = 0.0
    for i in range(n):
        t = i / sr
        if kind == "wind":
            last = last * .985 + random.uniform(-1, 1) * .015
            v = last * 9 * (.25 + .75 * (.5 + .5 * math.sin(2 * math.pi * t / dur))) * 900
        elif kind == "water":
            last = last * .72 + random.uniform(-1, 1) * .28
            v = last * (.6 + .4 * math.sin(2 * math.pi * t / dur)) * 800
        elif kind == "insect":
            last = last * .5 + random.uniform(-1, 1) * .5
            v = last * (.3 + .7 * (.5 + .5 * math.sin(2 * math.pi * 26 * t))) * 260
        elif kind == "crackle":
            last = last * .8 + (random.uniform(-1, 1) * (1 if random.random() < .05 else 0)) * .5
            v = last * 4000
        else:
            v = (math.sin(2 * math.pi * 98 * t) + math.sin(2 * math.pi * 147 * t)) * (.5 + .5 * math.sin(2 * math.pi * t / dur)) * 700
        s = int(clamp(v, -32000, 32000))
        buf[i * 2] = s; buf[i * 2 + 1] = s
    return pygame.mixer.Sound(buffer=buf)

class Audio:
    def __init__(self):
        self.ready = False; self.muted = False; self.sfx = {}; self.ch = {}
        try: pygame.mixer.init(44100, -16, 2, 512); self.ready = True
        except Exception: return
        try:
            for k in ["coin","gem","chest","hurt","clue","quest","correct","wrong","win","fanfare","levelup","gamecomplete","open","chirp","click","buy","swing","plant","pop","rock",
                      "step_grass_a","step_grass_b","step_dirt_a","step_dirt_b","step_wood_a","step_wood_b"]:
                self.sfx[k] = make_sfx(k)
            # --- Multi-track BGM ---
            self.bgm_ok = False
            self.bgm_path = None
            self.bgm_current = None
            self.bgm_tracks = {}
            try:
                bases = []
                try:
                    bases.append(os.path.dirname(os.path.abspath(__file__)))
                except Exception:
                    pass
                bases.extend([
                    SOUND_DIR,
                    os.getcwd(),
                    "/home/workdir/artifacts",
                    "/home/workdir/attachments",
                    str(Path.home() / "Downloads") if False else os.getcwd(),
                ])
                def _find(name):
                    names = [name, name.lower(), name.upper()]
                    for b in bases:
                        for n in names:
                            p = os.path.join(b, n)
                            if os.path.isfile(p):
                                return os.path.abspath(p)
                    if os.path.isfile(name):
                        return os.path.abspath(name)
                    return None
                for key, fname in (("menu", BGM_MENU), ("play", BGM_PLAY), ("end", BGM_END)):
                    p = _find(fname)
                    if p:
                        self.bgm_tracks[key] = p
                # Prefer menu, else any available track
                start_key = "menu" if "menu" in self.bgm_tracks else (next(iter(self.bgm_tracks)) if self.bgm_tracks else None)
                if start_key:
                    pygame.mixer.music.load(self.bgm_tracks[start_key])
                    pygame.mixer.music.set_volume(0.6)
                    pygame.mixer.music.play(-1)
                    self.bgm_ok = True
                    self.bgm_path = self.bgm_tracks[start_key]
                    self.bgm_current = start_key
            except Exception as _e:
                self.bgm_ok = False
            for k, ci in [("wind",1),("water",2),("insect",3),("cave",4),("crackle",5)]:
                c = pygame.mixer.Channel(ci); c.play(make_loop(k), -1)
                c.set_volume(0.0 if k != "wind" else .3); self.ch[k] = c
        except Exception: self.ready = False

    def play(self, k, vol=1.0):
        if self.ready and not self.muted and vol > .03 and k in self.sfx:
            c = self.sfx[k].play()
            if c: c.set_volume(vol)

    def fade(self, k, v):
        if self.ready and not self.muted and k in self.ch: self.ch[k].set_volume(clamp(v, 0, 1))

    def step(self, surf):
        self.play("step_%s_%s" % (surf, "a" if hash01(pygame.time.get_ticks()) > .5 else "b"), .7)

    def set_music(self, track_key):
        """Switch BGM only when track changes. Never restarts the same track every frame."""
        if not getattr(self, "ready", False):
            return
        if self.muted:
            return
        tracks = getattr(self, "bgm_tracks", {}) or {}
        path = tracks.get(track_key)
        if not path:
            return
        # Same track already selected
        if track_key == getattr(self, "bgm_current", None):
            try:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.6)
                    pygame.mixer.music.play(-1)
                    self.bgm_ok = True
            except Exception:
                pass
            return
        # Different track → load once and loop
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)
            self.bgm_path = path
            self.bgm_current = track_key
            self.bgm_ok = True
        except Exception:
            pass

    def update_for_state(self, state):
        """Map game state → music track (idempotent)."""
        if state in ("INTRO", "TITLE", "MAP", "HOWTO", "CUSTOMIZE"):
            self.set_music("menu")
        elif state in ("GAME_COMPLETE", "CERTIFICATE", "CERT_FORM"):
            self.set_music("end")
        elif state in ("PLAY", "QUIZ", "PAUSE", "SHOP", "LEVEL_DONE", "OVER", "HOUSE"):
            self.set_music("play")

    def mute(self):

        self.muted = not self.muted
        if self.ready:
            try:
                if self.muted:
                    pygame.mixer.music.set_volume(0)
                else:
                    # resume / ensure playing
                    if not pygame.mixer.music.get_busy() and getattr(self, "bgm_ok", False):
                        try:
                            if self.bgm_path:
                                pygame.mixer.music.load(self.bgm_path)
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass
                    pygame.mixer.music.set_volume(0.55)
            except Exception:
                pass
            for c in list(self.ch.values()):
                c.set_volume(0 if self.muted else .5)

# ================= CONFIG =================
W, H = 1100, 700
WW, WH = 3600, 2700
MAP_W, MAP_H = 1100, 700
FPS = 60
SAVE_FILE = "braintrek_save.json"
BRIDGE = pygame.Rect(610, 660, 100, 205)
C_HEART = (190, 70, 70); C_GOLD = (212, 172, 82); C_TEXT = (235, 232, 220)
C_CYAN = (120, 220, 235); C_GREEN_OK = (90, 200, 110); C_RED_BAD = (225, 90, 80)
REED_C = (70, 135, 62)
M_WHITE = (255, 255, 255); M_BLACK = (20, 20, 20); M_GREEN = (70, 170, 70); M_DGREEN = (30, 100, 40)
M_BLUE = (40, 130, 210); M_PURPLE = (135, 80, 190); M_YELLOW = (255, 210, 40); M_BROWN = (105, 65, 30)
M_LBLUE = (45, 175, 220); M_GRAY = (100, 100, 100); M_GRASS = (50, 145, 65)

NUM_LEVELS = 10
level_positions = [
    # Cute winding highland trail (left → right with loops, like a mobile map)
    (90, 520),    # 1 start
    (130, 620),   # 2 dip
    (220, 560),   # 3
    (180, 430),   # 4 up
    (250, 320),   # 5 top-left loop
    (360, 380),   # 6
    (430, 500),   # 7
    (540, 560),   # 8 bottom mid
    (660, 480),   # 9
    (780, 400),   # 10 end stretch
]

BIOMES = [
    # 0 - Dense Pine Forest
    {"name":"Dense Pine Forest","grass":(48,130,68),"leaf":((28,100,48),(55,140,65)),"water":[(30,70,110),(55,110,140),(100,150,160)],"sand":(170,155,120),"foam":(210,240,250),"amb":"leaf","sky":(120,190,230),"tree_type":"pine","houses":False,"flags":True,"chortens":False,"mountains":False,"terraces":False},
    # 1 - High Mountain Pass
    {"name":"High Mountain Pass","grass":(90,115,85),"leaf":((35,85,50),(60,115,70)),"water":[(50,90,130),(80,130,160),(130,170,190)],"sand":(180,170,155),"foam":(230,245,250),"amb":"leaf","sky":(170,195,220),"tree_type":"pine","houses":False,"flags":True,"chortens":True,"mountains":True,"terraces":False},
    # 2 - Riverside Valley
    {"name":"Riverside Valley","grass":(60,135,85),"leaf":((30,100,55),(55,140,75)),"water":[(25,85,115),(55,125,145),(105,165,170)],"sand":(195,180,135),"foam":(220,250,250),"amb":"leaf","sky":(150,200,225),"tree_type":"birch","houses":True,"flags":True,"chortens":False,"mountains":False,"terraces":True},
    # 3 - Ancient Dzong Ruins
    {"name":"Ancient Dzong Ruins","grass":(165,150,95),"leaf":((180,165,110),(200,185,130)),"water":[(130,115,75),(160,145,105),(190,175,135)],"sand":(210,195,155),"foam":(235,225,195),"amb":"ancient","sky":(195,175,140),"tree_type":"oak","houses":False,"flags":True,"chortens":True,"mountains":False,"terraces":False},
    # 4 - Village Foothills
    {"name":"Village Foothills","grass":(70,140,80),"leaf":((40,110,55),(65,150,75)),"water":[(40,90,120),(70,130,150),(120,170,175)],"sand":(185,170,130),"foam":(225,245,250),"amb":"leaf","sky":(140,195,230),"tree_type":"oak","houses":True,"flags":True,"chortens":True,"mountains":True,"terraces":True},
    # 5 - Alpine Meadow
    {"name":"Alpine Meadow","grass":(100,145,90),"leaf":((50,120,65),(80,155,85)),"water":[(60,110,140),(90,145,170),(140,180,195)],"sand":(200,190,160),"foam":(240,250,255),"amb":"leaf","sky":(180,210,235),"tree_type":"pine","houses":False,"flags":True,"chortens":False,"mountains":True,"terraces":False},
    # 6 - Misty Bamboo Grove
    {"name":"Misty Bamboo Grove","grass":(55,125,70),"leaf":((40,115,60),(70,150,80)),"water":[(35,80,105),(65,120,140),(110,160,165)],"sand":(175,165,125),"foam":(215,240,245),"amb":"leaf","sky":(160,185,200),"tree_type":"birch","houses":False,"flags":False,"chortens":False,"mountains":False,"terraces":False},
    # 7 - Cliffside Monastery
    {"name":"Cliffside Monastery","grass":(85,110,80),"leaf":((45,90,55),(70,125,70)),"water":[(55,95,125),(85,135,155),(135,175,185)],"sand":(175,165,150),"foam":(225,240,250),"amb":"leaf","sky":(160,185,215),"tree_type":"pine","houses":True,"flags":True,"chortens":True,"mountains":True,"terraces":False},
    # 8 - Golden Rice Terraces
    {"name":"Golden Rice Terraces","grass":(140,150,70),"leaf":((120,140,60),(160,165,80)),"water":[(50,100,120),(80,140,150),(130,180,170)],"sand":(200,180,120),"foam":(230,245,240),"amb":"leaf","sky":(170,200,220),"tree_type":"oak","houses":True,"flags":True,"chortens":False,"mountains":True,"terraces":True},
    # 9 - Sacred Forest Shrine
    {"name":"Sacred Forest Shrine","grass":(50,120,65),"leaf":((30,95,50),(60,140,70)),"water":[(30,75,105),(60,115,140),(105,155,160)],"sand":(165,150,115),"foam":(210,235,245),"amb":"leaf","sky":(130,180,220),"tree_type":"pine","houses":False,"flags":True,"chortens":True,"mountains":False,"terraces":False},
]
def biome_for(lvl): return (lvl - 1) % len(BIOMES)

# Distinct environment per level (open maps, Brain Trek style)
LEVEL_ENV = {
    # water: "river" (wide + bridge), "stream" (narrow, no bridge), "ponds", "none"
    1:  {"theme": "forest",    "water": "river",   "label": "Misty Pine Forest"},
    2:  {"theme": "forest",    "water": "ponds",   "label": "Rhododendron Woodland"},
    3:  {"theme": "village",   "water": "river",   "label": "Riverside Village"},
    4:  {"theme": "mountain",  "water": "none",    "label": "High Mountain Pass"},
    5:  {"theme": "temple",    "water": "ponds",   "label": "Cliffside Monastery"},
    6:  {"theme": "village",   "water": "none",    "label": "Foothill Market Town"},
    7:  {"theme": "ruins",     "water": "stream",  "label": "Ancient Dzong Ruins"},
    8:  {"theme": "mountain",  "water": "river",   "label": "Alpine River Gorge"},
    9:  {"theme": "temple",    "water": "none",    "label": "Sacred Shrine Plateau"},
    10: {"theme": "city",      "water": "ponds",   "label": "Thimphu Valley Outskirts"},
}


WEATHER_BY_BIOME = {
    0: ["sunshine", "rain"],
    1: ["wind", "fog"],
    2: ["rain", "sunshine"],
    3: ["sunshine", "wind"],
    4: ["sunshine", "rain"],
    5: ["wind", "sunshine"],
    6: ["fog", "rain"],
    7: ["wind", "fog"],
    8: ["sunshine", "rain"],
    9: ["fog", "sunshine"],
}

# ================= QUESTION BANK =================
# Format: (Subject, Question, Answer, [Options], Fact, Difficulty 1-5)
# Difficulty scales with levels: early = recall, late = reasoning
QUESTION_BANK = [
    # ===== DIFFICULTY 1 – foundation (levels 1–2) =====
    ("Science", "Which gas do trees release that we breathe?", "oxygen", ["oxygen", "carbon dioxide", "nitrogen", "helium"], "Trees take in CO2 and release oxygen during photosynthesis.", 1),
    ("Science", "What do green plants need to make their food?", "sunlight", ["sunlight", "moonlight", "salt water", "wind only"], "Photosynthesis uses sunlight, water, and carbon dioxide.", 1),
    ("Science", "How many legs does a spider have?", "8", ["8", "6", "10", "4"], "All spiders have eight legs.", 1),
    ("Science", "Frozen water is which state of matter?", "solid", ["solid", "liquid", "gas", "plasma"], "Ice is water in its solid state.", 1),
    ("Science", "Which organ pumps blood around the body?", "heart", ["heart", "lungs", "liver", "stomach"], "The heart is a muscular pump for blood.", 1),
    ("Mathematics", "What is 7 + 6?", "13", ["13", "12", "14", "11"], "7 + 6 = 13.", 1),
    ("Mathematics", "What is 8 x 5?", "40", ["40", "35", "45", "13"], "8 groups of 5 is 40.", 1),
    ("Mathematics", "What is 10 - 4?", "6", ["6", "5", "7", "14"], "10 take away 4 leaves 6.", 1),
    ("Mathematics", "Half of 20 is?", "10", ["10", "5", "15", "8"], "Half means divide by 2: 20 / 2 = 10.", 1),
    ("Mathematics", "What is 9 + 3?", "12", ["12", "11", "13", "6"], "9 + 3 = 12.", 1),
    ("History", "What is the capital of Bhutan?", "thimphu", ["thimphu", "paro", "punakha", "phuentsholing"], "Thimphu is Bhutan's capital city.", 1),
    ("History", "Bhutan's national sport is?", "archery", ["archery", "football", "cricket", "wrestling"], "Archery is the national sport of Bhutan.", 1),
    ("Environment", "What do bees collect from flowers?", "nectar", ["nectar", "soil", "bark", "stones"], "Bees gather nectar to make honey.", 1),
    ("Environment", "Why are forests important for animals?", "they provide habitat", ["they provide habitat", "they stop all rain", "they remove rivers", "they block sunlight forever"], "Forests give food, shelter, and breeding places.", 1),
    ("Economics", "You have 50 gold and spend 20. How much remains?", "30", ["30", "20", "70", "50"], "50 - 20 = 30 gold left.", 1),
    ("Economics", "A person who buys goods is called a?", "consumer", ["consumer", "producer", "farmer only", "miner"], "Consumers buy and use goods and services.", 1),

    # ===== DIFFICULTY 2 – solid basics (levels 2–4) =====
    ("Science", "Which gas do trees absorb from the air?", "carbon dioxide", ["carbon dioxide", "oxygen", "neon", "hydrogen"], "Trees use carbon dioxide in photosynthesis.", 2),
    ("Science", "Water boils at about what temperature at sea level?", "100 C", ["100 C", "50 C", "0 C", "200 C"], "At standard pressure, water boils at 100°C.", 2),
    ("Science", "Which planet is known as the Red Planet?", "mars", ["mars", "venus", "jupiter", "mercury"], "Iron oxide gives Mars its red colour.", 2),
    ("Science", "A crab has how many walking legs?", "8", ["8", "6", "10", "4"], "Crabs have 8 walking legs plus claws.", 2),
    ("Science", "Which vitamin can your skin make from sunlight?", "vitamin d", ["vitamin d", "vitamin c", "vitamin a", "vitamin b12"], "Sunlight helps the skin produce vitamin D.", 2),
    ("Mathematics", "Solve: (12 + 8) / 4", "5", ["5", "4", "6", "8"], "Brackets first: 20 / 4 = 5.", 2),
    ("Mathematics", "What is 9 x 7?", "63", ["63", "56", "72", "54"], "9 x 7 = 63.", 2),
    ("Mathematics", "What is 100 divided by 4?", "25", ["25", "20", "40", "50"], "100 / 4 = 25.", 2),
    ("Mathematics", "What is 3 x 8?", "24", ["24", "21", "27", "18"], "3 x 8 = 24.", 2),
    ("Mathematics", "What is 12 x 12?", "144", ["144", "124", "132", "156"], "12 x 12 = 144.", 2),
    ("History", "Bhutan lies in which mountain range?", "himalayas", ["himalayas", "andes", "alps", "rockies"], "Bhutan is in the eastern Himalayas.", 2),
    ("History", "Bhutan's national animal is the?", "takin", ["takin", "tiger", "snow leopard", "yak"], "The takin is Bhutan's national animal.", 2),
    ("History", "Bhutan's national flower is the?", "blue poppy", ["blue poppy", "lotus", "rose", "orchid"], "The Himalayan blue poppy is the national flower.", 2),
    ("History", "What is the currency of Bhutan?", "ngultrum", ["ngultrum", "rupee", "taka", "yen"], "The ngultrum (Nu) is Bhutan's currency.", 2),
    ("Environment", "What do decomposers do?", "break down dead organisms", ["break down dead organisms", "make new mountains", "create wind", "produce only heat"], "Decomposers recycle nutrients into soil.", 2),
    ("Environment", "A major cause of soil erosion is?", "cutting down trees", ["cutting down trees", "planting grass", "building terraces", "mulching soil"], "Tree roots hold soil in place.", 2),
    ("Environment", "Which animal is a herbivore?", "deer", ["deer", "tiger", "eagle", "wolf"], "Deer eat plants, so they are herbivores.", 2),
    ("Economics", "Saving money mainly means?", "spending less than you earn", ["spending less than you earn", "borrowing more always", "ignoring prices", "printing notes"], "Savings grow when income exceeds spending.", 2),
    ("Economics", "Trading goods without using money is called?", "barter", ["barter", "tax", "interest", "wage"], "Barter is direct exchange of goods or services.", 2),
    ("Economics", "Money kept in a bank can earn?", "interest", ["interest", "rent tax", "debt only", "inflation always"], "Banks may pay interest on savings.", 2),

    # ===== DIFFICULTY 3 – applied thinking (levels 4–6) =====
    ("Science", "Water vapour turning into rain is called?", "condensation", ["condensation", "evaporation", "erosion", "melting"], "Cooling vapour condenses into liquid drops.", 3),
    ("Science", "The powerhouse of the cell is the?", "mitochondria", ["mitochondria", "nucleus", "ribosome", "vacuole"], "Mitochondria produce most of the cell's energy (ATP).", 3),
    ("Science", "Most abundant gas in Earth's air is?", "nitrogen", ["nitrogen", "oxygen", "carbon dioxide", "argon"], "About 78% of air is nitrogen.", 3),
    ("Science", "Which process removes CO2 from the air?", "photosynthesis", ["photosynthesis", "respiration", "combustion", "digestion"], "Plants lock carbon into sugars via photosynthesis.", 3),
    ("Science", "Blood travels through the body in?", "blood vessels", ["blood vessels", "bones only", "nerves only", "skin pores"], "Arteries and veins carry blood.", 3),
    ("Mathematics", "What is 15% of 200?", "30", ["30", "15", "20", "45"], "10% of 200 is 20; 5% is 10; total 30.", 3),
    ("Mathematics", "What is the square root of 144?", "12", ["12", "14", "16", "10"], "12 x 12 = 144.", 3),
    ("Mathematics", "Solve: 3 x (4 + 7) - 5", "28", ["28", "33", "23", "38"], "Brackets: 11; 3x11=33; 33-5=28.", 3),
    ("Mathematics", "If 3x + 4 = 19, what is x?", "5", ["5", "4", "6", "7"], "3x = 15, so x = 5.", 3),
    ("Mathematics", "What is 2 to the power of 5?", "32", ["32", "16", "64", "25"], "2x2x2x2x2 = 32.", 3),
    ("Mathematics", "Next prime number after 7?", "11", ["11", "9", "10", "8"], "8, 9, 10 are not prime; 11 is.", 3),
    ("History", "In which year did Bhutan adopt its Constitution?", "2008", ["2008", "1999", "2010", "1985"], "Bhutan became a constitutional monarchy in 2008.", 3),
    ("History", "Which king introduced Gross National Happiness?", "jigme singye wangchuck", ["jigme singye wangchuck", "ugyen wangchuck", "jigme dorji wangchuck", "jigme khesar namgyel wangchuck"], "The 4th King popularised GNH as a development goal.", 3),
    ("History", "Bhutan joined the United Nations in?", "1971", ["1971", "1961", "1981", "1991"], "Bhutan became a UN member in 1971.", 3),
    ("History", "Country that borders Bhutan to the north?", "china", ["china", "india", "nepal", "bangladesh"], "China (Tibet region) lies north of Bhutan.", 3),
    ("Environment", "Variety of life on Earth is called?", "biodiversity", ["biodiversity", "geology", "climate only", "altitude"], "Biodiversity means the variety of living things.", 3),
    ("Environment", "Planting trees on bare land is called?", "afforestation", ["afforestation", "deforestation", "desertification", "mining"], "Afforestation increases forest cover.", 3),
    ("Environment", "Which is a renewable energy source?", "solar power", ["solar power", "coal", "oil", "natural gas"], "Sunlight keeps arriving; fossil fuels do not renew quickly.", 3),
    ("Environment", "A greenhouse gas that traps heat is?", "methane", ["methane", "oxygen", "nitrogen", "argon"], "Methane and CO2 trap heat in the atmosphere.", 3),
    ("Economics", "Inflation means?", "a general rise in prices", ["a general rise in prices", "falling prices only", "fixed prices forever", "lower wages always"], "Inflation reduces how much one unit of money can buy.", 3),
    ("Economics", "Buying local goods mainly helps?", "the local economy", ["the local economy", "only foreign banks", "imports only", "inflation always"], "Local spending supports nearby jobs and businesses.", 3),
    ("Economics", "25% of 80 equals?", "20", ["20", "25", "40", "16"], "One quarter of 80 is 20.", 3),

    # ===== DIFFICULTY 4 – reasoning (levels 6–8) =====
    ("Science", "Speed of light is about?", "300000 km/s", ["300000 km/s", "30000 km/s", "3000 km/s", "150000 km/s"], "Light travels roughly 300,000 kilometres per second.", 4),
    ("Science", "Chemical symbol for gold is?", "au", ["au", "ag", "go", "gd"], "Au comes from Latin aurum.", 4),
    ("Science", "Largest organ of the human body?", "skin", ["skin", "liver", "brain", "heart"], "Skin covers the body and is the largest organ.", 4),
    ("Science", "If a trekker climbs higher, air pressure usually?", "decreases", ["decreases", "increases", "stays identical", "becomes pure oxygen"], "Higher altitude means thinner air and lower pressure.", 4),
    ("Science", "Why do highland lakes often look blue-green?", "light scatters in clean water", ["light scatters in clean water", "the water is painted", "fish dye the water", "ice always melts red"], "Clear water scatters shorter wavelengths of light.", 4),
    ("Mathematics", "Solve: 2x + 5 = 15", "5", ["5", "10", "7", "20"], "2x = 10 → x = 5.", 4),
    ("Mathematics", "What is 15 squared?", "225", ["225", "215", "255", "200"], "15 x 15 = 225.", 4),
    ("Mathematics", "A path is 3 km up and 3 km down. Average speed up is 3 km/h, down is 6 km/h. Total time?", "1.5 hours", ["1.5 hours", "1 hour", "2 hours", "3 hours"], "Up: 1 h; down: 0.5 h; total 1.5 h.", 4),
    ("Mathematics", "You find 3 chests worth 80, 150 and 220 gold. Average value?", "150", ["150", "180", "130", "200"], "(80+150+220)/3 = 450/3 = 150.", 4),
    ("Mathematics", "A map scale is 1:50000. 2 cm on map equals how many km on ground?", "1 km", ["1 km", "0.5 km", "2 km", "5 km"], "2 cm x 50000 = 100000 cm = 1 km.", 4),
    ("History", "Who is credited with building early Dzongs and unifying Bhutan?", "ngawang namgyal", ["ngawang namgyal", "ugyen wangchuck", "padmasambhava", "jigme dorji"], "Zhabdrung Ngawang Namgyal founded the dual system and many Dzongs.", 4),
    ("History", "First King of unified modern Bhutan?", "ugyen wangchuck", ["ugyen wangchuck", "jigme wangchuck", "jigme singye wangchuck", "jigme khesar namgyel wangchuck"], "Ugyen Wangchuck was crowned in 1907.", 4),
    ("History", "GNH stands for?", "gross national happiness", ["gross national happiness", "gross national harvest", "general national highway", "global nature heritage"], "Bhutan measures progress with Gross National Happiness.", 4),
    ("Environment", "Primary driver of recent climate change is?", "greenhouse gases", ["greenhouse gases", "only volcanoes", "only solar eclipses", "ocean salt"], "Human-caused greenhouse gases trap extra heat.", 4),
    ("Environment", "Which action best reduces plastic waste on a trek?", "reusing containers", ["reusing containers", "burning all plastic", "leaving bottles on trails", "using more single-use packs"], "Reuse stops plastic entering rivers and soil.", 4),
    ("Environment", "Ozone layer mainly protects life from?", "ultraviolet radiation", ["ultraviolet radiation", "all rain", "earthquakes", "wind only"], "Stratospheric ozone absorbs harmful UV rays.", 4),
    ("Economics", "Opportunity cost is?", "the next best alternative given up", ["the next best alternative given up", "the price of gold only", "a bank fee always", "total profit only"], "Every choice costs the best option you did not take.", 4),
    ("Economics", "A tax on imported goods is called a?", "tariff", ["tariff", "subsidy", "wage", "dividend"], "Tariffs tax imports and can protect local producers.", 4),
    ("Economics", "A market with only one seller is a?", "monopoly", ["monopoly", "competition", "barter fair", "cooperative only"], "Mono = one; a single seller controls supply.", 4),
    ("Economics", "If demand rises and supply stays the same, price tends to?", "increase", ["increase", "fall to zero", "stay fixed forever", "disappear"], "More buyers chasing the same goods push prices up.", 4),

    # ===== DIFFICULTY 5 – challenge / multi-step (levels 8–10) =====
    ("Science", "A trekker boils water at high altitude. It boils at a lower temperature because?", "air pressure is lower", ["air pressure is lower", "water becomes oil", "gravity reverses", "the sun is closer"], "Lower pressure lowers the boiling point.", 5),
    ("Science", "Photosynthesis stores energy mainly in which molecule form?", "sugars (glucose)", ["sugars (glucose)", "pure nitrogen gas", "table salt", "iron ore"], "Light energy is stored in chemical bonds of sugars.", 5),
    ("Science", "Why are decomposers essential after a forest fire?", "they recycle nutrients into soil", ["they recycle nutrients into soil", "they create new oxygen tanks", "they stop all rain", "they build bridges"], "Without decomposers, nutrients stay locked in dead matter.", 5),
    ("Mathematics", "A merchant sells 4 maps for 60 gold each and buys supplies for 90 gold. Net gold from maps after supplies?", "150", ["150", "240", "90", "60"], "4x60=240; 240-90=150.", 5),
    ("Mathematics", "Trail sections: 2.5 km, 3.5 km, 4 km. You walk 5 km/h. Hours needed (no rests)?", "2", ["2", "1.5", "3", "10"], "Total 10 km / 5 km/h = 2 hours.", 5),
    ("Mathematics", "Solve for x: 4(x - 3) = 2x + 10", "11", ["11", "8", "5", "14"], "4x - 12 = 2x + 10 → 2x = 22 → x = 11.", 5),
    ("Mathematics", "A square terrace has area 196 m². Length of one side?", "14 m", ["14 m", "12 m", "16 m", "98 m"], "Side = square root of 196 = 14.", 5),
    ("Mathematics", "Probability of rolling a 6 on a fair die?", "1/6", ["1/6", "1/2", "1/3", "1/12"], "One favourable face out of six equally likely faces.", 5),
    ("History", "Why were Dzongs built on ridges and river bends?", "defence and administration", ["defence and administration", "only for decoration", "to block all trade", "to hide from the sun"], "Dzongs served as fortresses and centres of local rule.", 5),
    ("History", "Constitutional monarchy means the king's powers are?", "limited by a constitution", ["limited by a constitution", "unlimited in every matter", "removed completely", "shared only with merchants"], "A constitution defines and limits royal and government powers.", 5),
    ("Environment", "Terracing on mountain slopes mainly helps by?", "reducing soil erosion", ["reducing soil erosion", "increasing wind speed", "removing all water", "stopping photosynthesis"], "Steps slow runoff and hold soil on steep land.", 5),
    ("Environment", "If a valley loses half its forest, which effect is most likely?", "more soil washed into rivers", ["more soil washed into rivers", "instant desert worldwide", "no change at all", "air loses all nitrogen"], "Fewer roots mean more erosion and sediment.", 5),
    ("Economics", "A village produces more cheese than it needs and trades the extra. This is?", "specialisation and trade", ["specialisation and trade", "inflation only", "a monopoly law", "barter ban"], "Surplus from specialisation enables trade.", 5),
    ("Economics", "Real value of money falls when?", "prices rise generally (inflation)", ["prices rise generally (inflation)", "you save in a box", "you plant a tree", "you walk uphill"], "Inflation reduces purchasing power.", 5),
    ("Science", "On a cold highland morning you see fog in the valley. Fog is?", "tiny water droplets in air", ["tiny water droplets in air", "smoke from space", "dry dust only", "frozen nitrogen blocks"], "Fog is a cloud at ground level made of droplets.", 5),
    ("Mathematics", "Three quiz chests give scores 8, 9 and 10. What is the mean score?", "9", ["9", "8", "10", "27"], "Mean = (8+9+10)/3 = 9.", 5),
]

ACH = {
    "first_steps": ("First Steps", "Clear level 1"),
    "treasure_hunter": ("Treasure Hunter", "Open 25 chests"),
    "scholar": ("Scholar", "Answer 20 questions correctly"),
    "brain_master": ("Brain Master", "Answer 50 questions correctly"),
    "nature_guardian": ("Nature Guardian", "Complete 3 environmental quests"),
    "explorer": ("Explorer", "Find 5 secret chests"),
    "perfect_level": ("Perfect Level", "Complete a level without wrong answers"),
    "world_walker": ("World Walker", "Visit 6 different biomes"),
    "valley_cleaner": ("Valley Cleaner", "Pick up all litter in a level"),
    "green_thumb": ("Green Thumb", "Plant 3 saplings"),
    "merchant_friend": ("Merchant's Friend", "Buy 3 items"),
    "wildlife_watcher": ("Wildlife Watcher", "Observe rabbit, bird and fish"),
    "beast_slayer": ("Beast Slayer", "Defeat 3 enemies in one level"),
    "naturalist": ("Naturalist", "Forage 5 bushes"),
    "spring_bather": ("Spring Bather", "Rest at a hot spring"),
    "lore_seeker": ("Lore Seeker", "Read an ancient statue"),
}

SKINS = {
    "classic": {"name": "Classic Gho", "robe": (188,138,48), "belt": (70,45,20), "cuff": (235,232,225), "hat": (24,24,28), "sash": (232,150,60), "price": 0},
    "red": {"name": "Red Kabney", "robe": (168,64,52), "belt": (60,40,20), "cuff": (235,225,200), "hat": (24,24,28), "sash": (205,70,55), "price": 7000},
    "saffron": {"name": "Saffron Festival", "robe": (214,150,40), "belt": (120,60,20), "cuff": (245,240,225), "hat": (120,40,40), "sash": (240,180,60), "price": 8000},
    "green": {"name": "Gompo Herder", "robe": (96,124,72), "belt": (60,45,25), "cuff": (235,232,225), "hat": (70,55,35), "sash": (120,150,90), "price": 7500},
}

RARITY = {"common": (80, (235,215,130)), "rare": (150, (120,220,235)), "epic": (220, (200,140,230))}

# Collectible resources (trade at Dawa's shop). Coins remain gold.
RESOURCE_TYPES = {
    "gem":      {"name": "Gem", "color": (80, 200, 255), "label": "Gems"},
    "scroll":   {"name": "Ancient Scroll", "color": (230, 200, 120), "label": "Scrolls"},
    "relic":    {"name": "Historical Relic", "color": (200, 140, 80), "label": "Relics"},
    "nature":   {"name": "Nature Item", "color": (100, 200, 110), "label": "Nature"},
    "artifact": {"name": "Legendary Artifact", "color": (220, 100, 255), "label": "Artifacts"},
}


def mtext(surf, text, font, color, x, y, center=True):
    img = font.render(text, True, color)
    r = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
    surf.blit(img, r)

def mstar(surf, x, y, radius, color):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.45
        pts.append((x + math.cos(ang) * r, y + math.sin(ang) * r))
    pygame.draw.polygon(surf, color, pts)

def mstars(surf, x, y, n):
    for i in range(3):
        mstar(surf, x - 25 + i * 25, y, 11, M_YELLOW if i < n else M_GRAY)

def mtree(surf, x, y):
    pygame.draw.rect(surf, M_BROWN, (x - 7, y, 14, 35))
    pygame.draw.circle(surf, M_DGREEN, (x, y - 15), 30)
    pygame.draw.circle(surf, M_GREEN, (x - 18, y), 24)
    pygame.draw.circle(surf, M_GREEN, (x + 18, y), 24)

# ================= ANIME-STYLE PLAYER DRAWING =================
def draw_anime_player(surf, x, y, direction, frame, moving, skin_data, gender="male"):
    """Bhutanese explorer with natural walk cycle – stride, opposite arms, foot plant bob."""
    # Continuous phase from walk counter (smooth, not jumpy frames)
    phase = frame * 0.38
    # Idle: gentle breathing bob
    idle_bob = math.sin(frame * 0.08) * 0.4 if not moving else 0
    # Walk: body rises/falls twice per full stride (foot plant)
    stride = math.sin(phase)
    stride2 = math.sin(phase * 2.0)  # double-frequency for vertical bob
    bob = (abs(stride2) * 1.35) if moving else idle_bob
    # Legs opposite: left +sin, right -sin
    leg_swing = stride * 5.5 if moving else 0
    # Arms opposite to legs (natural counter-swing)
    arm_swing = math.sin(phase + math.pi) * 4.2 if moving else 0
    # Slight forward lean into movement
    lean = 0
    if moving:
        if direction == "left": lean = -0.9
        elif direction == "right": lean = 0.9
        elif direction == "up": lean = 0
        else: lean = 0
    x = x + lean
    robe = skin_data.get("robe", (188, 138, 48))
    sash = skin_data.get("sash", (232, 150, 60))
    belt_c = skin_data.get("belt", (70, 45, 20))
    is_female = (gender == "female")
    by = bob

    # Ground shadow (soft, plants under feet)
    sh = pygame.Surface((36, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 55), (0, 2, 36, 11))
    surf.blit(sh, (int(x - 18), int(y + 1)))

    skin = (252, 220, 195) if is_female else (245, 210, 180)
    hair_c = (40, 24, 18) if is_female else (30, 22, 38)
    hair_hi = (95, 65, 48) if is_female else (68, 52, 85)

    # ========== BODY ==========
    if is_female:
        # Bhutanese adventurer: wonju + kira + kera + rachu (pixel art)
        kira = robe
        kira_dk = darken(kira, 28)
        kira_lt = lighten(kira, 18)
        wonju = (250, 240, 228)
        wonju_dk = (228, 212, 198)
        kera_c = belt_c if belt_c else (55, 35, 20)

        # Kira skirt — A-line with weave
        pygame.draw.polygon(surf, kira_dk, [
            (x - 10, y - 18 + by), (x + 10, y - 18 + by),
            (x + 14, y + 5 + by), (x - 14, y + 5 + by)
        ])
        pygame.draw.polygon(surf, kira, [
            (x - 9, y - 17 + by), (x + 9, y - 17 + by),
            (x + 12, y + 4 + by), (x - 12, y + 4 + by)
        ])
        pygame.draw.line(surf, kira_dk, (x - 3, y - 16 + by), (x - 5, y + 3 + by), 1)
        pygame.draw.line(surf, kira_lt, (x + 3, y - 16 + by), (x + 5, y + 3 + by), 1)
        for i in range(4):
            ly = y - 14 + by + i * 4
            hw = 8 + i
            pygame.draw.line(surf, darken(kira, 15 + i * 3), (x - hw, ly), (x + hw, ly), 1)
        pygame.draw.line(surf, kira_lt, (x - 11, y + 3 + by), (x + 11, y + 3 + by), 1)

        # Wonju blouse
        pygame.draw.rect(surf, wonju_dk, (x - 9, y - 32 + by, 18, 15), border_radius=3)
        pygame.draw.rect(surf, wonju, (x - 8, y - 31 + by, 16, 13), border_radius=3)
        pygame.draw.rect(surf, (255, 248, 238), (x - 6, y - 30 + by, 12, 4), border_radius=2)
        pygame.draw.line(surf, (210, 190, 175), (x - 4, y - 28 + by), (x + 4, y - 28 + by), 1)

        # Kera belt + clasp
        pygame.draw.rect(surf, kera_c, (x - 11, y - 18 + by, 22, 5), border_radius=1)
        pygame.draw.rect(surf, lighten(kera_c, 25), (x - 11, y - 18 + by, 22, 1))
        pygame.draw.rect(surf, C_GOLD, (x - 3, y - 18 + by, 6, 5), border_radius=1)
        pygame.draw.circle(surf, (255, 220, 100), (int(x), int(y - 16 + by)), 1)

        # Rachu scarf
        rachu = sash
        if direction in ("down", "left"):
            pygame.draw.lines(surf, darken(rachu, 25), False, [
                (x - 8, y - 30 + by), (x - 2, y - 22 + by), (x + 8, y - 10 + by)
            ], 4)
            pygame.draw.lines(surf, rachu, False, [
                (x - 7, y - 29 + by), (x - 1, y - 21 + by), (x + 7, y - 11 + by)
            ], 2)
        else:
            pygame.draw.lines(surf, darken(rachu, 25), False, [
                (x + 8, y - 30 + by), (x + 2, y - 22 + by), (x - 8, y - 10 + by)
            ], 4)
            pygame.draw.lines(surf, rachu, False, [
                (x + 7, y - 29 + by), (x + 1, y - 21 + by), (x - 7, y - 11 + by)
            ], 2)

        # Arms
        aL = arm_swing
        aR = -arm_swing
        if direction == "down":
            pygame.draw.rect(surf, wonju_dk, (x - 13, y - 29 + by + aL * 0.35, 5, 12), border_radius=2)
            pygame.draw.rect(surf, wonju, (x - 12, y - 28 + by + aL * 0.35, 4, 10), border_radius=2)
            pygame.draw.rect(surf, wonju_dk, (x + 8, y - 29 + by + aR * 0.35, 5, 12), border_radius=2)
            pygame.draw.rect(surf, wonju, (x + 9, y - 28 + by + aR * 0.35, 4, 10), border_radius=2)
            pygame.draw.circle(surf, skin, (int(x - 10), int(y - 16 + by + aL * 0.35)), 3)
            pygame.draw.circle(surf, skin, (int(x + 11), int(y - 16 + by + aR * 0.35)), 3)
        elif direction == "up":
            pygame.draw.rect(surf, wonju, (x - 12, y - 28 + by + aR * 0.3, 5, 9), border_radius=2)
            pygame.draw.rect(surf, wonju, (x + 7, y - 28 + by + aL * 0.3, 5, 9), border_radius=2)
        elif direction == "left":
            pygame.draw.rect(surf, wonju, (x - 14, y - 28 + by, 5, 12 + aL * 0.45), border_radius=2)
            pygame.draw.circle(surf, skin, (int(x - 12), int(y - 15 + by + aL * 0.45)), 3)
            pygame.draw.rect(surf, wonju_dk, (x + 7, y - 27 + by, 4, 8), border_radius=2)
        else:
            pygame.draw.rect(surf, wonju, (x + 9, y - 28 + by, 5, 12 + aR * 0.45), border_radius=2)
            pygame.draw.circle(surf, skin, (int(x + 12), int(y - 15 + by + aR * 0.45)), 3)
            pygame.draw.rect(surf, wonju_dk, (x - 11, y - 27 + by, 4, 8), border_radius=2)

        lift_l = max(0.0, -leg_swing * 0.22) if moving else 0.0
        lift_r = max(0.0, leg_swing * 0.22) if moving else 0.0
        pygame.draw.ellipse(surf, (45, 32, 22), (x - 9, y + 3 - by - lift_l, 8, 5))
        pygame.draw.ellipse(surf, (45, 32, 22), (x + 1, y + 3 - by - lift_r, 8, 5))
    else:
        # Male Gho
        # cape / kabney behind
        cape_w = math.sin(frame * 0.12) * 2.5
        if direction == "down":
            cape = [(x - 10, y - 18 + by), (x - 17 - cape_w, y + 6), (x - 11, y + 8), (x - 5, y - 16 + by)]
        elif direction == "up":
            cape = [(x + 10, y - 18 + by), (x + 17 + cape_w, y + 6), (x + 11, y + 8), (x + 5, y - 16 + by)]
        elif direction == "left":
            cape = [(x + 8, y - 18 + by), (x + 18 + cape_w, y - 2), (x + 14, y + 6), (x + 5, y - 16 + by)]
        else:
            cape = [(x - 8, y - 18 + by), (x - 18 - cape_w, y - 2), (x - 14, y + 6), (x - 5, y - 16 + by)]
        pygame.draw.polygon(surf, darken(sash, 35), cape)
        pygame.draw.polygon(surf, sash, [(p[0]+1, p[1]+1) for p in cape[:3]] + [cape[3]])

        # legs – alternating stride
        if direction in ("left", "right"):
            pygame.draw.rect(surf, (36, 30, 26), (x - 7, y - 4 - by, 6, 10 + leg_swing * 0.55), border_radius=2)
            pygame.draw.rect(surf, (36, 30, 26), (x + 1, y - 4 - by, 6, 10 - leg_swing * 0.55), border_radius=2)
        else:
            # down/up: length change reads as step
            pygame.draw.rect(surf, (36, 30, 26), (x - 7, y - 4 - by, 6, 10 + max(0, -leg_swing * 0.35)), border_radius=2)
            pygame.draw.rect(surf, (36, 30, 26), (x + 1, y - 4 - by, 6, 10 + max(0, leg_swing * 0.35)), border_radius=2)
        # boots with clear foot plant
        lift_l = max(0.0, -leg_swing * 0.28) if moving else 0.0
        lift_r = max(0.0, leg_swing * 0.28) if moving else 0.0
        pygame.draw.rect(surf, (50, 35, 22), (x - 8, y + 4 - by - lift_l, 8, 5), border_radius=2)
        pygame.draw.rect(surf, (50, 35, 22), (x, y + 4 - by - lift_r, 8, 5), border_radius=2)

        # gho body – clear rectangle with folds
        pygame.draw.rect(surf, darken(robe, 40), (x - 12, y - 28 + by, 24, 26), border_radius=4)
        pygame.draw.rect(surf, robe, (x - 10, y - 26 + by, 20, 24), border_radius=4)
        pygame.draw.line(surf, darken(robe, 25), (x - 3, y - 25 + by), (x - 3, y - 4 + by), 1)
        pygame.draw.line(surf, lighten(robe, 20), (x + 3, y - 25 + by), (x + 3, y - 4 + by), 1)

        # sash across chest
        if direction in ("down", "left"):
            pygame.draw.line(surf, darken(sash, 20), (x - 8, y - 22 + by), (x + 8, y - 8 + by), 4)
            pygame.draw.line(surf, sash, (x - 7, y - 21 + by), (x + 7, y - 9 + by), 2)
        else:
            pygame.draw.line(surf, darken(sash, 20), (x + 8, y - 22 + by), (x - 8, y - 8 + by), 4)
            pygame.draw.line(surf, sash, (x + 7, y - 21 + by), (x - 7, y - 9 + by), 2)

        # belt
        pygame.draw.rect(surf, belt_c, (x - 11, y - 12 + by, 22, 4), border_radius=1)
        pygame.draw.rect(surf, C_GOLD, (x - 2, y - 12 + by, 5, 4), border_radius=1)

        # arms – counter-swing to legs
        aL = arm_swing
        aR = -arm_swing
        if direction == "down":
            pygame.draw.rect(surf, darken(robe, 15), (x - 14, y - 23 + by + aL * 0.4, 6, 11), border_radius=2)
            pygame.draw.rect(surf, darken(robe, 15), (x + 8, y - 23 + by + aR * 0.4, 6, 11), border_radius=2)
            pygame.draw.circle(surf, skin, (int(x - 11), int(y - 11 + by + aL * 0.4)), 3)
            pygame.draw.circle(surf, skin, (int(x + 11), int(y - 11 + by + aR * 0.4)), 3)
            # collar
            pygame.draw.rect(surf, (90, 60, 35), (x - 6, y - 25 + by, 12, 8), border_radius=2)
        elif direction == "up":
            pygame.draw.rect(surf, darken(robe, 15), (x - 14, y - 23 + by + aR * 0.35, 6, 9), border_radius=2)
            pygame.draw.rect(surf, darken(robe, 15), (x + 8, y - 23 + by + aL * 0.35, 6, 9), border_radius=2)
        elif direction == "left":
            pygame.draw.rect(surf, darken(robe, 15), (x - 15, y - 23 + by, 6, 11 + aL * 0.5), border_radius=2)
            pygame.draw.circle(surf, skin, (int(x - 13), int(y - 11 + by + aL * 0.5)), 3)
            pygame.draw.rect(surf, darken(robe, 25), (x + 8, y - 22 + by, 5, 8), border_radius=2)
        else:
            pygame.draw.rect(surf, darken(robe, 15), (x + 9, y - 23 + by, 6, 11 + (-arm_swing) * 0.5), border_radius=2)
            pygame.draw.circle(surf, skin, (int(x + 13), int(y - 11 + by + (-arm_swing) * 0.5)), 3)
            pygame.draw.rect(surf, darken(robe, 25), (x - 13, y - 22 + by, 5, 8), border_radius=2)

    # ========== HEAD ==========
    head_y = y - 39 + by
    hr = 10 if is_female else 9
    # neck
    pygame.draw.rect(surf, skin, (x - 3, y - 33 + by, 6, 5))
    # face base
    pygame.draw.circle(surf, darken(skin, 15), (int(x + 1), int(head_y + 1)), hr)
    pygame.draw.circle(surf, skin, (int(x), int(head_y)), hr)
    pygame.draw.circle(surf, lighten(skin, 12), (int(x - 2), int(head_y - 2)), max(3, hr // 2))

    # --- HAIR (always solid, never disappears) ---
    if is_female:
        # Neat hair: fringe, side locks, low bun + gold pin
        bun = (205, 155, 55)
        if direction == "down":
            pygame.draw.ellipse(surf, hair_c, (x - 12, head_y - 13, 24, 15))
            pygame.draw.ellipse(surf, hair_c, (x - 11, head_y - 15, 22, 10))
            pygame.draw.ellipse(surf, hair_c, (x - 14, head_y - 4, 8, 18))
            pygame.draw.ellipse(surf, hair_c, (x + 6, head_y - 4, 8, 18))
            pygame.draw.ellipse(surf, darken(hair_c, 12), (x - 13, head_y + 6, 6, 10))
            pygame.draw.ellipse(surf, darken(hair_c, 12), (x + 7, head_y + 6, 6, 10))
            pygame.draw.ellipse(surf, hair_c, (x - 6, head_y + 4, 12, 10))
            pygame.draw.ellipse(surf, hair_hi, (x - 5, head_y - 11, 10, 5))
            pygame.draw.circle(surf, bun, (int(x), int(head_y + 8)), 2)
        elif direction == "up":
            pygame.draw.ellipse(surf, hair_c, (x - 12, head_y - 14, 24, 16))
            pygame.draw.ellipse(surf, hair_c, (x - 10, head_y - 17, 20, 12))
            pygame.draw.ellipse(surf, hair_c, (x - 7, head_y - 4, 14, 12))
            pygame.draw.ellipse(surf, darken(hair_c, 15), (x - 5, head_y - 2, 10, 8))
            pygame.draw.circle(surf, bun, (int(x), int(head_y - 6)), 2)
            pygame.draw.circle(surf, (195, 70, 85), (int(x), int(head_y - 16)), 2)
        elif direction == "left":
            pygame.draw.ellipse(surf, hair_c, (x - 15, head_y - 13, 16, 22))
            pygame.draw.ellipse(surf, hair_c, (x - 12, head_y - 15, 18, 12))
            pygame.draw.ellipse(surf, hair_c, (x - 14, head_y - 2, 10, 16))
            pygame.draw.ellipse(surf, darken(hair_c, 12), (x + 1, head_y - 5, 7, 14))
            pygame.draw.ellipse(surf, hair_c, (x - 8, head_y + 4, 10, 9))
            pygame.draw.ellipse(surf, hair_hi, (x - 11, head_y - 11, 8, 4))
            pygame.draw.circle(surf, bun, (int(x - 4), int(head_y + 7)), 2)
        else:
            pygame.draw.ellipse(surf, hair_c, (x - 1, head_y - 13, 16, 22))
            pygame.draw.ellipse(surf, hair_c, (x - 6, head_y - 15, 18, 12))
            pygame.draw.ellipse(surf, hair_c, (x + 4, head_y - 2, 10, 16))
            pygame.draw.ellipse(surf, darken(hair_c, 12), (x - 8, head_y - 5, 7, 14))
            pygame.draw.ellipse(surf, hair_c, (x - 2, head_y + 4, 10, 9))
            pygame.draw.ellipse(surf, hair_hi, (x + 3, head_y - 11, 8, 4))
            pygame.draw.circle(surf, bun, (int(x + 4), int(head_y + 7)), 2)
    else:
        if direction == "down":
            pygame.draw.ellipse(surf, hair_c, (x - 12, head_y - 13, 24, 15))
            for oxp in (-8, -4, 0, 4, 8):
                pygame.draw.polygon(surf, hair_c, [
                    (x + oxp, head_y - 5),
                    (x + oxp - 2.5, head_y + 3),
                    (x + oxp + 2.5, head_y + 2),
                ])
            pygame.draw.ellipse(surf, hair_c, (x - 13, head_y - 6, 7, 13))
            pygame.draw.ellipse(surf, hair_c, (x + 6, head_y - 6, 7, 13))
            pygame.draw.ellipse(surf, hair_hi, (x - 6, head_y - 11, 10, 5))
        elif direction == "up":
            pygame.draw.ellipse(surf, hair_c, (x - 12, head_y - 12, 24, 15))
            pygame.draw.ellipse(surf, hair_c, (x - 10, head_y - 16, 20, 12))
            pygame.draw.ellipse(surf, hair_c, (x - 5, head_y - 20, 10, 10))
            pygame.draw.circle(surf, (190, 55, 70), (int(x), int(head_y - 14)), 3)
        elif direction == "left":
            pygame.draw.ellipse(surf, hair_c, (x - 14, head_y - 13, 16, 20))
            pygame.draw.ellipse(surf, hair_c, (x - 12, head_y - 15, 18, 12))
            pygame.draw.ellipse(surf, hair_c, (x - 8, head_y - 9, 12, 9))
            pygame.draw.ellipse(surf, darken(hair_c, 12), (x + 1, head_y - 9, 8, 12))
            pygame.draw.ellipse(surf, hair_c, (x - 11, head_y - 1, 5, 9))
            pygame.draw.ellipse(surf, hair_hi, (x - 10, head_y - 12, 7, 4))
        else:  # right
            pygame.draw.ellipse(surf, hair_c, (x - 2, head_y - 13, 16, 20))
            pygame.draw.ellipse(surf, hair_c, (x - 6, head_y - 15, 18, 12))
            pygame.draw.ellipse(surf, hair_c, (x - 4, head_y - 9, 12, 9))
            pygame.draw.ellipse(surf, darken(hair_c, 12), (x - 9, head_y - 9, 8, 12))
            pygame.draw.ellipse(surf, hair_c, (x + 6, head_y - 1, 5, 9))
            pygame.draw.ellipse(surf, hair_hi, (x + 3, head_y - 12, 7, 4))

    # --- FACE ---
    if direction == "down":
        pygame.draw.circle(surf, (255, 165, 155), (int(x - 5), int(head_y + 2)), 2)
        pygame.draw.circle(surf, (255, 165, 155), (int(x + 5), int(head_y + 2)), 2)
        # eyes (clearer for female adventurer)
        eye_iris = (55, 40, 95) if is_female else (40, 35, 85)
        pygame.draw.ellipse(surf, (255, 255, 255), (x - 7, head_y - 3, 6, 6))
        pygame.draw.ellipse(surf, (255, 255, 255), (x + 1, head_y - 3, 6, 6))
        pygame.draw.ellipse(surf, eye_iris, (x - 6, head_y - 2, 4, 5))
        pygame.draw.ellipse(surf, eye_iris, (x + 2, head_y - 2, 4, 5))
        pygame.draw.circle(surf, (15, 10, 25), (int(x - 4), int(head_y + 1)), 2)
        pygame.draw.circle(surf, (15, 10, 25), (int(x + 4), int(head_y + 1)), 2)
        pygame.draw.circle(surf, (255, 255, 255), (int(x - 5), int(head_y - 1)), 1)
        pygame.draw.circle(surf, (255, 255, 255), (int(x + 3), int(head_y - 1)), 1)
        if is_female:
            pygame.draw.line(surf, (50, 35, 40), (x - 7, head_y - 4), (x - 2, head_y - 5), 1)
            pygame.draw.line(surf, (50, 35, 40), (x + 2, head_y - 5), (x + 7, head_y - 4), 1)
        pygame.draw.arc(surf, (180, 100, 100), (x - 3, head_y + 3, 7, 3), 0, math.pi, 1)
        pygame.draw.line(surf, hair_c, (x - 7, head_y - 5), (x - 2, head_y - 6), 1)
        pygame.draw.line(surf, hair_c, (x + 2, head_y - 6), (x + 7, head_y - 5), 1)
    elif direction == "left":
        pygame.draw.circle(surf, (255, 165, 155), (int(x - 4), int(head_y + 2)), 2)
        pygame.draw.ellipse(surf, (255, 255, 255), (x - 8, head_y - 3, 5, 6))
        pygame.draw.ellipse(surf, (40, 35, 85), (x - 7, head_y - 2, 4, 5))
        pygame.draw.circle(surf, (15, 10, 25), (int(x - 5), int(head_y + 1)), 2)
        pygame.draw.circle(surf, (255, 255, 255), (int(x - 6), int(head_y - 1)), 1)
        pygame.draw.line(surf, hair_c, (x - 8, head_y - 5), (x - 3, head_y - 6), 1)
        pygame.draw.arc(surf, (180, 100, 100), (x - 6, head_y + 3, 5, 3), 0, math.pi, 1)
    elif direction == "right":
        pygame.draw.circle(surf, (255, 165, 155), (int(x + 4), int(head_y + 2)), 2)
        pygame.draw.ellipse(surf, (255, 255, 255), (x + 3, head_y - 3, 5, 6))
        pygame.draw.ellipse(surf, (40, 35, 85), (x + 3, head_y - 2, 4, 5))
        pygame.draw.circle(surf, (15, 10, 25), (int(x + 5), int(head_y + 1)), 2)
        pygame.draw.circle(surf, (255, 255, 255), (int(x + 4), int(head_y - 1)), 1)
        pygame.draw.line(surf, hair_c, (x + 3, head_y - 6), (x + 8, head_y - 5), 1)
        pygame.draw.arc(surf, (180, 100, 100), (x + 1, head_y + 3, 5, 3), 0, math.pi, 1)
    # up: ears only
    if direction == "up":
        pygame.draw.circle(surf, skin, (int(x - 8), int(head_y + 1)), 2)
        pygame.draw.circle(surf, skin, (int(x + 8), int(head_y + 1)), 2)


# ================= GAME =================
class Game:
    def __init__(self):
        pygame.init()
        try:
            self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.FULLSCREEN, vsync=1)
        except TypeError:
            try:
                self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.FULLSCREEN)
            except Exception:
                self.screen = pygame.display.set_mode((W, H))
        except Exception:
            # Windowed fallback if fullscreen fails
            try:
                self.screen = pygame.display.set_mode((W, H), pygame.SCALED)
            except Exception:
                self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Brain Trek - Highland Expedition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.small = pygame.font.SysFont("Arial", 15, bold=True)
        self.title_f = pygame.font.SysFont("Arial", 46, bold=True)
        self.map_title_f = pygame.font.SysFont("Arial", 55, bold=True)
        self.map_level_f = pygame.font.SysFont("Arial", 27, bold=True)
        self.map_small_f = pygame.font.SysFont("Arial", 20, bold=True)
        self.audio = Audio()
        # Certificate drawn in code; image.png = creator signature (optional)
        self.cert_image = None
        def _load_signature(filename, max_dim=400):
            for base in (
                IMAGE_DIR,
                os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".",
                os.getcwd(),
                "/home/workdir/artifacts",
                "/home/workdir/attachments",
                ".",
            ):
                p = os.path.join(base, filename)
                try:
                    if not os.path.isfile(p):
                        continue
                    raw = pygame.image.load(p).convert_alpha()
                    sw, sh = raw.get_width(), raw.get_height()
                    if max(sw, sh) > max_dim:
                        sc = max_dim / float(max(sw, sh))
                        raw = pygame.transform.smoothscale(
                            raw, (max(1, int(sw * sc)), max(1, int(sh * sc)))
                        ).convert_alpha()
                    try:
                        for yy in range(raw.get_height()):
                            for xx in range(raw.get_width()):
                                c = raw.get_at((xx, yy))
                                if c.r >= 245 and c.g >= 245 and c.b >= 245:
                                    raw.set_at((xx, yy), (255, 255, 255, 0))
                    except Exception:
                        pass
                    return raw
                except Exception:
                    continue
            return None

        # image.png = Game Creator signature · image4.png = Adventure Guide signature
        self.cert_signature = _load_signature("image.png")
        self.cert_guide_signature = _load_signature("image4.png")

        def _load_logo(filename, max_dim=200):
            """Load badge logo; strip pure white only; support png/jpg."""
            names = [filename]
            if filename.lower().endswith(".png"):
                names.append(filename[:-4] + ".jpg")
                names.append(filename[:-4] + ".jpeg")
            bases = [
                IMAGE_DIR,
                os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".",
                os.getcwd(),
                "/home/workdir/artifacts",
                "/home/workdir/attachments",
                ".",
            ]
            for name in names:
                for base in bases:
                    p = os.path.join(base, name)
                    try:
                        if not os.path.isfile(p):
                            continue
                        raw = pygame.image.load(p).convert_alpha()
                        sw, sh = raw.get_width(), raw.get_height()
                        if max(sw, sh) > max_dim:
                            sc = max_dim / float(max(sw, sh))
                            raw = pygame.transform.smoothscale(
                                raw, (max(1, int(sw * sc)), max(1, int(sh * sc)))
                            ).convert_alpha()
                        # Only punch pure white corners (keep soft art intact)
                        try:
                            for yy in range(raw.get_height()):
                                for xx in range(raw.get_width()):
                                    c = raw.get_at((xx, yy))
                                    if c.r >= 250 and c.g >= 250 and c.b >= 250 and c.a > 0:
                                        raw.set_at((xx, yy), (255, 255, 255, 0))
                        except Exception:
                            pass
                        return raw
                    except Exception:
                        continue
            return None

        self.cert_logo = _load_logo("image5.png", max_dim=200)
        self.title_bg = None
        self.title_bg_scaled = None
        self.cert_name = ""
        self.cert_grade = ""
        self.cert_school = ""
        self.cert_country = ""
        self.cert_date = ""
        self.cert_id = ""
        self.cert_focus = "name"
        self.cert_submitted = False
        # Title menu background art (image2.png home screen)
        for _tp in (
            os.path.join(IMAGE_DIR, "image2.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ".", "image2.png"),
            os.path.join(os.getcwd(), "image2.png"),
            "/home/workdir/artifacts/image2.png",
            "/home/workdir/attachments/image2.png",
            "/home/workdir/artifacts/title_bg.png",
            "image2.png",
            "title_bg.png",
        ):
            try:
                if os.path.isfile(_tp):
                    self.title_bg = pygame.image.load(_tp).convert()
                    self.title_bg_scaled = pygame.transform.smoothscale(self.title_bg, (W, H))
                    break
            except Exception:
                pass
        
        # Persistent Data
        self.level_stars = [0] * NUM_LEVELS
        self.level_unlocked = [False] * NUM_LEVELS
        self.level_unlocked[0] = True
        self.ach = set()
        self.gold = 0
        self.resources = {k: 0 for k in RESOURCE_TYPES}  # gems, scrolls, relics, nature, artifacts
        self.hint_charges = 0          # bought quiz hints (persistent)
        self.free_hints_left = 2      # first 2 H uses free (persistent across levels)
        self.max_lives = 8
        self.perm_speed = False
        self.inventory = []
        self.purchases = 0
        self.skins_owned = ["classic"]
        self.skin = "classic"
        self.gender = "male"   # "male" or "female" (female wears Kira)
        self.total_correct = 0
        self.total_chests = 0
        self.secret_chests_found = 0
        self.quest_env = 0
        
        # Level-specific Data
        self.biome = 0
        self.weather = "sunshine"
        self.current_level = 1
        self.used_questions_global = set()
        
        # === INTRO (image3.png + poem on four sides) ===
        self.state = "INTRO"
        self.intro_start = pygame.time.get_ticks()
        self.intro_phase = 0
        self.intro_skip = False
        self.intro_done = False
        self.intro_duration = 17.0
        self.intro_bg = None
        self.intro_bg_scaled = None
        for _ip in (
            os.path.join(IMAGE_DIR, "image3.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".", "image3.png"),
            os.path.join(os.getcwd(), "image3.png"),
            "/home/workdir/artifacts/image3.png",
            "/home/workdir/attachments/image3.png",
            "image3.png",
        ):
            try:
                if os.path.isfile(_ip):
                    self.intro_bg = pygame.image.load(_ip).convert()
                    self.intro_bg_scaled = pygame.transform.smoothscale(self.intro_bg, (W, H))
                    break
            except Exception:
                pass
        
        self.bridges = []
        self.build_water(); self.build_path(); self.build_world()
        self.build_terrain(); self.build_minimap_base(); self.build_light()
        
        # Hitboxes match painted title buttons (START / HOW TO / CUSTOMIZE)
        # Tuned for image2.png layout at 1100x700
        self.title_play = pygame.Rect(W // 2 - 175, 405, 350, 58)
        self.title_howto = pygame.Rect(W // 2 - 175, 475, 350, 54)
        self.title_custom = pygame.Rect(W // 2 - 175, 540, 350, 54)
        self.map_shop = pygame.Rect(MAP_W - 180, MAP_H - 70, 160, 46)
        # START button — bottom-left, clear of level nodes
        self.map_start_btn = pygame.Rect(MAP_W - 360, MAP_H - 78, 150, 46)
        self.map_selected_level = None  # chosen on map before START
        self.map_custom = pygame.Rect(MAP_W - 360, MAP_H - 70, 160, 46)
        self.p_resume = pygame.Rect(370, 180, 360, 42)
        self.p_shop = pygame.Rect(370, 230, 360, 42)
        self.p_save = pygame.Rect(370, 280, 360, 42)
        self.p_mute = pygame.Rect(370, 330, 360, 42)
        self.p_custom = pygame.Rect(370, 380, 360, 42)
        self.p_map = pygame.Rect(370, 430, 360, 42)
        self.sh_back = pygame.Rect(40, 620, 160, 46)
        self.lc_next = pygame.Rect(W//2-260, 498, 520, 46)
        self.lc_map = pygame.Rect(W//2-260, 552, 255, 46)
        self.lc_retry = pygame.Rect(W//2+5, 552, 255, 46)
        self.gc_play = pygame.Rect(W//2-260, 550, 520, 46)
        
        self.quiz_rects = []; self.shop_rects = []; self.shop_items = []
        self.dialog = None; self.dialog_lines = []
        self.reset_run()
        try:
            self.load_progress()
        except Exception:
            pass

    # ... build methods ...
    def build_water(self):
        ctrl = [(-60,800,58),(140,812,52),(320,782,50),(470,772,48),(600,766,46),(660,762,47),
                (760,748,64),(880,724,96),(1020,706,128),(1160,700,150),(1320,706,128),
                (1480,722,96),(1650,752,70),(1820,782,58),(2060,800,56)]
        pts = []
        for i in range(len(ctrl) - 1):
            x1, y1, r1 = ctrl[i]; x2, y2, r2 = ctrl[i + 1]
            steps = max(2, int(math.hypot(x2 - x1, y2 - y1) / 10))
            for s in range(steps):
                t = s / steps
                x = lerp(x1, x2, t); y = lerp(y1, y2, t); r = lerp(r1, r2, t)
                y += math.sin(x * .013) * 8 + math.sin(x * .031) * 5
                r += math.sin(x * .021) * 6
                pts.append((x, y, r))
        self.water = pts

    def in_water(self, x, y, margin=0):
        for wx, wy, wr in self.water:
            dx = x - wx
            if dx > 200 or dx < -200: continue
            dy = y - wy
            if dx * dx + dy * dy < (wr - margin) ** 2: return True
        return False

    def nearest_water(self, x, y):
        bi, bd = 0, 1e18
        for i, (wx, wy, wr) in enumerate(self.water):
            d = (x - wx) ** 2 + (y - wy) ** 2
            if d < bd: bd, bi = d, i
        return bi, math.sqrt(bd)

    def on_bridge(self, x, y):
        for br in getattr(self, "bridges", []) or []:
            # Slight inflate so edges of the deck are still walkable
            if br.inflate(8, 8).collidepoint(int(x), int(y)):
                return True
        return False

    def dist_to_path(self, x, y):
        if not getattr(self, "path_pts", None):
            return 9999.0
        best = 1e18
        for px, py in self.path_pts:
            d = (x - px) ** 2 + (y - py) ** 2
            if d < best: best = d
        return math.sqrt(best)

    def build_path(self, theme=None):
        # Default highland trail
        ctrl = [(430,1050),(520,940),(600,880),(660,862),(660,662),(700,560),(900,520),
                (1200,520),(1500,600),(1700,700),(1780,760),(1830,640),(1878,530)]
        if theme == "village":
            # Wider village loop with southern market spur
            ctrl = [(430,1050),(500,980),(580,920),(650,860),(660,700),(720,600),(900,540),
                    (1100,520),(1300,560),(1500,620),(1650,720),(1750,800),(1850,720),(1900,560)]
        elif theme == "mountain":
            # High northern ridge path
            ctrl = [(400,900),(520,700),(640,500),(780,380),(1000,320),(1200,300),
                    (1450,340),(1650,420),(1800,500),(1900,580),(1950,500)]
        elif theme == "desert":
            # Eastern dry-road
            ctrl = [(500,1000),(700,950),(900,900),(1100,850),(1300,800),(1500,750),
                    (1700,700),(1850,650),(2000,600),(2100,550)]
        elif theme == "temple":
            # Sacred approach toward northern shrine
            ctrl = [(450,1100),(550,1000),(650,900),(750,780),(850,650),(950,520),
                    (1100,400),(1300,350),(1500,320),(1700,300),(1850,340)]
        self.path_pts = []
        for i in range(len(ctrl) - 1):
            x1, y1 = ctrl[i]; x2, y2 = ctrl[i + 1]
            n = int(math.hypot(x2 - x1, y2 - y1) / 14) + 1
            for s in range(n):
                t = s / max(1, n - 1)
                self.path_pts.append((lerp(x1, x2, t), lerp(y1, y2, t)))
        self.POIS = [(430,1050),(1000,902),(596,900),(1880,500),(250,220),(1720,1120),(560,940),(760,640),(520,1150)]
        if self.path_pts:
            self.POIS = list(self.POIS) + [self.path_pts[0], self.path_pts[len(self.path_pts)//2], self.path_pts[-1]]

    def clear_of_pois(self, x, y, d=70):
        return all(math.hypot(x - px, y - py) > d for px, py in self.POIS)

    def build_world(self):
        rnd = random.Random(777)
        self.colliders = []; self.trees = []; self.rocks = []; self.reeds = []; self.shore_rocks = []
        self.flowers = []; self.mushrooms = []; self.logs = []; self.leaves_sp = []
        self.thorns = []  # removed – dark green damage circles that looked like ponds
        # Dense natural forest – many trees scattered (no big clusters)
        self.place_trees_natural(160, rnd, theme="forest")
        for _ in range(18):
            x, y = rnd.uniform(100, WW-100), rnd.uniform(100, WH-100)
            if not self.in_water(x, y, -30) and self.clear_of_pois(x, y, 45):
                r = rnd.uniform(6, 22); self.rocks.append((x, y, r))
                if r > 10: self.colliders.append((x, y, r*.8))
        # small path-side stones for natural trail edges
        for _ in range(14):
            if not self.path_pts: break
            p = rnd.choice(self.path_pts)
            a = rnd.uniform(0, 6.28)
            x = p[0] + math.cos(a) * rnd.uniform(18, 36)
            y = p[1] + math.sin(a) * rnd.uniform(14, 28)
            if not self.in_water(x, y, -10) and 40 < x < WW-40:
                self.rocks.append((x, y, rnd.uniform(4, 9)))
        for i in range(0, len(self.water), 5):
            wx, wy, wr = self.water[i]
            if not (BRIDGE.left - 40 < wx < BRIDGE.right + 40):
                a = hash01(i) * 6.28
                ox, oy = math.cos(a) * (wr + 10), math.sin(a) * (wr + 10) * .6
                if hash01(i*3) > .6: self.shore_rocks.append((wx + ox, wy + oy, 3 + hash01(i*7) * 4))
                if hash01(i*5) > .45: self.reeds.append((wx + ox*.8, wy + oy*.8))
        # Colorful flower meadows scattered across the map
        flower_cols = [
            (255, 120, 140), (255, 200, 80), (255, 255, 120), (200, 140, 255),
            (255, 160, 200), (120, 200, 255), (255, 100, 80), (180, 255, 160),
            (255, 220, 100), (230, 180, 255), (255, 180, 150), (140, 220, 180),
        ]
        # Sparse natural patches – not crowded
        meadow_centers = [
            (700,1100),(1100,950),(500,700),(1300,300),(1600,1000),(300,600),
            (400,1400),(900,1600),(1500,500),(1800,1400),(250,300),(800,800),
            (430,1080),(520,1020),
        ]
        for cx, cy in meadow_centers:
            dens = 4 if abs(cx - 430) < 120 and abs(cy - 1050) < 150 else 3
            for _ in range(dens):
                x, y = cx + rnd.gauss(0, 42), cy + rnd.gauss(0, 32)
                if not self.in_water(x, y, -15) and 40 < x < WW-40 and 40 < y < WH-40:
                    self.flowers.append((x, y, rnd.choice(flower_cols)))
        # Light scatter of wildflowers across the map
        for _ in range(28):
            x, y = rnd.uniform(50, WW-50), rnd.uniform(50, WH-50)
            if not self.in_water(x, y, -12) and self.dist_to_path(x, y) > 20:
                self.flowers.append((x, y, rnd.choice(flower_cols)))
        for tr in self.trees:
            tx, ty = tr[0], tr[1]
            if hash01(tx) > .45: self.mushrooms.append((tx + rnd.uniform(-20, 20), ty + rnd.uniform(8, 20)))
            self.leaves_sp.append((tx + rnd.gauss(0, 18), ty + rnd.gauss(0, 14)))
        for x, y, a in [(350,420,.4),(1450,1120,1.2),(950,350,2.0),(620,880,0.9),(1700,500,1.5),(280,700,2.4),(1100,1400,0.6)]:
            if not self.in_water(x, y, -20):
                self.logs.append((x, y, a)); self.colliders.append((x, y, 16))
        self.bushes = []
        for _ in range(48):
            x, y = rnd.uniform(50, WW-50), rnd.uniform(50, WH-50)
            if not self.in_water(x, y, -20) and self.dist_to_path(x, y) > 28 and self.clear_of_pois(x, y, 36):
                self.bushes.append((x, y, rnd.uniform(.7, 1.4)))
        # Extra bushes framing the start area
        for _ in range(18):
            a = rnd.uniform(0, 6.28)
            d = rnd.uniform(70, 180)
            x, y = 430 + math.cos(a) * d, 1050 + math.sin(a) * d * 0.9
            if not self.in_water(x, y, -20) and self.dist_to_path(x, y) > 20 and self.clear_of_pois(x, y, 30):
                self.bushes.append((x, y, rnd.uniform(0.9, 1.5)))
        self.ferns = []
        for _ in range(55):
            x, y = rnd.uniform(50, WW-50), rnd.uniform(50, WH-50)
            if not self.in_water(x, y, -10) and self.dist_to_path(x, y) > 22:
                self.ferns.append((x, y, rnd.uniform(.7, 1.3)))
        for _ in range(20):
            a = rnd.uniform(0, 6.28)
            d = rnd.uniform(50, 140)
            x, y = 430 + math.cos(a) * d, 1050 + math.sin(a) * d * 0.85
            if not self.in_water(x, y, -10) and self.dist_to_path(x, y) > 14:
                self.ferns.append((x, y, rnd.uniform(0.8, 1.4)))
        self.grass_tufts = []
        for _ in range(140):
            x, y = rnd.uniform(40, WW-40), rnd.uniform(40, WH-40)
            if not self.in_water(x, y, -6) and self.dist_to_path(x, y) > 18:
                self.grass_tufts.append((x, y, rnd.uniform(.6, 1.4), rnd.uniform(0, 6.28)))
        self.lily = []
        for i in range(6, len(self.water)-6, 9):
            wx, wy, wr = self.water[i]
            if wr > 95 and hash01(i*11) > .72 and not (BRIDGE.left-60 < wx < BRIDGE.right+60):
                a = hash01(i*5) * 6.28
                self.lily.append((wx + math.cos(a)*wr*.4, wy + math.sin(a)*wr*.3, rnd.uniform(.8, 1.2)))
        self.coins = []
        while len(self.coins) < 12:
            x, y = rnd.uniform(80, WW-80), rnd.uniform(80, WH-80)
            if not self.in_water(x, y, -10) and not self.on_bridge(x, y) and self.clear_of_pois(x, y, 40):
                self.coins.append([x, y])
        self.trash = [{"x": x, "y": y, "got": False} for x, y in [(700,980),(900,560),(1250,900),(520,700),(1500,1050)]]
        self.saplings = []
        self.pillars = []
        prnd = random.Random(31)
        for _ in range(6):
            x, y = prnd.uniform(200, WW-200), prnd.uniform(200, WH-200)
            if not self.in_water(x, y, -30) and self.clear_of_pois(x, y, 75) and self.dist_to_path(x, y) > 55:
                self.pillars.append((x, y, prnd.uniform(0.75, 1.35)))
        # === Bhutanese decorative elements ===
        self.houses = []          # list of dicts: x,y,s,owner,is_player
        self.prayer_flags = []
        self.chortens = []
        hrnd = random.Random(88)
        # Prayer flag poles / lines – scatter along ridges and near path
        for _ in range(8):
            x, y = hrnd.uniform(100, WW-100), hrnd.uniform(100, WH-100)
            if not self.in_water(x, y, -20) and self.clear_of_pois(x, y, 45):
                self.prayer_flags.append((x, y, hrnd.uniform(0.8, 1.35), hrnd.randint(4, 8)))
        # a few flags near the starting village for atmosphere
        for ox, oy in [(-80, -40), (90, 30), (-40, 90)]:
            self.prayer_flags.append((430 + ox, 1050 + oy, 1.1, 6))
        # Chortens / stupas as exploration landmarks
        for _ in range(5):
            x, y = hrnd.uniform(180, WW-180), hrnd.uniform(180, WH-180)
            if not self.in_water(x, y, -30) and self.clear_of_pois(x, y, 65) and self.dist_to_path(x, y) > 50:
                self.chortens.append((x, y, hrnd.uniform(0.85, 1.35)))
        self.geysers = [(900, 400), (1500, 500), (700, 1200), (1600, 1200)]
        self.snowp = []
        srnd = random.Random(77)
        for _ in range(10):
            self.snowp.append((srnd.uniform(150, WW-150), srnd.uniform(150, WH-150), srnd.uniform(60, 110)))
        self.landmarks = [
            {"kind": "spring", "x": 260, "y": 620, "used": False},
            {"kind": "statue", "x": 1200, "y": 300, "used": False},
            {"kind": "spring", "x": 1800, "y": 900, "used": False},
            {"kind": "statue", "x": 600, "y": 400, "used": False},
            {"kind": "spring", "x": 1400, "y": 1300, "used": False},
        ]
        self.runes = []
        for _ in range(3):
            x, y = rnd.uniform(100, WW-100), rnd.uniform(100, WH-100)
            if not self.in_water(x, y, -20) and self.clear_of_pois(x, y, 60):
                self.runes.append({"x": x, "y": y, "used": False})
        self.npcs = [
            {"x": 430.0, "y": 1020.0, "kind": "guide", "name": "Guide Karma", "home": (430, 1020), "radius": 120, "speed": 0.85, "work": "gather", "work_name": "reading a map", "robe": (90, 90, 120), "headgear": "hat"},
            {"x": 1500.0, "y": 360.0, "kind": "merchant", "name": "Merchant Dawa", "home": (1500, 360), "radius": 230, "speed": 0.95, "work": "gather", "work_name": "gathering herbs", "robe": (150, 64, 58), "headgear": "hat"},
            {"x": 560.0, "y": 940.0, "kind": "keeper", "name": "Keeper Pema", "home": (560, 900), "radius": 200, "speed": 0.9, "work": "chop", "work_name": "chopping wood", "robe": (120, 92, 60), "headgear": "hood"},
            {"x": 430.0, "y": 1230.0, "kind": "villager", "name": "Villager Sonam", "home": (430, 1230), "radius": 240, "speed": 1.0, "work": "farm", "work_name": "tending the flowers", "robe": (92, 124, 72), "headgear": "band"},
            {"x": 1200.0, "y": 920.0, "kind": "historian", "name": "Historian Dorji", "home": (1200, 920), "radius": 150, "speed": 0.75, "work": "gather", "work_name": "studying ruins", "robe": (100, 80, 120), "headgear": "hat"},
            {"x": 800.0, "y": 1100.0, "kind": "environmentalist", "name": "Eco Tshering", "home": (800, 1100), "radius": 180, "speed": 0.9, "work": "gather", "work_name": "checking soil", "robe": (60, 120, 90), "headgear": "band"},
        ]
        for n in self.npcs:
            n.update({"state": "IDLE", "timer": random.uniform(0.6, 1.6), "tx": n["x"], "ty": n["y"], "face": 1, "phase": 0.0, "paused_state": None})
        # Houses are NOT placed in early forest levels.
        # They appear later via place_houses_for_level() when the biome supports homes.
        self.houses = []
        self.player_house = None
        self.near_house = None
        self.can_enter_house = False
        self.near_npc = None
        self.house_colliders = []  # dynamic colliders added per level
        self.rabbits = []
        for hx, hy in [(700,1200),(300,800),(1200,1100),(1500,900)]:
            self.rabbits.append({"x": float(hx), "y": float(hy), "hx": hx, "hy": hy, "t": rnd.uniform(0,6), "hop": 0, "a": 0.0, "zone": pygame.Rect(hx-160, hy-120, 320, 240)})
        self.birds = []
        for i in range(6):
            hx, hy = rnd.choice(self.trees)[:2] if self.trees else (600, 600)
            self.birds.append({"x": float(hx), "y": float(hy), "hx": hx, "hy": hy, "st": "perch", "vx": 0, "vy": 0, "t": rnd.uniform(0, 4), "perch": (hx, hy), "wing": 0.0})
        self.worms = []
        for _ in range(7):
            hx, hy = rnd.uniform(120, WW-120), rnd.uniform(120, WH-120)
            if not self.in_water(hx, hy, -10):
                self.worms.append({"x": hx, "y": hy, "a": rnd.uniform(0, 6.28), "sp": rnd.uniform(8, 16), "ph": rnd.uniform(0, 6.28), "bur": 0.0, "seg": []})
        self.bugs = []
        for _ in range(9):
            hx, hy = rnd.uniform(150, WW-150), rnd.uniform(150, WH-150)
            if not self.in_water(hx, hy, -10):
                self.bugs.append({"x": hx, "y": hy, "a": rnd.uniform(0, 6.28), "sp": rnd.uniform(20, 40), "ph": rnd.uniform(0, 6.28), "turn": 0})
        self.butterflies = []
        bf_cols = [
            (255, 180, 60), (255, 120, 160), (180, 140, 255), (120, 200, 255),
            (255, 220, 100), (255, 100, 100), (200, 255, 160), (255, 160, 220),
            (255, 200, 140), (160, 180, 255),
        ]
        # denser butterflies from flower patches + extras
        for fx, fy, c in self.flowers[::3]:
            self.butterflies.append({
                "x": fx, "y": fy, "hx": fx, "hy": fy,
                "p": rnd.uniform(0, 6.28), "c": rnd.choice(bf_cols),
                "sz": rnd.uniform(0.7, 1.3),
            })
        for _ in range(55):
            hx = rnd.uniform(80, WW - 80)
            hy = rnd.uniform(80, WH - 80)
            if not self.in_water(hx, hy, -10):
                self.butterflies.append({
                    "x": hx, "y": hy, "hx": hx, "hy": hy,
                    "p": rnd.uniform(0, 6.28), "c": rnd.choice(bf_cols),
                    "sz": rnd.uniform(0.7, 1.3),
                })
        self.leaves = []
        for _ in range(45):
            self.leaves.append({"x": random.randint(0, W), "y": random.randint(0, H), "speed": random.uniform(0.8, 1.8), "sway": random.uniform(0, 6.28), "color": random.choice([(235,210,140),(240,220,220),(200,190,230),(180,220,140)])})
        self.rain = [{"x": random.randint(0, W), "y": random.randint(0, H), "s": random.uniform(4, 7)} for _ in range(60)]
        self.fireflies = [{"x": random.randint(0, W), "y": random.randint(0, H), "p": random.uniform(0, 6)} for _ in range(14)]
        self.fish = [{"t": rnd.uniform(10, len(self.water)-10), "lat": rnd.uniform(-.5,.5), "sp": rnd.uniform(.02,.05) * rnd.choice([1,-1]), "ph": rnd.uniform(0,6)} for _ in range(7)]
        self.ducks = [{"t": 60 + i*8, "lat": .2, "sp": .012, "ph": i*2} for i in range(2)]
        self.float_leaves = [{"t": rnd.uniform(10, len(self.water)-10), "lat": rnd.uniform(-.6,.6), "sp": .015} for _ in range(6)]
        self.base_colliders = list(self.colliders)
        self.spawn_enemies(1)
        self.ripples = []; self.parts = []

    def spawn_enemies(self, lvl):
        self.enemies = []
        base_crabs = [(500.0, 855.0, pygame.Rect(250, 825, 1200, 80)), (1100.0, 860.0, pygame.Rect(250, 825, 1200, 80)), (1000.0, 615.0, pygame.Rect(780, 590, 700, 60))]
        for x, y, z in base_crabs:
            self.enemies.append({"type": "CRAB", "x": x, "y": y, "hp": 2, "a": random.uniform(0, 6.28), "t": 0, "zone": z, "sp": .45, "leg": 0.0, "mv": 0.6, "wait": 0.0, "lunge": 0.0})
        for sx, sy, z in [(1700.0, 560.0, pygame.Rect(1520, 430, 430, 250)), (380.0, 330.0, pygame.Rect(180, 180, 420, 320))]:
            self.enemies.append({"type": "SNAKE", "x": sx, "y": sy, "hp": 1, "a": random.uniform(0, 6.28), "t": 0, "zone": z, "sp": .9, "ph": 0.0, "seg": [], "lunge": 0.0})
        rnd = random.Random(555 + lvl)
        zones = [pygame.Rect(1520, 430, 430, 250), pygame.Rect(180, 180, 420, 320), pygame.Rect(250, 825, 1200, 80), pygame.Rect(780, 590, 700, 60), pygame.Rect(600, 1000, 800, 350)]
        for k in range((lvl - 1) // 3):
            z = rnd.choice(zones)
            typ = "SNAKE" if k % 2 == 0 else "CRAB"
            e = {"type": typ, "x": float(rnd.uniform(z.x+30, z.x+z.w-30)), "y": float(rnd.uniform(z.y+20, z.y+z.h-20)), "hp": 1 if typ == "SNAKE" else 2, "a": rnd.uniform(0, 6.28), "t": 0, "zone": z, "sp": .9 if typ == "SNAKE" else .45, "lunge": 0.0}
            if typ == "CRAB": e.update({"leg": 0.0, "mv": 0.6, "wait": 0.0})
            else: e.update({"ph": 0.0, "seg": []})
            self.enemies.append(e)

    def try_tree(self, x, y, rnd, big, min_tree_sep=28, path_clear=52):
        """Place one tree if spacing/path/water rules allow. Returns True if placed."""
        x = clamp(x, 60, WW-60); y = clamp(y, 60, WH-60)
        # Clear path corridor and water / bridges / POIs
        if (self.in_water(x, y, -34) or self.dist_to_path(x, y) < path_clear
                or not self.clear_of_pois(x, y)):
            return False
        for br in getattr(self, "bridges", []) or []:
            if br.inflate(48, 48).collidepoint(x, y):
                return False
        # Minimum spacing vs existing trees (scaled a bit by size later)
        for tr in self.trees:
            dx, dy = x - tr[0], y - tr[1]
            need = min_tree_sep + (tr[2] + (1.2 if big else 0.7)) * 6
            if dx * dx + dy * dy < need * need:
                return False
        preferred = BIOMES[getattr(self, "biome", 0)].get("tree_type", "pine")
        pool = {
            "pine":  ["pine", "pine", "tall_pine", "cedar", "oak", "round", "bushy"],
            "birch": ["birch", "birch", "round", "oak", "pine", "bushy"],
            "oak":   ["oak", "oak", "round", "bushy", "pine", "birch", "cedar"],
        }.get(preferred, ["pine", "oak", "round", "birch", "cedar", "bushy"])
        kind = rnd.choice(pool)
        # Varied sizes: few giants, many medium, some small saplings
        roll = rnd.random()
        if big or roll > 0.82:
            s = rnd.uniform(1.15, 1.85)
        elif roll < 0.22:
            s = rnd.uniform(0.45, 0.75)
        else:
            s = rnd.uniform(0.75, 1.2)
        shape = rnd.uniform(0.0, 1.0)
        self.trees.append((x, y, s, kind, shape))
        trunk_r = 3.5 * s if kind in ("pine", "tall_pine", "cedar", "birch") else 4.2 * s
        self.colliders.append((x, y, trunk_r))
        return True

    def place_trees_natural(self, count, rnd, theme="forest"):
        """Place exactly `count` trees: dense groves off-path, clear corridors, open gaps."""
        if count <= 0:
            return
        # More grove centers so trees cover the whole map (not just a few clumps)
        n_groves = max(6, min(18, count // 12))
        groves = []
        tries = 0
        while len(groves) < n_groves and tries < 600:
            tries += 1
            gx = rnd.uniform(120, WW - 120)
            gy = rnd.uniform(120, WH - 120)
            if self.in_water(gx, gy, -40):
                continue
            if self.dist_to_path(gx, gy) < 70:
                continue
            if any((gx - ox) ** 2 + (gy - oy) ** 2 < 130 ** 2 for ox, oy, *_ in groves):
                continue
            groves.append((gx, gy, rnd.uniform(60, 120)))
        if not groves:
            groves = [(WW * 0.2, WH * 0.25, 110), (WW * 0.5, WH * 0.2, 100),
                      (WW * 0.8, WH * 0.3, 110), (WW * 0.25, WH * 0.7, 100),
                      (WW * 0.55, WH * 0.75, 105), (WW * 0.8, WH * 0.7, 100)]

        # Balanced: enough scatter to fill empty areas, groves for natural clusters
        if theme == "forest":
            grove_share = 0.55
            path_clear = 52
            sep_dense, sep_open = 20, 36
        elif theme in ("village", "city"):
            grove_share = 0.40
            path_clear = 58
            sep_dense, sep_open = 26, 42
        elif theme == "mountain":
            grove_share = 0.48
            path_clear = 54
            sep_dense, sep_open = 22, 38
        else:
            grove_share = 0.45
            path_clear = 55
            sep_dense, sep_open = 24, 40

        n_grove = int(count * grove_share)
        n_scatter = count - n_grove
        placed = 0
        attempts = 0
        max_attempts = count * 40 + 500

        # Dense grove placement
        while placed < n_grove and attempts < max_attempts:
            attempts += 1
            gx, gy, gr = rnd.choice(groves)
            ang = rnd.uniform(0, 6.28318)
            # Prefer center of grove for denser feel (gaussian-ish)
            rad = abs(rnd.gauss(0, gr * 0.45))
            rad = min(rad, gr * 1.15)
            x = gx + math.cos(ang) * rad
            y = gy + math.sin(ang) * rad
            big = rnd.random() < 0.28
            if self.try_tree(x, y, rnd, big, min_tree_sep=sep_dense, path_clear=path_clear):
                placed += 1

        # Scatter for natural edges / thinner zones (still off main path)
        while placed < count and attempts < max_attempts * 2:
            attempts += 1
            if rnd.random() < 0.35 and self.path_pts:
                p = rnd.choice(self.path_pts)
                ang = rnd.uniform(0, 6.28318)
                # Stand back from path — clear corridor, soft edge belt
                dist = rnd.uniform(path_clear + 8, path_clear + 90)
                x = p[0] + math.cos(ang) * dist
                y = p[1] + math.sin(ang) * dist
            else:
                x = rnd.uniform(90, WW - 90)
                y = rnd.uniform(90, WH - 90)
            big = rnd.random() < 0.18
            if self.try_tree(x, y, rnd, big, min_tree_sep=sep_open, path_clear=path_clear):
                placed += 1

        # Final fill if still short (relax spacing slightly, never change target count intent)
        relax = sep_open
        while placed < count and attempts < max_attempts * 3:
            attempts += 1
            x = rnd.uniform(90, WW - 90)
            y = rnd.uniform(90, WH - 90)
            if self.try_tree(x, y, rnd, rnd.random() < 0.2, min_tree_sep=max(16, relax - 6), path_clear=path_clear):
                placed += 1

    def ok_spot(self, x, y):
        if not (60 < x < WW-60 and 60 < y < WH-60): return False
        if self.in_water(x, y, -16) or self.on_bridge(x, y): return False
        for cx, cy, cr in self.colliders:
            if (x-cx)**2 + (y-cy)**2 < (cr+30)**2: return False
        for tx, ty in self.thorns:
            if (x-tx)**2 + (y-ty)**2 < 50**2: return False
        if not self.clear_of_pois(x, y, 60): return False
        return True

    def gen_spots(self, rnd, count, far, min_sep, avoid):
        out = []; tries = 0
        pool = (self.anchors_far if far else self.anchors_near) or self.anchors_near
        while len(out) < count and tries < 7000:
            tries += 1
            if pool and rnd.random() < 0.8:
                ax, ay = rnd.choice(pool)
                a = rnd.uniform(0, 6.283); d = rnd.uniform(8, 34)
                x = clamp(ax + math.cos(a)*d, 60, WW-60); y = clamp(ay + math.sin(a)*d, 60, WH-60)
            elif far:
                z = rnd.choice([(150,520,150,520),(1650,1950,320,620),(1500,1900,1000,1400),(150,520,1080,1400)])
                x = rnd.uniform(z[0], z[1]); y = rnd.uniform(z[2], z[3])
            else:
                p = rnd.choice(self.path_pts); a = rnd.uniform(0, 6.283); d = rnd.uniform(30, 90)
                x = clamp(p[0]+math.cos(a)*d, 60, WW-60); y = clamp(p[1]+math.sin(a)*d, 60, WH-60)
            if not self.ok_spot(x, y): continue
            if all((x-sx)**2 + (y-sy)**2 > min_sep**2 for sx, sy in out) and all((x-ax)**2 + (y-ay)**2 > 120**2 for ax, ay in avoid):
                out.append((x, y))
        while len(out) < count:
            out.append((rnd.uniform(200, WW-200), rnd.uniform(200, WH-200)))
        return out

    def make_hint(self, x, y):
        marks = [("the wooden bridge", 660, 760), ("the pond", 1160, 700), ("the Old Forest", 300, 300), ("the cliffs", 1850, 470), ("the village", 430, 1050)]
        name, mx, my = min(marks, key=lambda m: math.hypot(x-m[1], y-m[2]))
        dist = int(math.hypot(x-mx, y-my) / 12)
        dx, dy = x-1000, y-750
        card = "north" if dy < -abs(dx)*0.5 else "south" if dy > abs(dx)*0.5 else "west" if dx < 0 else "east"
        return name, card, dist

    def pick_unique_question(self, lvl):
        # Difficulty bands: 1–3 Easy, 4–6 Medium, 7–10 Hard
        if lvl <= 3:
            min_diff, max_diff, target = 1, 2, 1 if lvl == 1 else 2
        elif lvl <= 6:
            min_diff, max_diff, target = 2, 3, 3 if lvl >= 5 else 2
        else:
            min_diff, max_diff, target = 4, 5, 5 if lvl >= 9 else 4

        def pool(lo, hi, unused_only=True):
            out = []
            for i, row in enumerate(QUESTION_BANK):
                d = row[5]
                if lo <= d <= hi and (not unused_only or i not in self.used_questions_global):
                    out.append(i)
            return out

        available = pool(min_diff, max_diff, True)
        if not available:
            available = pool(target, target, True)
        if not available:
            available = pool(min_diff, max_diff, False)
            self.used_questions_global = set()
        if not available:
            available = list(range(len(QUESTION_BANK)))

        # Prefer exact target difficulty when possible
        preferred = [i for i in available if QUESTION_BANK[i][5] == target]
        q_idx = random.choice(preferred if preferred else available)
        self.used_questions_global.add(q_idx)
        subj, q, a, opts, fact, diff = QUESTION_BANK[q_idx]

        idxs = list(range(len(opts)))
        random.shuffle(idxs)
        shuffled_opts = [opts[i] for i in idxs]
        correct_pos = idxs.index(0)
        return {"subj": subj, "question": q, "answer": a, "options": shuffled_opts, "correct_index": correct_pos, "fact": fact, "bank_index": q_idx, "diff": diff}

    def gen_level_content(self, lvl):
        rnd = random.Random()  # fresh randomness: chests/question boxes and the goal star move every time
        num_required = 2  # only 2 question chests per level
        num_secret = 0
        self.anchors_near = []; self.anchors_far = []
        for tr in self.trees:
            x, y = tr[0], tr[1]
            px, py = x + 18, y + 10
            if self.ok_spot(px, py):
                (self.anchors_near if self.dist_to_path(px, py) < 150 else self.anchors_far).append((px, py))
        for (x, y, r) in self.rocks:
            px, py = x + 14, y + 8
            if self.ok_spot(px, py):
                (self.anchors_near if self.dist_to_path(px, py) < 150 else self.anchors_far).append((px, py))
                
        chest_positions = self.gen_spots(rnd, num_required + num_secret, lvl > 2, 250, [])
        self.chests = []
        for i, (x, y) in enumerate(chest_positions):
            q_data = self.pick_unique_question(lvl)
            roll = rnd.random()
            rar = "epic" if roll < 0.1 else ("rare" if roll < 0.4 else "common")
            is_required = i < num_required
            self.chests.append({"x": x, "y": y, "opened": False, "rarity": rar, "required": is_required, "question": q_data, "hint_level": 0, "hint": self.make_hint(x, y), "value": RARITY[rar][0]})
            
        self.required_chests = num_required
        self.chests_opened = 0
        # World loot: gems, scrolls, relics, nature items, rare artifacts
        self.loot_drops = []
        loot_n = 5 + min(6, lvl)
        kinds = ["gem", "gem", "scroll", "relic", "nature", "nature"]
        if lvl >= 5:
            kinds.append("artifact")
        if lvl >= 8:
            kinds.extend(["artifact", "scroll"])
        for i, (x, y) in enumerate(self.gen_spots(rnd, loot_n, False, 120, [(c["x"], c["y"]) for c in self.chests])):
            kind = kinds[i % len(kinds)]
            if lvl >= 7 and rnd.random() < 0.12:
                kind = "artifact"
            self.loot_drops.append({"x": x, "y": y, "kind": kind, "got": False})
        self.active_chest = None
        self.seal_t = 0
        self.quiz_feedback_t = 0
        self.feedback_msg = ""
        self.feedback_col = C_TEXT
        
        n_bram = 0 if lvl < 4 else min(6, (lvl - 2) // 2)
        avoid_all = [(c["x"], c["y"]) for c in self.chests] + [(430, 1050)]
        self.brambles = [{"x": x, "y": y} for x, y in self.gen_spots(rnd, n_bram, False, 150, avoid_all)]
        self.forage = []
        if self.bushes:
            for i in rnd.sample(range(len(self.bushes)), min(5, len(self.bushes))):
                bx, by, s = self.bushes[i]
                self.forage.append({"x": bx, "y": by, "used": False})
        self.gift_taken = False
        for lm in self.landmarks: lm["used"] = False
        for r in self.runes: r["used"] = False

    def goal_xy_for(self, lvl):
        for c in self.chests:
            if c.get("required", True) and not c["opened"]:
                return (c["x"], c["y"])
        return (300, 300)

    def make_quiz_image(self, subj, question):
        """Clear, high-contrast subject art for quiz (Brain Trek / highland themed)."""
        try:
            s = pygame.Surface((160, 120), pygame.SRCALPHA)
            # parchment panel
            s.fill((32, 42, 38))
            pygame.draw.rect(s, (48, 62, 55), (4, 4, 152, 112), border_radius=10)
            pygame.draw.rect(s, (120, 160, 140), (4, 4, 152, 112), 2, border_radius=10)
            sub = (subj or "").lower()
            q = (question or "").lower()
            cx, cy = 80, 62

            def tree_icon(x, y, sc=1.0):
                pygame.draw.rect(s, (90, 60, 35), (int(x - 4 * sc), int(y), int(8 * sc), int(22 * sc)))
                pygame.draw.circle(s, (36, 120, 55), (int(x), int(y - 8 * sc)), int(16 * sc))
                pygame.draw.circle(s, (50, 150, 70), (int(x - 8 * sc), int(y - 4 * sc)), int(10 * sc))
                pygame.draw.circle(s, (55, 160, 75), (int(x + 8 * sc), int(y - 4 * sc)), int(10 * sc))

            # --- SCIENCE ---
            if "photosynth" in q or ("plant" in q and "food" in q) or ("gas" in q and "tree" in q) or "oxygen" in q or "carbon dioxide" in q:
                tree_icon(70, 78, 1.15)
                pygame.draw.circle(s, (255, 210, 70), (30, 28), 14)
                for a in range(0, 360, 45):
                    pygame.draw.line(s, (255, 220, 100), (30, 28),
                                     (30 + int(math.cos(math.radians(a)) * 20), 28 + int(math.sin(math.radians(a)) * 20)), 2)
                # O2 / CO2 hint bubbles
                pygame.draw.circle(s, (140, 210, 255), (115, 40), 12)
                pygame.draw.circle(s, (100, 180, 120), (125, 70), 10)
            elif "cell" in q or "mitochond" in q or "blood" in q or "heart" in q:
                pygame.draw.ellipse(s, (200, 70, 85), (45, 30, 70, 55))
                pygame.draw.ellipse(s, (240, 110, 120), (55, 38, 50, 38))
                pygame.draw.ellipse(s, (255, 160, 160), (65, 45, 20, 16))
            elif "spider" in q or "crab" in q or "leg" in q:
                pygame.draw.ellipse(s, (160, 100, 70), (55, 48, 50, 28))
                pygame.draw.circle(s, (160, 100, 70), (110, 55), 12)
                for i in range(4):
                    pygame.draw.line(s, (120, 80, 50), (60 + i * 10, 72), (52 + i * 12, 95), 2)
                    pygame.draw.line(s, (120, 80, 50), (60 + i * 10, 72), (70 + i * 10, 95), 2)
            elif "mars" in q or "planet" in q or "red planet" in q:
                pygame.draw.circle(s, (200, 90, 60), (cx, cy), 32)
                pygame.draw.circle(s, (180, 70, 45), (cx - 10, cy - 8), 8)
                pygame.draw.circle(s, (220, 120, 80), (cx + 12, cy + 10), 6)
            elif "boil" in q or "water" in q and "temperature" in q or "pressure" in q or "altitude" in q:
                pygame.draw.rect(s, (80, 140, 200), (50, 55, 60, 40), border_radius=4)
                for i in range(5):
                    pygame.draw.circle(s, (200, 220, 240), (60 + i * 10, 48 - i * 2), 4)
            elif "vitamin" in q or "sunlight" in q:
                pygame.draw.circle(s, (255, 210, 70), (cx, 40), 20)
                pygame.draw.ellipse(s, (240, 200, 170), (50, 70, 60, 30))
            elif "fog" in q or "droplet" in q:
                for i in range(8):
                    pygame.draw.ellipse(s, (180, 200, 210), (20 + i * 14, 40 + (i % 3) * 10, 40, 16))
            elif "nitrogen" in q or "air" in q:
                pygame.draw.circle(s, (140, 190, 230), (cx, cy), 36, 3)
                for i, lab in enumerate(["N2", "O2"]):
                    pygame.draw.circle(s, (100, 160, 210) if i == 0 else (120, 200, 160), (55 + i * 50, cy), 16)
            else:
                # generic science flask
                pygame.draw.polygon(s, (160, 210, 230), [(70, 30), (90, 30), (100, 90), (60, 90)])
                pygame.draw.rect(s, (200, 230, 240), (68, 22, 24, 12), border_radius=2)

            # --- MATH ---
            if "math" in sub or any(k in q for k in ["x ", "solve", "square", "prime", "percent", "%", "average", "mean", "probability", "km", "area", "power"]):
                s.fill((32, 42, 38))
                pygame.draw.rect(s, (40, 55, 70), (4, 4, 152, 112), border_radius=10)
                pygame.draw.rect(s, (100, 160, 200), (4, 4, 152, 112), 2, border_radius=10)
                # chalkboard numbers
                pygame.draw.rect(s, (45, 70, 55), (20, 20, 120, 80), border_radius=6)
                if "triangle" in q or "angle" in q:
                    pygame.draw.polygon(s, (80, 180, 220), [(80, 30), (130, 90), (30, 90)])
                elif "percent" in q or "%" in q or "15%" in q or "25%" in q:
                    pygame.draw.circle(s, (230, 200, 80), (cx, cy), 28, 3)
                    pygame.draw.line(s, (230, 200, 80), (cx - 12, cy + 12), (cx + 12, cy - 12), 3)
                elif "prime" in q:
                    for i, n in enumerate(["2", "3", "5", "7"]):
                        pygame.draw.circle(s, (90, 160, 200), (40 + i * 28, cy), 14)
                elif "map" in q or "scale" in q:
                    pygame.draw.rect(s, (210, 190, 140), (30, 25, 100, 70), border_radius=4)
                    pygame.draw.line(s, (80, 60, 40), (40, 80), (120, 40), 2)
                    pygame.draw.circle(s, (200, 60, 50), (50, 70), 4)
                else:
                    # x and operators
                    pygame.draw.line(s, (220, 230, 200), (45, 40), (70, 75), 4)
                    pygame.draw.line(s, (220, 230, 200), (70, 40), (45, 75), 4)
                    pygame.draw.line(s, (180, 200, 120), (90, 55), (130, 55), 4)
                    pygame.draw.line(s, (180, 200, 120), (110, 35), (110, 75), 4)

            # --- HISTORY / BHUTAN ---
            if "histor" in sub or "bhutan" in q or "dzong" in q or "king" in q or "gnh" in q or "constitution" in q or "thimphu" in q or "archery" in q or "takin" in q or "ngultrum" in q or "poppy" in q:
                s.fill((32, 42, 38))
                pygame.draw.rect(s, (55, 48, 40), (4, 4, 152, 112), border_radius=10)
                pygame.draw.rect(s, (200, 160, 70), (4, 4, 152, 112), 2, border_radius=10)
                # dzong silhouette
                pygame.draw.rect(s, (190, 175, 140), (35, 50, 90, 50))
                pygame.draw.polygon(s, (150, 50, 45), [(28, 50), (132, 50), (118, 28), (42, 28)])
                pygame.draw.rect(s, (50, 40, 30), (70, 68, 20, 32))
                pygame.draw.rect(s, (200, 160, 50), (50, 46, 60, 8))
                # prayer flag dots
                for i, c in enumerate([(210, 50, 50), (230, 200, 50), (50, 140, 70), (50, 90, 190)]):
                    pygame.draw.rect(s, c, (40 + i * 20, 18, 14, 6))

            # --- ECONOMICS ---
            if "econ" in sub or "gold" in q or "price" in q or "money" in q or "market" in q or "trade" in q or "inflation" in q or "tariff" in q or "monopoly" in q or "interest" in q or "consumer" in q or "saving" in q or "opportunity" in q:
                s.fill((32, 42, 38))
                pygame.draw.rect(s, (50, 48, 35), (4, 4, 152, 112), border_radius=10)
                pygame.draw.rect(s, (212, 172, 82), (4, 4, 152, 112), 2, border_radius=10)
                pygame.draw.circle(s, (212, 172, 82), (cx, cy), 34)
                pygame.draw.circle(s, (160, 120, 40), (cx, cy), 34, 3)
                pygame.draw.circle(s, (240, 210, 120), (cx - 8, cy - 8), 8)
                # simple G mark
                pygame.draw.arc(s, (90, 55, 20), (cx - 12, cy - 12, 24, 24), 0.3, 5.5, 3)

            # --- ENVIRONMENT ---
            if "environ" in sub or "forest" in q or "soil" in q or "erosion" in q or "biodiversity" in q or "plastic" in q or "climate" in q or "ozone" in q or "terrace" in q or "decomposer" in q or "herbivore" in q or "bee" in q or "nectar" in q or "renewable" in q or "afforestation" in q:
                s.fill((32, 42, 38))
                pygame.draw.rect(s, (35, 55, 40), (4, 4, 152, 112), border_radius=10)
                pygame.draw.rect(s, (70, 160, 90), (4, 4, 152, 112), 2, border_radius=10)
                tree_icon(55, 85, 1.0)
                tree_icon(100, 90, 0.85)
                pygame.draw.ellipse(s, (90, 160, 70), (25, 90, 110, 18))
                if "bee" in q or "nectar" in q:
                    pygame.draw.circle(s, (255, 220, 80), (120, 40), 10)
                    pygame.draw.circle(s, (40, 40, 40), (120, 40), 10, 1)
                    pygame.draw.line(s, (40, 40, 40), (120, 30), (120, 50), 2)
                if "plastic" in q or "reuse" in q:
                    pygame.draw.arc(s, (60, 180, 100), (100, 25, 40, 40), 0.2, 4, 3)

            pygame.draw.rect(s, (160, 210, 190), s.get_rect(), 2, border_radius=8)
            return s
        except Exception:
            return None

    def setup_quiz_for_chest(self, chest):
        q = chest["question"]
        self.quiz_subj = q["subj"]; self.quiz_question = q["question"]; self.quiz_answer = q["answer"]
        self.quiz_fact = q["fact"]
        opts = list(q["options"])
        random.shuffle(opts)                         # correct answer lands in a random box
        self.quiz_opts = opts
        self.quiz_ans = opts.index(q["answer"])
        self.quiz_start = pygame.time.get_ticks()
        self.quiz_feedback_t = 0
        self.hint_removed = []
        # always show a clear subject illustration
        self.quiz_image = None
        try:
            self.quiz_image = self.make_quiz_image(self.quiz_subj, self.quiz_question)
        except Exception:
            self.quiz_image = None


    def burst_fx(self, x, y, color, n=14, speed=2.5, life=28):
        """Small particle burst at world position."""
        if not hasattr(self, "parts"):
            self.parts = []
        for _ in range(n):
            ang = random.uniform(0, 6.28318)
            sp = random.uniform(0.6, speed)
            self.parts.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * sp,
                "vy": math.sin(ang) * sp - random.uniform(0.5, 1.8),
                "l": life + random.randint(0, 10),
                "c": color,
            })

    def ring_fx(self, x, y, color, n=10):
        for i in range(n):
            ang = (i / float(n)) * 6.28318
            self.parts.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * 2.2,
                "vy": math.sin(ang) * 2.2,
                "l": 22,
                "c": color,
            })

    def reveal_hint(self):
        """Point to nearest unopened chest. 2 free hints per level, then gold/bought."""
        targets = [c for c in self.chests if not c.get("opened")]
        if not targets:
            self.say("No unopened chests left on this level.")
            return False
        free = int(getattr(self, "level_free_hints", getattr(self, "free_hints_left", 2)))
        bought = int(getattr(self, "hint_charges", 0))
        gold_cost = 1200
        if free <= 0 and bought <= 0 and self.gold < gold_cost:
            self.say("No free hints left this level. Buy a hint (1200g) at the shop.")
            return False
        if free > 0:
            self.level_free_hints = free - 1
            self.free_hints_left = self.level_free_hints  # keep save field in sync
            paid = "%d free left" % self.level_free_hints
        elif bought > 0:
            self.hint_charges = bought - 1
            paid = "1 bought used"
        else:
            self.gold -= gold_cost
            paid = "1200g spent"
        nearest = min(targets, key=lambda c: (c["x"]-self.px)**2 + (c["y"]-self.py)**2)
        nearest["hint_level"] = max(int(nearest.get("hint_level", 0)), 3)
        self.beacon_t = pygame.time.get_ticks() + 18000
        self.beacon_chest = nearest
        dx, dy = nearest["x"] - self.px, nearest["y"] - self.py
        # 8-direction compass
        ang = math.degrees(math.atan2(dx, -dy)) % 360  # 0 = north
        dirs = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
        card = dirs[int((ang + 22.5) // 45) % 8]
        dist = int(math.hypot(dx, dy) / 12)
        self.say("Treasure clue: about %dm %s  (%s)" % (dist, card, paid))
        self.audio.play("clue")
        # silent save only — never show "Progress saved" for H
        try:
            self.save_progress(silent=True)
        except Exception:
            pass
        return True

    def hints_available(self):
        return max(0, int(getattr(self, "free_hints_left", 0))) + max(0, int(getattr(self, "hint_charges", 0)))

    def use_quiz_hint(self):
        """Use one quiz hint: free stock first, then purchased charges. Returns True if used."""
        if len(getattr(self, "hint_removed", []) or []) >= 2:
            self.say("No more wrong answers to remove on this question.")
            return False
        free = int(getattr(self, "free_hints_left", 0))
        bought = int(getattr(self, "hint_charges", 0))
        if free <= 0 and bought <= 0:
            self.say("No hints left. Buy Quiz Hints from the merchant (1200g).")
            return False
        wrong_opts = [i for i in range(4) if i != self.quiz_ans and i not in self.hint_removed]
        if not wrong_opts:
            self.say("Nothing left to remove.")
            return False
        # Consume free first
        if free > 0:
            self.free_hints_left = free - 1
            src = "free"
        else:
            self.hint_charges = bought - 1
            src = "bought"
        self.hint_removed.append(random.choice(wrong_opts))
        self.audio.play("clue")
        left = self.hints_available()
        if src == "free":
            self.say("Free hint used! (%d free left, %d bought)" % (self.free_hints_left, self.hint_charges))
        else:
            self.say("Hint used! (%d free left, %d bought)" % (self.free_hints_left, self.hint_charges))
        try:
            self.save_progress(silent=True)
        except Exception:
            pass
        return True

    def chests_left(self):
        return sum(1 for c in self.chests if c.get("required", True) and not c["opened"])

    def earn_ach(self, i):
        if i not in self.ach:
            self.ach.add(i)
            if not hasattr(self, "ach_this_level"):
                self.ach_this_level = []
            self.ach_this_level.append(i)
            self.audio.play("clue")
            name = ACH[i][0] if i in ACH else i.replace("_", " ").title()
            self.say("Achievement unlocked: %s" % name)

    def build_terrain(self):
        b = BIOMES[self.biome]
        rnd = random.Random(4242)
        t = pygame.Surface((WW, WH), pygame.SRCALPHA)
        t.fill(b["grass"])
        # Fine grass texture only (no large circular patches)
        # fine grass noise
        for _ in range(3800):
            x, y = rnd.randint(0, WW-1), rnd.randint(0, WH-1)
            pygame.draw.circle(t, shade(b["grass"], rnd.choice([-12, -6, 5, 10, 14])), (x, y), rnd.randint(1, 3))
        # soft color patches for terrain variety (meadow / moss / dry)
        for _ in range(90):
            x, y = rnd.randint(40, WW-40), rnd.randint(40, WH-40)
            if self.in_water(x, y, -8): continue
            col = shade(b["grass"], rnd.choice([-18, -12, 10, 16]))
            pygame.draw.circle(t, col, (x, y), rnd.randint(18, 42))
        # grass blades
        for _ in range(2600):
            x, y = rnd.randint(0, WW-1), rnd.randint(0, WH-1)
            if self.in_water(x, y, -4): continue
            h = rnd.randint(3, 9)
            base = darken(b["grass"], rnd.randint(16, 32))
            tip = lighten(b["grass"], rnd.randint(6, 20))
            pygame.draw.line(t, base, (x, y), (x-2, y-h), 1)
            pygame.draw.line(t, tip, (x-1, y-h+1), (x-2, y-h), 1)
            pygame.draw.line(t, base, (x, y), (x+2, y-h+1), 1)
        # Footpaths intentionally not drawn – open natural ground only.
        # path_pts still used for logic (NPC roam, step sounds, etc.).
        wb = b["water"]
        for band, col in [(16, b["sand"]), (7, wb[0]), (0, wb[1]), (-26, wb[2])]:
            for wx, wy, wr in self.water[::2]:
                r = wr + band
                if r > 6: pygame.draw.circle(t, col, (int(wx), int(wy)), int(r))
        for i in range(4, len(self.water), 37):
            wx, wy, wr = self.water[i]
            pygame.draw.ellipse(t, (110, 96, 74), (int(wx-wr-26), int(wy-8), 30, 16))
        for x, y, r in self.rocks:
            soft_shadow(t, x, y + r * 0.3, int(r), int(r * 0.4), 80)
        for bx, by, bs in self.bushes:
            # fuller multi-lobe bushes
            pygame.draw.circle(t, darken(b["leaf"][0], 12), (int(bx), int(by - 2*bs)), int(10*bs))
            pygame.draw.circle(t, b["leaf"][0], (int(bx-6*bs), int(by-6*bs)), int(9*bs))
            pygame.draw.circle(t, (46, 128, 66), (int(bx+5*bs), int(by-5*bs)), int(8*bs))
            pygame.draw.circle(t, b["leaf"][1], (int(bx), int(by-11*bs)), int(7*bs))
            pygame.draw.circle(t, lighten(b["leaf"][1], 15), (int(bx-3*bs), int(by-12*bs)), int(4*bs))
        for fx, fy, fs in self.ferns:
            for a in (-0.7, -0.25, 0.25, 0.7):
                ex = fx + math.sin(a) * 11 * fs
                ey = fy - math.cos(a) * 15 * fs
                pygame.draw.line(t, (55, 130, 68), (int(fx), int(fy)), (int(ex), int(ey)), 2)
                pygame.draw.line(t, (80, 160, 90), (int(fx), int(fy - 1)), (int(ex), int(ey - 1)), 1)
        for lx, ly in self.leaves_sp:
            pygame.draw.circle(t, rnd.choice([(120, 140, 60), (140, 150, 50), (100, 130, 60), (90, 125, 55)]), (int(lx), int(ly)), 2)
        for sx, sy, r in self.shore_rocks:
            pygame.draw.ellipse(t, darken((128,130,136), 15), (int(sx-r), int(sy-r*.55), int(r*2), int(r*1.15)))
            pygame.draw.ellipse(t, (128,130,136), (int(sx-r*0.85), int(sy-r*.65), int(r*1.7), int(r)))
            pygame.draw.ellipse(t, lighten((128,130,136), 20), (int(sx-r*.4), int(sy-r*.85), int(r), int(r*.5)))
        for fx, fy, c in self.flowers:
            # stem
            pygame.draw.line(t, (45, 110, 50), (int(fx), int(fy + 4)), (int(fx), int(fy - 1)), 1)
            # petals – slightly larger, more colorful
            for a in range(0, 360, 45):
                px = int(fx + math.cos(math.radians(a)) * 4.5)
                py = int(fy + math.sin(math.radians(a)) * 3.5)
                pygame.draw.circle(t, c, (px, py), 2)
            pygame.draw.circle(t, lighten(c, 35), (int(fx), int(fy)), 2)
            pygame.draw.circle(t, (255, 248, 170), (int(fx), int(fy)), 1)
        for mx, my in self.mushrooms:
            pygame.draw.rect(t, (225,218,205), (int(mx)-1, int(my)-1, 3, 5))
            pygame.draw.ellipse(t, (170,65,55), (int(mx)-5, int(my)-6, 10, 6))
            pygame.draw.ellipse(t, (200,90,75), (int(mx)-3, int(my)-7, 5, 3))
            pygame.draw.circle(t, (255, 240, 230), (int(mx)-2, int(my)-5), 1)
        for tx, ty in self.thorns:
            pygame.draw.circle(t, (44, 76, 40), (tx, ty), 24)
            pygame.draw.circle(t, (58, 92, 48), (tx, ty), 18)
        if b["amb"] == "snow":
            for sxp, syp, sr in getattr(self, "snowp", []) or []:
                pygame.draw.ellipse(t, (245, 248, 252, 200), (int(sxp-sr), int(syp-int(sr*.6)), int(sr*2), int(sr*1.2)))
        # Pillars / stone structures for ruin & monastery biomes
        if b.get("chortens") or b["amb"] == "ancient":
            for x, y, s in self.pillars:
                soft_shadow(t, x, y+2, int(12*s), int(6*s), 90)
                pygame.draw.rect(t, (150, 150, 158), (int(x-6*s), int(y-40*s), int(12*s), int(40*s)))
                pygame.draw.rect(t, (170, 170, 178), (int(x-8*s), int(y-44*s), int(16*s), int(6*s)))
                pygame.draw.rect(t, (90, 110, 80), (int(x-6*s), int(y-10), int(12*s), 6))
        if b["amb"] == "ancient":
            for _ in range(15):
                x, y = rnd.randint(100, WW-100), rnd.randint(100, WH-100)
                if self.ok_spot(x, y):
                    pygame.draw.rect(t, (160, 150, 130), (x-8, y-30, 16, 30))
                    pygame.draw.rect(t, (180, 170, 150), (x-10, y-32, 20, 4))
        self.terrain = t

    def build_minimap_base(self):
        bg = pygame.Surface((WW, WH)); bg.fill((30, 36, 30)); bg.blit(self.terrain, (0, 0))
        self.mm_base = pygame.transform.smoothscale(bg, (150, 112))
        for br in getattr(self, "bridges", []) or []:
            pygame.draw.rect(self.mm_base, (150,110,60), (int(br.x/WW*150), int(br.y/WH*112), max(2, int(br.w/WW*150)), max(2, int(br.h/WH*112))))

    def build_light(self):
        self.light = pygame.Surface((W, H), pygame.SRCALPHA)
        # soft sun-shaft warmth from upper right
        for i in range(40):
            pygame.draw.ellipse(self.light, (255, 245, 210, 2), (-200 + i * 7, -280 + i * 6, 1100 - i * 14, 850 - i * 12))
        # cooler vignette edges for cinematic depth
        for i in range(30):
            a = min(5, 2 + i // 6)
            pygame.draw.rect(self.light, (8, 18, 14, a), (0, 0, W, H), 36 - i)
        # subtle top sky wash
        for i in range(12):
            pygame.draw.rect(self.light, (200, 220, 240, 2), (0, i * 4, W, 6))

    def reset_run(self):
        self.px, self.py = 430.0, 1050.0
        self.vx = self.vy = 0.0
        self.lives = self.max_lives
        self.inv = 0; self.flash = 0
        self.camx, self.camy = self.px, self.py
        self.walk = 0.0; self.face = 1; self.moving = False; self.running = False
        self.direction = "down"
        self.dash_cd = 0; self.dash_t = 0
        self.attack_cd = 0; self.attack_t = 0; self.attack_dir = (1, 0)
        self.shield_until = 0; self.boost_until = 0
        self.weapon = "staff" in self.inventory
        # hint_charges & free_hints_left persist across levels (not reset here)
        self.hint_removed = []
        if not hasattr(self, "loot_drops"): self.loot_drops = []
        self.quest_trees = 0; self.quest_trash = 0
        self.toast = ""; self.toast_t = 0
        self.prompt = None; self.interact = None
        self.chirp_t = 3000
        self.parts = []; self.ripples = []
        self.saplings = []
        self.quiz_correct = 0; self.quiz_wrong = 0
        self.streak = 0; self.best_streak = 0
        self.last_quiz = None
        self.reward_bonus = 0
        self.done_t = 0
        self.dialog = None; self.dialog_lines = []
        self.ach_this_level = []; self.hits_taken = 0; self.kills_this_level = 0
        self.forage_count = getattr(self, "forage_count", 0)
        self.biomes_visited = getattr(self, "biomes_visited", set())
        self.beacon_t = 0
        self.beacon_chest = None
        self.extra = []
        self.fade_t = 0
        self.rockfalls = []; self.rock_t = 3.0
        self.active_chest = None
        self.seen = set(); self.wild_rewarded = False
        self.weather = getattr(self, "weather", "sunshine"); self.thunder_t = 0; self.flash_white = 0
        for tr in self.trash: tr["got"] = False
        for lm in self.landmarks: lm["used"] = False
        for n in getattr(self, "npcs", []):
            n["x"], n["y"] = float(n["home"][0]), float(n["home"][1])
            n["state"] = "IDLE"; n["timer"] = random.uniform(0.6, 1.6)
            n["tx"], n["ty"] = n["x"], n["y"]; n["phase"] = 0.0
        self.spawn_enemies(self.current_level)
        self.gen_level_content(self.current_level)

    def place_houses_for_level(self):
        """Place highland houses on dry land only — never in water or on bridges."""
        self.houses = []
        self.house_colliders = []
        self.player_house = None
        theme = getattr(self, "level_env", {}).get("theme", "forest")
        if theme not in ("village", "city", "forest", "temple", "ruins"):
            # still allow a mine house on dry land
            pass
        rnd = random.Random(400 + self.current_level * 17)

        def dry_spot(x, y, tries=40):
            x, y = float(x), float(y)
            for _ in range(tries):
                if (not self.in_water(x, y, -30)
                        and not self.on_bridge(x, y)
                        and 80 < x < WW - 80 and 80 < y < WH - 80):
                    # keep off other houses
                    ok = True
                    for h in self.houses:
                        if (x - h["x"]) ** 2 + (y - h["y"]) ** 2 < 120 ** 2:
                            ok = False; break
                    if ok:
                        return x, y
                x += rnd.uniform(-80, 80)
                y += rnd.uniform(-60, 60)
            # fallback: scan north of river band
            for yy in range(int(WH * 0.15), int(WH * 0.40), 40):
                for xx in range(120, int(WW) - 120, 90):
                    if not self.in_water(xx, yy, -30) and not self.on_bridge(xx, yy):
                        return float(xx), float(yy)
            return float(WW * 0.3), float(WH * 0.25)

        # Estimate river band center Y from water samples
        river_y = WH * 0.5
        if self.water:
            river_y = sum(w[1] for w in self.water) / len(self.water)

        layouts = {
            "village": [
                (WW * 0.22, river_y - 220, "Guide Karma"),
                (WW * 0.32, river_y - 180, "Merchant Dawa"),
                (WW * 0.42, river_y - 240, "Keeper Pema"),
                (WW * 0.28, river_y + 220, "Villager Sonam"),
                (WW * 0.38, river_y + 260, "Historian Dorji"),
                (WW * 0.50, river_y + 200, "Eco Tshering"),
            ],
            "city": [
                (WW * 0.20, river_y - 200, "Guide Karma"),
                (WW * 0.30, river_y - 170, "Merchant Dawa"),
                (WW * 0.45, river_y - 230, "Keeper Pema"),
                (WW * 0.55, river_y + 210, "Villager Sonam"),
            ],
            "forest": [
                (WW * 0.25, river_y - 200, "Guide Karma"),
                (WW * 0.40, river_y + 210, "Merchant Dawa"),
            ],
            "temple": [
                (WW * 0.30, river_y - 240, "Keeper Pema"),
                (WW * 0.50, river_y - 180, "Historian Dorji"),
            ],
            "ruins": [
                (WW * 0.28, river_y - 200, "Historian Dorji"),
                (WW * 0.48, river_y + 220, "Guide Karma"),
            ],
        }
        spots = layouts.get(theme, layouts["forest"])
        for hx, hy, owner in spots:
            hx, hy = dry_spot(hx, hy)
            s = 1.15
            self.houses.append({
                "x": hx, "y": hy, "s": s,
                "owner": owner, "is_player": False, "theme": theme,
            })
            self.house_colliders.append((hx, hy, 22 * s))

        # Player / mine house on dry land
        mx, my = dry_spot(WW * 0.18, river_y - 280)
        mine_s = 1.8
        self.houses.append({
            "x": mx, "y": my, "s": mine_s,
            "owner": "Mine House", "is_player": True, "theme": theme,
        })
        self.house_colliders.append((mx, my, 24 * mine_s))
        self.player_house = self.houses[-1]
        for c in self.house_colliders:
            self.colliders.append(c)


    def ensure_bridges(self, water_mode="river", lvl=1):
        """Guarantee visible, walkable bridges spanning the water. Never empty for river/stream."""
        self.bridges = []
        if not self.water:
            return
        if water_mode not in ("river", "stream"):
            # ponds / none: no bridges
            self.bridges = []
            return

        # Sample water centerline Y at several X positions
        def water_at_x(tx):
            best = min(self.water, key=lambda w: abs(w[0] - tx))
            return best  # wx, wy, wr

        if water_mode == "ponds":
            # Ponds stay open water — no wooden decks/bridges
            self.bridges = []
            return

        # River / stream: 2–3 full-span wooden bridges across the map
        xs = [WW * 0.22, WW * 0.50, WW * 0.78] if water_mode == "river" else [WW * 0.35, WW * 0.65]
        for tx in xs:
            wx, wy, wr = water_at_x(tx)
            if water_mode == "river":
                # Proportional fantasy span (room for posts + rails)
                bw = 80
                bh = int(max(120, wr * 2.5 + 52))
            else:
                bw = 64
                bh = int(max(88, wr * 2.3 + 40))
            br = pygame.Rect(int(wx - bw // 2), int(wy - bh // 2), bw, bh)
            self.bridges.append(br)

        # Absolute fallback
        if not self.bridges:
            wx, wy, wr = self.water[len(self.water) // 2]
            self.bridges.append(pygame.Rect(int(wx - 65), int(wy - 90), 130, int(max(160, wr * 3 + 90))))

        # Clear any tree/rock colliders that sit on bridge decks (post-place cleanup is also done later)
        return

    def rebuild_open_world(self, lvl, env):
        """Realistic, theme-varied highland layout. Bridges only span rivers."""
        rnd = random.Random(1000 + lvl * 97)
        theme = env.get("theme", "forest")
        water_mode = env.get("water", "stream")
        self.bridges = []  # pygame.Rect list — only over real water
        self.water = []

        # ---------- WATER ----------
        if water_mode == "river":
            # Wide Himalayan river — horizontal band across the map
            y0 = WH * 0.50
            pts = []
            for i in range(0, int(WW) + 40, 14):
                x = float(i)
                y = y0 + math.sin(i * 0.012 + lvl * 0.4) * 55 + math.sin(i * 0.031) * 18
                r = 78 + 12 * math.sin(i * 0.02)
                pts.append((x, y, r))
            self.water = pts
        elif water_mode == "stream":
            y0 = WH * 0.48
            pts = []
            for i in range(0, int(WW) + 40, 16):
                x = float(i)
                y = y0 + math.sin(i * 0.018 + lvl) * 40
                r = 36 + 6 * math.sin(i * 0.03)
                pts.append((x, y, r))
            self.water = pts
        elif water_mode == "ponds":
            self.water = []
            for i in range(3):
                cx = WW * (0.22 + i * 0.28)
                cy = WH * (0.35 + (i % 2) * 0.25)
                for a in range(0, 360, 20):
                    rad = math.radians(a)
                    rr = 55 + 10 * math.sin(a * 0.1 + i)
                    self.water.append((cx + math.cos(rad) * rr * 0.3, cy + math.sin(rad) * rr * 0.25, rr))
        else:
            self.water = []

        # ALWAYS place walkable bridges when water exists (never leave river uncrossable)
        self.ensure_bridges(water_mode, lvl)

        # ---------- CLEAR PROPS ----------
        # ---------- CLEAR PROPS ----------
        self.colliders = []
        self.trees = []; self.rocks = []; self.reeds = []; self.shore_rocks = []
        self.flowers = []; self.mushrooms = []; self.logs = []; self.leaves_sp = []
        self.bushes = []; self.ferns = []; self.grass_tufts = []; self.lily = []
        self.thorns = []; self.prayer_flags = []; self.chortens = []; self.pillars = []

        # Density by theme (open, not cramped)
        dens = {
            "forest":   {"trees": 260, "rocks": 22, "bushes": 70, "ferns": 80, "flowers": 90, "grass": 180, "flags": 6, "chortens": 1},
            "village":  {"trees": 110, "rocks": 10, "bushes": 35, "ferns": 25, "flowers": 50, "grass": 100, "flags": 10, "chortens": 2},
            "mountain": {"trees": 140, "rocks": 45, "bushes": 20, "ferns": 15, "flowers": 25, "grass": 80,  "flags": 5, "chortens": 2},
            "temple":   {"trees": 120, "rocks": 14, "bushes": 22, "ferns": 18, "flowers": 35, "grass": 70,  "flags": 12, "chortens": 4},
            "ruins":    {"trees": 100, "rocks": 30, "bushes": 18, "ferns": 12, "flowers": 15, "grass": 60,  "flags": 4, "chortens": 5},
            "city":     {"trees": 95,  "rocks": 8,  "bushes": 20, "ferns": 10, "flowers": 30, "grass": 70,  "flags": 8, "chortens": 2},
        }.get(theme, {"trees": 140, "rocks": 16, "bushes": 40, "ferns": 40, "flowers": 40, "grass": 100, "flags": 4, "chortens": 1})

        # Level 1: extra polish — denser, livelier forest welcome
        if lvl == 1:
            dens = dict(dens)
            dens["trees"] = max(dens["trees"], 280)
            dens["bushes"] = max(dens["bushes"], 90)
            dens["ferns"] = max(dens["ferns"], 95)
            dens["flowers"] = max(dens["flowers"], 120)
            dens["grass"] = max(dens["grass"], 220)
            dens["rocks"] = max(dens["rocks"], 24)
            dens["flags"] = max(dens["flags"], 8)

        # Trees — same count, natural groves + clear paths + varied sizes
        self.place_trees_natural(dens["trees"], rnd, theme)
        # Keep bridge decks free of trees/rocks so the crossing stays visible
        if self.bridges:
            self.trees = [tr for tr in self.trees if not any(
                br.inflate(36, 36).collidepoint(tr[0], tr[1]) for br in self.bridges)]
            # rebuild tree colliders only — remove colliders that sit on bridges
            self.colliders = [c for c in self.colliders if not any(
                br.inflate(20, 20).collidepoint(c[0], c[1]) for br in self.bridges)]
            # re-add tree trunk colliders for remaining trees
            for tr in self.trees:
                s = tr[2]
                kind = tr[3] if len(tr) > 3 else "pine"
                trunk_r = 3.5 * s if kind in ("pine", "tall_pine", "cedar", "birch") else 4.2 * s
                self.colliders.append((tr[0], tr[1], trunk_r))

        # Rocks (more on mountains)
        for _ in range(dens["rocks"]):
            x, y = rnd.uniform(140, WW - 140), rnd.uniform(140, WH - 140)
            if not self.in_water(x, y, -18) and self.clear_of_pois(x, y, 45) and self.dist_to_path(x, y) > 20:
                r = rnd.uniform(7, 22 if theme == "mountain" else 16)
                self.rocks.append((x, y, r))
                if r > 11:
                    self.colliders.append((x, y, r * 0.75))

        # Path-edge stones
        for _ in range(12):
            if not self.path_pts:
                break
            p = rnd.choice(self.path_pts)
            a = rnd.uniform(0, 6.28)
            x = p[0] + math.cos(a) * rnd.uniform(20, 40)
            y = p[1] + math.sin(a) * rnd.uniform(16, 32)
            if not self.in_water(x, y, -8):
                self.rocks.append((x, y, rnd.uniform(4, 9)))

        # Flowers — forest meadows & village gardens
        flower_cols = [
            (255, 120, 140), (255, 200, 80), (255, 255, 130), (200, 140, 255),
            (255, 160, 200), (120, 200, 255), (255, 100, 80), (180, 255, 160),
            (255, 220, 100), (230, 180, 255),  # rhododendron-ish pinks/yellows
        ]
        for _ in range(dens["flowers"]):
            x, y = rnd.uniform(70, WW - 70), rnd.uniform(70, WH - 70)
            if not self.in_water(x, y, -10) and self.dist_to_path(x, y) > 18:
                self.flowers.append((x, y, rnd.choice(flower_cols)))

        # Bushes & ferns
        for _ in range(dens["bushes"]):
            x, y = rnd.uniform(70, WW - 70), rnd.uniform(70, WH - 70)
            if not self.in_water(x, y, -14) and self.dist_to_path(x, y) > 26 and self.clear_of_pois(x, y, 36):
                self.bushes.append((x, y, rnd.uniform(0.7, 1.35)))
        for _ in range(dens["ferns"]):
            x, y = rnd.uniform(60, WW - 60), rnd.uniform(60, WH - 60)
            if not self.in_water(x, y, -8) and self.dist_to_path(x, y) > 18:
                self.ferns.append((x, y, rnd.uniform(0.7, 1.25)))
        for _ in range(dens["grass"]):
            x, y = rnd.uniform(40, WW - 40), rnd.uniform(40, WH - 40)
            if not self.in_water(x, y, -5) and self.dist_to_path(x, y) > 14:
                self.grass_tufts.append((x, y, rnd.uniform(0.55, 1.3), rnd.uniform(0, 6.28)))

        # Understory under trees
        for tr in self.trees:
            if hash01(tr[0] * 0.1 + tr[1]) > 0.5:
                self.mushrooms.append((tr[0] + rnd.uniform(-18, 18), tr[1] + rnd.uniform(6, 18)))
            self.leaves_sp.append((tr[0] + rnd.gauss(0, 16), tr[1] + rnd.gauss(0, 12)))

        # Fallen logs in forest / ruins
        if theme in ("forest", "ruins"):
            for _ in range(5):
                x, y = rnd.uniform(200, WW - 200), rnd.uniform(200, WH - 200)
                if not self.in_water(x, y, -20) and self.dist_to_path(x, y) > 40:
                    self.logs.append((x, y, rnd.uniform(0, 3.14)))
                    self.colliders.append((x, y, 14))

        # Shore life
        if self.water:
            for i in range(0, len(self.water), 6):
                wx, wy, wr = self.water[i]
                a = hash01(i + lvl * 3) * 6.28
                ox, oy = math.cos(a) * (wr + 10), math.sin(a) * (wr + 10) * 0.55
                if hash01(i * 3) > 0.5:
                    self.shore_rocks.append((wx + ox, wy + oy, 3 + hash01(i * 7) * 5))
                if hash01(i * 5) > 0.4:
                    self.reeds.append((wx + ox * 0.75, wy + oy * 0.75))
            if water_mode in ("river", "ponds"):
                for i in range(8, len(self.water) - 8, 12):
                    wx, wy, wr = self.water[i]
                    if wr > 50 and hash01(i * 11) > 0.6:
                        self.lily.append((wx + rnd.uniform(-wr * 0.3, wr * 0.3), wy + rnd.uniform(-wr * 0.2, wr * 0.2), rnd.uniform(0.8, 1.2)))

        # Bhutanese prayer flags & chortens (landmarks, not clutter)
        for _ in range(dens["flags"]):
            x, y = rnd.uniform(120, WW - 120), rnd.uniform(120, WH - 120)
            if not self.in_water(x, y, -20) and self.clear_of_pois(x, y, 50):
                self.prayer_flags.append((x, y, rnd.uniform(0.85, 1.3), rnd.randint(4, 8)))
        for _ in range(dens["chortens"]):
            x, y = rnd.uniform(200, WW - 200), rnd.uniform(200, WH - 200)
            if not self.in_water(x, y, -30) and self.clear_of_pois(x, y, 70) and self.dist_to_path(x, y) > 45:
                self.chortens.append((x, y, rnd.uniform(0.9, 1.35)))
                self.colliders.append((x, y, 12))
        if theme in ("temple", "ruins"):
            for _ in range(6):
                x, y = rnd.uniform(200, WW - 200), rnd.uniform(200, WH - 200)
                if not self.in_water(x, y, -25) and self.clear_of_pois(x, y, 60):
                    s = rnd.uniform(0.8, 1.3)
                    self.pillars.append((x, y, s))
                    self.colliders.append((x, y, 10 * s))

        # Snow patches on mountain themes
        self.snowp = []
        if theme == "mountain":
            for _ in range(8):
                self.snowp.append((rnd.uniform(150, WW - 150), rnd.uniform(150, WH - 150), rnd.uniform(50, 100)))

        # Keep bridge decks clear of trees/rocks so wood stays visible
        kept_trees = []
        for tr in self.trees:
            on_br = any(br.inflate(30, 30).collidepoint(tr[0], tr[1]) for br in self.bridges)
            if not on_br:
                kept_trees.append(tr)
            else:
                # drop matching collider near trunk
                self.colliders = [c for c in self.colliders if not (abs(c[0]-tr[0]) < 2 and abs(c[1]-tr[1]) < 2)]
        self.trees = kept_trees
        kept_rocks = []
        for rk in self.rocks:
            if any(br.inflate(20, 20).collidepoint(rk[0], rk[1]) for br in self.bridges):
                self.colliders = [c for c in self.colliders if not (abs(c[0]-rk[0]) < 2 and abs(c[1]-rk[1]) < 2)]
            else:
                kept_rocks.append(rk)
        self.rocks = kept_rocks

        self.base_colliders = list(self.colliders)

        # Wildlife — more in forests
        self.butterflies = []
        bf_cols = [(255, 180, 60), (255, 120, 160), (180, 140, 255), (120, 200, 255), (255, 220, 100)]
        n_bf = 45 if theme == "forest" else 22
        for _ in range(n_bf):
            hx, hy = rnd.uniform(100, WW - 100), rnd.uniform(100, WH - 100)
            if not self.in_water(hx, hy, -10):
                self.butterflies.append({"x": hx, "y": hy, "hx": hx, "hy": hy, "p": rnd.uniform(0, 6.28), "c": rnd.choice(bf_cols), "sz": rnd.uniform(0.7, 1.25)})
        # Rabbits prefer forest / meadow edges
        self.rabbits = []
        n_rab = 5 if theme == "forest" else 2
        for _ in range(n_rab):
            hx, hy = rnd.uniform(200, WW - 200), rnd.uniform(200, WH - 200)
            if not self.in_water(hx, hy, -15):
                self.rabbits.append({"x": float(hx), "y": float(hy), "hx": hx, "hy": hy, "t": rnd.uniform(0, 6), "hop": 0, "a": 0.0, "zone": pygame.Rect(hx - 160, hy - 120, 320, 240)})
        self.birds = []
        for i in range(5 if theme == "forest" else 3):
            if self.trees:
                hx, hy = rnd.choice(self.trees)[:2]
                self.birds.append({"x": float(hx), "y": float(hy), "hx": hx, "hy": hy, "st": "perch", "vx": 0, "vy": 0, "t": rnd.uniform(0, 4), "perch": (hx, hy), "wing": 0.0})

    def start_level(self, lvl):
        self.current_level = lvl
        self.biome = biome_for(lvl)
        self.biomes_visited.add(self.biome)
        if len(self.biomes_visited) >= 6: self.earn_ach("world_walker")
        self.weather = random.Random(lvl*13).choice(WEATHER_BY_BIOME.get(self.biome, ["sunshine"]))
        self.thunder_t = 0; self.flash_white = 0
        env = LEVEL_ENV.get(lvl, {"theme": "forest", "water": "stream", "label": BIOMES[self.biome]["name"]})
        self.level_env = env
        path_theme = {
            "forest": None, "village": "village", "mountain": "mountain",
            "temple": "temple", "ruins": "desert", "city": "village",
        }.get(env["theme"], None)
        # Fresh open layout per level (no shared cramped river-bridge map)
        self.build_path(path_theme)
        self.rebuild_open_world(lvl, env)
        # Hard guarantee: river/stream levels always have bridges
        if env.get("water") in ("river", "stream") and not getattr(self, "bridges", None):
            self.ensure_bridges(env.get("water", "river"), lvl)
        elif env.get("water") == "river" and len(getattr(self, "bridges", [])) < 1:
            self.ensure_bridges("river", lvl)
        self.build_terrain(); self.build_minimap_base()
        self.colliders = list(self.base_colliders)
        b = BIOMES[self.biome]
        if b.get("chortens") or b["amb"] == "ancient" or env["theme"] in ("temple", "ruins"):
            for x, y, s in self.pillars: self.colliders.append((x, y, 10*s))
        self.place_houses_for_level()
        # Force every house onto dry land (never river / bridge)
        for h in getattr(self, "houses", []) or []:
            if self.in_water(h["x"], h["y"], -25) or self.on_bridge(h["x"], h["y"]):
                # Push north of river band
                ry = sum(w[1] for w in self.water) / len(self.water) if self.water else WH * 0.5
                h["x"] = float(max(100, min(WW - 100, h["x"])))
                h["y"] = float(ry - 220)
                # spiral search for dry land
                for k in range(60):
                    ang = k * 0.7
                    tx = h["x"] + math.cos(ang) * (40 + k * 8)
                    ty = h["y"] + math.sin(ang) * (30 + k * 6)
                    if not self.in_water(tx, ty, -25) and not self.on_bridge(tx, ty):
                        h["x"], h["y"] = float(tx), float(ty)
                        break
        self.spawn_enemies(lvl)
        self.gen_level_content(lvl)
        self.place_outdoor_house_chest()
        self.build_extra()
        # Spawn near path start for each theme
        if self.path_pts:
            self.px, self.py = float(self.path_pts[0][0]), float(self.path_pts[0][1])
        self.camx, self.camy = self.px, self.py
        self.level_free_hints = 2  # 2 free map hints every level
        self.free_hints_left = 2
        self.fade_t = pygame.time.get_ticks()
        self.state = "PLAY"
        self.audio.play("quest")
        diff_label = "Easy" if lvl <= 3 else ("Medium" if lvl <= 6 else "Hard")
        # Final safety: river/stream always has full-span bridges
        if self.level_env.get("water") in ("river", "stream"):
            if not getattr(self, "bridges", None) or len(self.bridges) < 1:
                self.ensure_bridges(self.level_env.get("water", "river"), lvl)
        # Spawn just north of the nearest bridge so the crossing is discoverable
        if self.bridges and self.level_env.get("water") in ("river", "stream"):
            br = min(self.bridges, key=lambda b: abs(b.centerx - self.px) + abs(b.centery - self.py))
            # Stand on the north bank approach of the closest bridge
            self.px = float(br.centerx)
            self.py = float(br.top - 40)
            if self.blocked(self.px, self.py):
                self.py = float(br.bottom + 40)
            self.camx, self.camy = self.px, self.py
        self.say("Level %d (%s) — %s — Find %d treasure chest(s)!" % (lvl, diff_label, env.get("label", b["name"]), self.required_chests))

    def place_outdoor_house_chest(self):
        """Put the former interior house treasure outside near Mine House (all levels)."""
        ph = getattr(self, "player_house", None)
        if not ph:
            return
        # Offset in front of the house so it is clearly outside and reachable
        cx = ph["x"] + 55
        cy = ph["y"] + 40
        # Nudge if water / blocked
        if self.in_water(cx, cy, -10) or self.blocked(cx, cy):
            cx = ph["x"] - 55
            cy = ph["y"] + 35
        if self.in_water(cx, cy, -10):
            cx, cy = ph["x"] + 40, ph["y"] - 50
        q_data = self.pick_unique_question(self.current_level)
        self.chests.append({
            "x": cx, "y": cy,
            "opened": False,
            "rarity": "rare",
            "required": False,  # bonus chest; not needed to finish the level
            "question": q_data,
            "hint_level": 0,
            "hint": self.make_hint(cx, cy),
            "value": RARITY["rare"][0],
            "from_house": False,
        })

    def build_extra(self):
        rnd = random.Random(900 + self.current_level)
        self.extra = []
        b = BIOMES[self.biome]
        # Frogs near water in wetland / riverside / misty biomes
        if self.biome in (2, 6) or "Valley" in b["name"] or "Wetland" in b["name"]:
            for _ in range(4):
                i = rnd.randint(0, len(self.water)-1); wx, wy, wr = self.water[i]
                x, y = wx + wr + 30, wy
                self.extra.append({"kind": "frog", "x": x, "y": y, "t": rnd.uniform(0, 5), "hop": 0, "a": 0})
        # Goats / yaks in mountain biomes
        if b.get("mountains"):
            kind = "yak" if self.biome in (1, 5, 7) else "goat"
            for _ in range(3):
                x, y = rnd.uniform(200, WW-200), rnd.uniform(200, WH-200)
                self.extra.append({"kind": kind, "x": x, "y": y, "a": rnd.uniform(0, 6), "t": rnd.uniform(0, 4)})

    def say(self, msg):
        self.toast = msg; self.toast_t = pygame.time.get_ticks()

    def save_progress(self, silent=False):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump({"gold": self.gold, "current_level": self.current_level, "inventory": self.inventory,
                           "max_lives": self.max_lives, "perm_speed": self.perm_speed, "skin": self.skin, "skins": self.skins_owned, "gender": self.gender,
                           "stars": self.level_stars, "unlocked": self.level_unlocked, "ach": sorted(list(self.ach)),
                           "total_correct": self.total_correct, "total_chests": self.total_chests, "secret_chests_found": self.secret_chests_found, "quest_env": self.quest_env,
                           "hint_charges": getattr(self, "hint_charges", 0),
                           "free_hints_left": getattr(self, "free_hints_left", 2),
                           "resources": getattr(self, "resources", {k: 0 for k in RESOURCE_TYPES})}, f)
            if not silent:
                self.say("Progress saved.")
        except Exception:
            if not silent:
                self.say("Could not save.")

    def load_progress(self):
        if not os.path.exists(SAVE_FILE): return False
        try:
            with open(SAVE_FILE) as f: d = json.load(f)
            self.gold = d.get("gold", 0); self.current_level = d.get("current_level", 1)
            self.inventory = d.get("inventory", [])
            self.max_lives = d.get("max_lives", 8); self.perm_speed = d.get("perm_speed", False)
            self.skins_owned = d.get("skins", ["classic"]); self.skin = d.get("skin", "classic")
            self.gender = d.get("gender", "male")
            self.hint_charges = int(d.get("hint_charges", 0))
            self.free_hints_left = int(d.get("free_hints_left", 2))
            loaded_res = d.get("resources", {})
            self.resources = {k: int(loaded_res.get(k, 0)) for k in RESOURCE_TYPES}
            stars = list(d.get("stars", [0]*NUM_LEVELS))
            unlocked = list(d.get("unlocked", [True]+[False]*(NUM_LEVELS-1)))
            while len(stars) < NUM_LEVELS: stars.append(0)
            while len(unlocked) < NUM_LEVELS: unlocked.append(False)
            self.level_stars = stars[:NUM_LEVELS]
            self.level_unlocked = unlocked[:NUM_LEVELS]
            if not any(self.level_unlocked):
                self.level_unlocked[0] = True
            self.ach = set(d.get("ach", []))
            self.total_correct = d.get("total_correct", 0)
            self.total_chests = d.get("total_chests", 0)
            self.secret_chests_found = d.get("secret_chests_found", 0)
            self.quest_env = d.get("quest_env", 0)
            self.biome = biome_for(self.current_level)
            if not hasattr(self, "biomes_visited") or self.biomes_visited is None:
                self.biomes_visited = set()
            self.biomes_visited.add(self.biome)
            # Keep progress values only here; full world rebuild happens when a level is started.
            # Do not force state to MAP if still on intro/title.
            if getattr(self, "state", None) not in ("INTRO", "TITLE", None):
                self.state = "MAP"
            return True
        except Exception:
            return False

    def blocked(self, x, y):
        if not (24 < x < WW-24 and 24 < y < WH-24): return True
        if self.in_water(x, y, 6) and not self.on_bridge(x, y): return True
        for cx, cy, cr in self.colliders:
            if (x-cx)**2 + (y-cy)**2 < (cr+7)**2: return True
        return False

    def blocked_land(self, x, y, zone):
        if not zone.collidepoint(x, y): return True
        if self.in_water(x, y, -6) or self.on_bridge(x, y): return True
        for cx, cy, cr in self.colliders:
            if (x-cx)**2 + (y-cy)**2 < (cr+5)**2: return True
        return False

    def buy(self, item_id):
        now = pygame.time.get_ticks()
        if not hasattr(self, "resources"):
            self.resources = {k: 0 for k in RESOURCE_TYPES}
        # Gold prices (coins). Resource costs are extra for special trades.
        price = {
            "hint": 1200, "charm": 1500, "boots": 1800, "life": 2500,
            "staff": 3500, "boots2": 4500, "amulet": 5500,
            "skin_red": 7000, "skin_saffron": 8000, "skin_green": 7500,
            # Resource trades (lower gold + materials)
            "hint_scroll": 400, "charm_nature": 500, "life_relic": 800,
            "staff_gem": 1500, "boots2_gem": 2000, "amulet_artifact": 2500,
            "skin_red_trade": 2000, "skin_saffron_trade": 2500, "skin_green_trade": 2200,
            "bundle_hints": 0, "legend_boost": 0,
        }.get(item_id, None)
        if price is None:
            self.say("Unknown item."); return
        res_cost = {
            "hint_scroll": {"scroll": 1},
            "charm_nature": {"nature": 2},
            "life_relic": {"relic": 1},
            "staff_gem": {"gem": 3},
            "boots2_gem": {"gem": 4},
            "amulet_artifact": {"artifact": 1, "gem": 2},
            "skin_red_trade": {"relic": 2, "scroll": 1},
            "skin_saffron_trade": {"artifact": 1, "scroll": 2},
            "skin_green_trade": {"nature": 4, "relic": 1},
            "bundle_hints": {"scroll": 2, "gem": 1},
            "legend_boost": {"artifact": 1, "gem": 3, "relic": 1},
        }.get(item_id, {})
        # Map trade ids to effect ids
        effect = {
            "hint_scroll": "hint", "charm_nature": "charm", "life_relic": "life",
            "staff_gem": "staff", "boots2_gem": "boots2", "amulet_artifact": "amulet",
            "skin_red_trade": "skin_red", "skin_saffron_trade": "skin_saffron",
            "skin_green_trade": "skin_green", "bundle_hints": "bundle_hints",
            "legend_boost": "legend_boost",
        }.get(item_id, item_id)
        if effect in ("staff", "boots2", "amulet") and effect in self.inventory:
            self.say("Already owned."); return
        if effect == "skin_red" and "red" in self.skins_owned:
            self.skin = "red"; self.say("Wearing: Red Kabney."); return
        if effect == "skin_saffron" and "saffron" in self.skins_owned:
            self.skin = "saffron"; self.say("Wearing: Saffron Festival."); return
        if effect == "skin_green" and "green" in self.skins_owned:
            self.skin = "green"; self.say("Wearing: Gompo Herder."); return
        if self.gold < price:
            self.say("Not enough gold."); return
        for rk, need in res_cost.items():
            if int(self.resources.get(rk, 0)) < need:
                self.say("Need more %s." % RESOURCE_TYPES.get(rk, {}).get("name", rk)); return
        self.gold -= price
        for rk, need in res_cost.items():
            self.resources[rk] = int(self.resources.get(rk, 0)) - need
        self.audio.play("buy")
        item_id = effect  # apply using original effect logic below
        self.purchases += 1
        if self.purchases >= 3: self.earn_ach("merchant_friend")
        if item_id == "charm": self.shield_until = now + 6000; self.say("River charm: protected 6s!")
        elif item_id == "boots": self.boost_until = now + 6000; self.say("Swift boots: faster 6s!")
        elif item_id == "life": self.lives += 1; self.say("Herbal charm: +1 life!")
        elif item_id == "hint":
            self.hint_charges = int(getattr(self, "hint_charges", 0)) + 1
            self.say("Quiz hint bought! Total bought: %d (free left: %d). Press H in quiz." % (self.hint_charges, getattr(self, "free_hints_left", 0)))
            try: self.save_progress()
            except Exception: pass
        elif item_id == "staff": self.weapon = True; self.inventory.append("staff"); self.say("Wooden staff added! Press F to swing.")
        elif item_id == "boots2": self.perm_speed = True; self.inventory.append("boots2"); self.say("Iron Boots: permanent +10% speed!")
        elif item_id == "amulet": self.max_lives += 1; self.lives += 1; self.inventory.append("amulet"); self.say("Turquoise Amulet: +1 max life!")
        elif item_id == "skin_red": self.skins_owned.append("red"); self.skin = "red"; self.say("Unlocked Red Kabney!")
        elif item_id == "skin_saffron": self.skins_owned.append("saffron"); self.skin = "saffron"; self.say("Unlocked Saffron Festival!")
        elif item_id == "skin_green": self.skins_owned.append("green"); self.skin = "green"; self.say("Unlocked Gompo Herder!")
        elif item_id == "bundle_hints":
            self.hint_charges = int(getattr(self, "hint_charges", 0)) + 3
            self.say("Scroll bundle: +3 quiz hints!")
            try: self.save_progress()
            except Exception: pass
        elif item_id == "legend_boost":
            self.boost_until = now + 20000
            self.shield_until = now + 12000
            self.say("Legendary blessing: speed + shield!")


    def try_attack(self):
        if not self.weapon:
            if self.attack_cd <= 0:
                self.say("No weapon - the merchant sells a staff.")
                self.attack_cd = .8
            return
        if self.attack_cd > 0: return
        self.attack_cd = .5; self.attack_t = .18
        d = math.hypot(self.vx, self.vy)
        self.attack_dir = (self.vx/d, self.vy/d) if d > .3 else (float(self.face), 0.0)
        self.audio.play("swing")
        ax, ay = self.px + self.attack_dir[0]*24, self.py + self.attack_dir[1]*24
        for e in self.enemies[:]:
            if (e["x"]-ax)**2 + (e["y"]-ay)**2 < 32**2:
                e["hp"] -= 1
                e["x"] += self.attack_dir[0]*26; e["y"] += self.attack_dir[1]*26
                if e["hp"] <= 0:
                    self.enemies.remove(e)
                    self.gold += 5; self.audio.play("pop")
                    self.kills_this_level += 1
                    if self.kills_this_level >= 3: self.earn_ach("beast_slayer")
                    self.say("Threat cleared! +5 gold")
                    for _ in range(6):
                        self.parts.append({"x": e["x"], "y": e["y"], "vx": random.uniform(-1,1), "vy": random.uniform(-1.5,0), "l": 16, "c": (150,150,140)})
                else:
                    self.audio.play("hurt", .5)

    def goal_xy(self):
        return self.goal_xy_for(self.current_level)

    def update_play(self, now, dt):
        keys = pygame.key.get_pressed()
        dx = (1 if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) else 0) - (1 if (keys[pygame.K_a] or keys[pygame.K_LEFT]) else 0)
        dy = (1 if (keys[pygame.K_s] or keys[pygame.K_DOWN]) else 0) - (1 if (keys[pygame.K_w] or keys[pygame.K_UP]) else 0)
        self.running = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        if keys[pygame.K_SPACE] and self.dash_cd <= 0 and (dx or dy):
            self.dash_t = .22; self.dash_cd = 2.5
        self.dash_cd = max(0, self.dash_cd - dt); self.dash_t = max(0, self.dash_t - dt)
        self.attack_cd = max(0, self.attack_cd - dt); self.attack_t = max(0, self.attack_t - dt)
        maxsp = 5.2 * (1.32 if self.running else 1) * (1.3 if now < self.boost_until else 1) * (1.7 if self.dash_t else 1)
        if self.perm_speed: maxsp *= 1.1
        # Slow in snow patches on mountain biomes
        if BIOMES[self.biome].get("mountains"):
            for sxp, syp, sr in getattr(self, "snowp", []) or []:
                if (self.px-sxp)**2 + (self.py-syp)**2 < sr*sr:
                    maxsp *= 0.65; break
        # Desired facing from input (smoothed later)
        want_dir = self.direction
        if dx or dy:
            if abs(dx) > abs(dy) * 0.55:
                want_dir = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) * 0.55:
                want_dir = "down" if dy > 0 else "up"
            else:
                want_dir = ("right" if dx > 0 else "left") if abs(dx) >= abs(dy) else ("down" if dy > 0 else "up")
        # Smooth turn: only change sprite facing after a short settle (avoids flicker)
        if not hasattr(self, "_face_t"): self._face_t = 0.0
        if want_dir != self.direction and (dx or dy):
            self._face_t += dt
            if self._face_t > 0.05:
                self.direction = want_dir
                self.face = 1 if want_dir == "right" else (-1 if want_dir == "left" else self.face)
                self._face_t = 0.0
        else:
            self._face_t = 0.0
        if dx or dy:
            L = math.hypot(dx, dy)
            # Gradual acceleration — walk then settle into speed
            accel = 0.12 if self.running else 0.09
            if self.dash_t: accel = 0.35
            # Stronger pull when nearly stopped so first step feels responsive
            spd0 = math.hypot(self.vx, self.vy)
            if spd0 < 1.0:
                accel = min(0.28, accel + 0.1)
            self.vx = lerp(self.vx, dx / L * maxsp, accel)
            self.vy = lerp(self.vy, dy / L * maxsp, accel)
        else:
            # Gradual deceleration — friction, not instant stop
            friction = 0.88 if not self.running else 0.90
            self.vx *= friction; self.vy *= friction
            if abs(self.vx) < 0.06: self.vx = 0.0
            if abs(self.vy) < 0.06: self.vy = 0.0
        self.moving = math.hypot(self.vx, self.vy) > 0.25
        # Sub-step move for smoother collision (less sticky sliding)
        steps = 2
        for _ in range(steps):
            nx = self.px + self.vx / steps
            ny = self.py + self.vy / steps
            if not self.blocked(nx, self.py):
                self.px = nx
            else:
                self.vx *= 0.15
            if not self.blocked(self.px, ny):
                self.py = ny
            else:
                self.vy *= 0.15
        if self.moving:
            # Cadence locked to distance travelled → natural stride rate
            spd = math.hypot(self.vx, self.vy)
            cadence = 8.0 + min(8.0, spd * 2.2)
            if self.running or self.dash_t: cadence *= 1.2
            self.walk += dt * cadence
            if int(self.walk * 0.55) != int((self.walk - dt * cadence) * 0.55):
                surf = "wood" if self.on_bridge(self.px, self.py) else ("dirt" if self.dist_to_path(self.px, self.py) < 16 else "grass")
                self.audio.step(surf)
        if now > self.inv and now > self.shield_until:
            for tx, ty in self.thorns:
                if (self.px-tx)**2 + (self.py-ty)**2 < 26**2: self.hurt(now, tx, ty, 1)
            for br in self.brambles:
                if (self.px-br["x"])**2 + (self.py-br["y"])**2 < 24**2: self.hurt(now, br["x"], br["y"], 1)
        # Rockfalls on mountain / cliff biomes
        if BIOMES[self.biome].get("mountains"):
            for r in self.rockfalls[:]:
                age = (now - r["t"])/1000.0
                if age > 1.1 and (self.px-r["x"])**2 + (self.py-r["y"])**2 < 30**2:
                    self.hurt(now, r["x"], r["y"], 1)
            self.rock_t -= dt
            if self.rock_t <= 0:
                self.rock_t = random.uniform(3.0, 6.0)
                tx = clamp(self.px + random.uniform(-160,160), 40, WW-40)
                ty = clamp(self.py + random.uniform(-160,160), 40, WH-40)
                if not self.in_water(tx, ty, 0):
                    self.rockfalls.append({"x":tx, "y":ty, "t":now})
                    self.audio.play("rock", .5)
        for r in self.rockfalls[:]:
            age = (now - r["t"])/1000.0
            if age > 1.1:
                for _ in range(6):
                    self.parts.append({"x":r["x"], "y":r["y"], "vx":random.uniform(-1,1), "vy":random.uniform(-1.5,0), "l":16, "c":(140,140,140)})
                self.rockfalls.remove(r)
        if self.weather in ("rain", "thunderstorm"):
            for r in self.rain:
                r["y"] += r["s"]; r["x"] -= 1
                if r["y"] > H: r["y"] = -5; r["x"] = random.randint(0, W)
        if self.weather == "thunderstorm":
            self.thunder_t -= dt
            if self.thunder_t <= 0:
                self.thunder_t = random.uniform(4, 9)
                self.flash_white = now + 180
                self.audio.play("rock", .8)
        elif self.weather == "snow":
            for r in self.rain:
                r["y"] += r["s"]*0.4; r["x"] += math.sin(now*0.001 + r["y"]*0.05)*0.5
                if r["y"] > H: r["y"] = -5; r["x"] = random.randint(0, W)
        if self.weather == "wind":
            self.audio.fade("wind", .6)
        for e in self.enemies:
            pd = math.hypot(self.px-e["x"], self.py-e["y"])
            if pd < 90 and e.get("lunge", 0) <= 0:
                e["lunge"] = 0.6
                e["a"] = math.atan2(self.py-e["y"], self.px-e["x"])
            if e.get("lunge", 0) > 0: e["lunge"] -= dt
            if (self.px-e["x"])**2 + (self.py-e["y"])**2 < 20**2 and now > self.inv and now > self.shield_until:
                self.hurt(now, e["x"], e["y"], 1.6 if e["type"] == "CRAB" else 1)
        for c in self.coins[:]:
            if (self.px-c[0])**2 + (self.py-c[1])**2 < 22**2:
                self.coins.remove(c); self.gold += 25; self.audio.play("coin")
                self.burst_fx(c[0], c[1], C_GOLD, n=10, speed=2.0, life=20)
        for drop in getattr(self, "loot_drops", []) or []:
            if drop.get("got"): continue
            if (self.px - drop["x"])**2 + (self.py - drop["y"])**2 < 26**2:
                drop["got"] = True
                kind = drop["kind"]
                if not hasattr(self, "resources"):
                    self.resources = {k: 0 for k in RESOURCE_TYPES}
                self.resources[kind] = int(self.resources.get(kind, 0)) + 1
                self.audio.play("gem" if kind in ("gem", "artifact") else "coin")
                nm = RESOURCE_TYPES.get(kind, {}).get("name", kind)
                self.say("Found %s! (%d)" % (nm, self.resources[kind]))
        for r in self.rabbits:
            if "rabbit" not in self.seen and (self.px-r["x"])**2 + (self.py-r["y"])**2 < 60**2:
                self.seen.add("rabbit"); self.say("You observe a rabbit."); self.audio.play("chirp", .5)
        for b in self.birds:
            if "bird" not in self.seen and (self.px-b["x"])**2 + (self.py-b["y"])**2 < 70**2:
                self.seen.add("bird"); self.say("You observe a bird."); self.audio.play("chirp", .5)
        for f in self.fish:
            fx, fy = self.water_pos(f["t"], f["lat"])
            if "fish" not in self.seen and (self.px-fx)**2 + (self.py-fy)**2 < 80**2:
                self.seen.add("fish"); self.say("You observe a fish."); self.audio.play("chirp", .5)
        if len(self.seen) >= 3 and not self.wild_rewarded:
            self.wild_rewarded = True; self.gold += 120; self.earn_ach("wildlife_watcher")
            self.say("Wildlife watched! +30 gold")
            
        self.prompt = None; self.interact = None
        self.near_house = None
        self.near_npc = None
        self.can_enter_house = False
        cands = []
        for chest in self.chests:
            if not chest["opened"]:
                cands.append((chest["x"], chest["y"], 40, "Open Chest", ("chest", chest)))
        for f in self.forage:
            if not f["used"]:
                cands.append((f["x"], f["y"], 42, "Forage the bush", ("forage", f)))
        for i, tr in enumerate(self.trash):
            if not tr["got"]:
                cands.append((tr["x"], tr["y"], 40, "Pick up litter", ("trash", i)))
        for i, s in enumerate(self.saplings):
            if not s["planted"]:
                cands.append((s["x"], s["y"], 40, "Plant sapling", ("plant", i)))
        for i, lm in enumerate(self.landmarks):
            if not lm["used"]:
                lab = "Rest at hot spring" if lm["kind"] == "spring" else "Read ancient statue"
                cands.append((lm["x"], lm["y"], 46, lab, ("landmark", i)))
        for i, r in enumerate(self.runes):
            if not r["used"]:
                cands.append((r["x"], r["y"], 40, "Examine rune", ("rune", i)))
                
        bd = 1e18
        for x, y, rad, lab, key in cands:
            dd = (self.px-x)**2 + (self.py-y)**2
            if dd < rad*rad and dd < bd:
                bd = dd; self.prompt, self.interact = lab, key
        # NPCs – talk with C key
        npc_bd = 1e18
        for n in self.npcs:
            dd = (self.px-n["x"])**2 + (self.py-n["y"])**2
            if dd < 70*70 and dd < npc_bd:
                npc_bd = dd
                self.near_npc = n
                if self.prompt is None:
                    self.prompt = "Talk to " + n["name"] + " [C]"
        # Houses are visual only – no interior entry. Treasure stays outside.
        # Name display for any nearby house
        if self.near_house is None:
            nearest_d = 1e18
            for h in self.houses:
                dd = (self.px - h["x"])**2 + (self.py - h["y"])**2
                if dd < 100*100 and dd < nearest_d:
                    nearest_d = dd
                    self.near_house = h
        self.update_npcs(dt)
        self.update_creatures(now, dt)
        self.update_water_fx(now)
        for p in self.parts[:]:
            p["x"] += p.get("vx", 0); p["y"] += p.get("vy", 0); p["l"] -= 1
            if p["l"] <= 0: self.parts.remove(p)
        # soft camera follow – lag slightly more when running for a natural feel
        cam_lerp = 0.09 if self.running else 0.09
        self.camx = clamp(lerp(self.camx, self.px, cam_lerp), W/2, WW - W/2)
        self.camy = clamp(lerp(self.camy, self.py, cam_lerp), H/2, WH - H/2)
        wi, wd = self.nearest_water(self.px, self.py)
        b = BIOMES[self.biome]
        self.audio.fade("water", clamp(1 - (wd-60)/380, 0, 1)*.8)
        forest = min(math.hypot(self.px-300, self.py-300), math.hypot(self.px-1150, self.py-260), math.hypot(self.px-900, self.py-300))
        self.audio.fade("insect", clamp(1 - forest/380, 0, 1) * .5)
        self.audio.fade("cave", .45 if (b.get("chortens") or b["amb"] == "ancient") else clamp(1 - math.hypot(self.px-1880, self.py-500)/420, 0, 1)*.4)
        if self.weather != "wind":
            self.audio.fade("wind", .55 if b.get("mountains") else .25)
        self.audio.fade("crackle", .5 if "Bamboo" in b["name"] or "Misty" in b["name"] else 0.0)
        self.chirp_t -= dt * 1000
        if self.chirp_t <= 0:
            self.chirp_t = random.uniform(3500, 9000)
            self.audio.play("chirp", clamp(1 - forest/600, .1, .5))
        if self.biome in (0,3) and self.weather not in ("rain","thunderstorm"):
            for ff in self.fireflies:
                ff["p"] += dt
                ff["x"] = (ff["x"] + math.sin(ff["p"])*0.6) % W
                ff["y"] = (ff["y"] + math.cos(ff["p"]*0.8)*0.5) % H

    def hurt(self, now, fx, fy, power):
        self.lives -= 1; self.inv = now + 1300; self.flash = now + 220
        self.hits_taken += 1
        a = math.atan2(self.py - fy, self.px - fx)
        self.vx, self.vy = math.cos(a)*4*power, math.sin(a)*4*power
        self.audio.play("hurt")
        self.say("Ouch! -1 life  (%d left)" % max(0, self.lives))
        if self.lives <= 0: self.state = "OVER"

    def do_interact(self):
        kind, payload = self.interact
        if kind == "chest":
            chest = payload
            self.active_chest = chest
            self.setup_quiz_for_chest(chest)
            self.state = "QUIZ"
            self.audio.play("chest")
        elif kind == "talk":
            n = payload
            lines = []
            left = self.chests_left()
            if n["kind"] == "guide":
                lines.append("Karma: 'Welcome, explorer! Treasure chests hide knowledge in this land.'")
                if left > 0:
                    lines.append("Karma: 'You still need %d chest(s). Explore carefully — chests are hidden well.'" % left)
                else:
                    lines.append("Karma: 'All chests found! Head to the exit when you are ready.'")
                lines.append("Karma: 'Please do not litter. Our forests stay pure when we care for them.'")
            elif n["kind"] == "merchant":
                lines.append("Dawa: 'My shop has charms and gear — save your gold for what you need.'")
                lines.append("Dawa: 'Treasures left here: %d. Answer well and you will earn more gold.'" % left)
                lines.append("Dawa: 'Tip: recycle what you can, and never throw waste in the river.'")
            elif n["kind"] == "keeper":
                if self.quest_trees == 0:
                    self.quest_trees = 1
                    self.saplings = []
                    tries = 0
                    while len(self.saplings) < 3 and tries < 60:
                        tries += 1
                        x = clamp(self.px + random.uniform(-220,220), 60, WW-60)
                        y = clamp(self.py + random.uniform(-220,220), 60, WH-60)
                        if not self.in_water(x, y, -10): self.saplings.append({"x":x, "y":y, "planted":False})
                    lines.append("Pema: 'Our forest needs care. Please plant 3 saplings nearby.'")
                    lines.append("Pema: 'Trees hold soil, give oxygen, and shelter animals. Thank you!'")
                elif self.quest_trees == 1:
                    lines.append("Pema: 'Saplings planted: %d/3. Keep going — every tree counts.'" % sum(1 for s in self.saplings if s["planted"]))
                else:
                    lines.append("Pema: 'The forest thanks you. Protect trees, and they protect us.'")
            elif n["kind"] == "villager":
                if self.quest_trash == 0:
                    self.quest_trash = 1
                    lines.append("Sonam: 'Please pick up 5 piles of litter. Waste harms rivers and wildlife.'")
                    lines.append("Sonam: 'Keep Bhutan clean — recycle and never dump trash in nature.'")
                elif self.quest_trash == 1:
                    lines.append("Sonam: 'Litter picked: %d/5. Almost there!'" % sum(1 for t in self.trash if t["got"]))
                else:
                    lines.append("Sonam: 'The valley is clean. Save water, plant trees, care for animals!'")
            elif n["kind"] == "historian":
                lines.append("Dorji: 'These lands hold stories of the Wangchuck kings and dzongs.'")
                if left > 0:
                    lines.append("Dorji: 'History chests remain. Answer carefully — learning is treasure.'")
                lines.append("Dorji: 'Respect sacred places. Leave no litter among the ruins.'")
            elif n["kind"] == "environmentalist":
                lines.append("Tshering: 'Protect nature: no littering, plant trees, save water, care for animals.'")
                if self.quest_trash == 1:
                    lines.append("Tshering: 'Litter left: %d. Pick it up for cleaner rivers.'" % sum(1 for t in self.trash if not t["got"]))
                elif self.quest_trees == 1:
                    lines.append("Tshering: 'Saplings left: %d. Roots hold the soil.'" % sum(1 for s in self.saplings if not s["planted"]))
                else:
                    lines.append("Tshering: 'Explore gently. Wildlife needs quiet forests and clean paths.'")
            if n["state"] != "IDLE":
                n["paused_state"] = n["state"]; n["state"] = "IDLE"
            self.dialog = n; self.dialog_idx = 0; self.dialog_lines = lines
            self.audio.play("chirp", .5)
        elif kind == "forage":
            f = payload; f["used"] = True
            self.forage_count += 1
            if self.forage_count >= 5: self.earn_ach("naturalist")
            r = random.random()
            if r < 0.4:
                self.gold += 40; self.audio.play("coin")
                if not hasattr(self, "resources"): self.resources = {k: 0 for k in RESOURCE_TYPES}
                if random.random() < 0.55:
                    self.resources["nature"] = int(self.resources.get("nature", 0)) + 1
                    self.say("Forage: coin + Nature Item!")
                else:
                    self.say("You find a hidden coin! +40 gold")
            elif r < 0.65:
                if self.lives < self.max_lives:
                    self.lives += 1; self.audio.play("gem"); self.say("Sweet berries! +1 life")
                else:
                    self.gold += 35; self.audio.play("coin"); self.say("Berries sold for +35 gold")
            else:
                self.audio.play("pop"); self.say("Just leaves and a ladybird...")
        elif kind == "trash":
            tr = self.trash[payload]; tr["got"] = True
            self.gold += 30; self.audio.play("pop")
            if self.quest_trash == 1 and all(q["got"] for q in self.trash):
                self.quest_trash = 2; self.gold += 150; self.earn_ach("valley_cleaner")
                self.quest_env += 1
                if self.quest_env >= 3: self.earn_ach("nature_guardian")
                self.say("Valley cleaned! +150 gold")
            else:
                self.say("Litter picked up. +30 gold")
        elif kind == "plant":
            s = self.saplings[payload]; s["planted"] = True
            self.audio.play("plant")
            if self.quest_trees == 1 and all(q["planted"] for q in self.saplings):
                self.quest_trees = 2; self.gold += 150; self.earn_ach("green_thumb")
                self.quest_env += 1
                if self.quest_env >= 3: self.earn_ach("nature_guardian")
                self.say("Reforested! +150 gold")
            else:
                self.say("Sapling planted. Trees protect soil and air.")
        elif kind == "landmark":
            lm = self.landmarks[payload]
            lm["used"] = True
            if lm["kind"] == "spring":
                if self.lives < self.max_lives: self.lives += 1
                self.earn_ach("spring_bather"); self.audio.play("splash")
                for _ in range(10):
                    self.parts.append({"x": lm["x"], "y": lm["y"], "vx": random.uniform(-.5,.5), "vy": random.uniform(-1.5,-.5), "l": 24, "c": (220,240,250)})
                self.say("The hot spring restores you. +1 life")
            else:
                self.earn_ach("lore_seeker"); self.audio.play("clue")
                self.say("The statue whispers a secret.")
        elif kind == "rune":
            r = self.runes[payload]
            r["used"] = True
            self.gold += 10; self.audio.play("clue")
            self.say("Ancient rune deciphered! +10 gold")
        # enter_house removed – houses are non-enterable; treasure is outside

    def advance_dialog(self):
        self.dialog_idx += 1
        if self.dialog_idx >= len(self.dialog_lines):
            n = self.dialog
            if n.get("paused_state"):
                n["state"] = n["paused_state"]; n["paused_state"] = None; n["timer"] = 1.2
            self.dialog = None
        else:
            self.audio.play("chirp", .4)

    def complete_level(self):
        # Ensure arrays are long enough (guards old / short saves)
        while len(self.level_stars) < NUM_LEVELS:
            self.level_stars.append(0)
        while len(self.level_unlocked) < NUM_LEVELS:
            self.level_unlocked.append(False)
        stars = 3 if self.lives >= 6 else (2 if self.lives >= 3 else 1)
        idx = max(0, min(NUM_LEVELS - 1, self.current_level - 1))
        self.level_stars[idx] = max(self.level_stars[idx], stars)
        # Unlock this level and the next (1-based current → next index == current_level)
        self.level_unlocked[idx] = True
        if self.current_level < NUM_LEVELS:
            self.level_unlocked[self.current_level] = True
        # Safety: unlock every level up to the next one so progression never soft-locks
        for i in range(min(self.current_level + 1, NUM_LEVELS)):
            self.level_unlocked[i] = True
        try:
            self.save_progress()
        except Exception:
            pass
        bonus = 120 + self.quiz_correct * 40 + self.best_streak * 15
        self.gold += bonus
        self.reward_bonus = bonus
        if self.current_level == 1: self.earn_ach("first_steps")
        if self.chests_opened == self.required_chests: self.earn_ach("treasure_hunter")
        if self.hits_taken == 0 and self.quiz_wrong == 0: self.earn_ach("perfect_level")
        if self.total_correct >= 20: self.earn_ach("scholar")
        if self.total_correct >= 50: self.earn_ach("brain_master")
        if self.total_chests >= 25: self.earn_ach("treasure_hunter")
        if self.secret_chests_found >= 5: self.earn_ach("explorer")
        
        self.done_t = pygame.time.get_ticks()
        self.burst_fx(self.px, self.py, C_GOLD, n=28, speed=3.5, life=40)
        self.ring_fx(self.px, self.py, M_YELLOW, n=16)
        if self.current_level >= NUM_LEVELS:
            self.audio.play("gamecomplete")
            self.audio.play("fanfare")
            self.state = "GAME_COMPLETE"
        else:
            self.audio.play("levelup")
            self.audio.play("win", 0.5)
            self.state = "LEVEL_DONE"

    def resolve_quiz(self, chosen_idx):
        correct = (chosen_idx == self.quiz_ans)
        self.last_quiz = (correct, self.quiz_fact, self.quiz_opts[chosen_idx], self.quiz_answer)
        if correct:
            self.quiz_correct += 1
            self.total_correct += 1
            self.streak += 1; self.best_streak = max(self.best_streak, self.streak)
            if self.streak >= 4: self.earn_ach("scholar")
            rem = max(0, 20 - (pygame.time.get_ticks() - self.quiz_start)/1000)
            # 100–200+ gold; harder (higher streak / speed) pays more
            reward = 100 + min(60, self.streak * 12) + (40 if rem > 12 else (20 if rem > 6 else 0))
            if getattr(self, "active_chest", None) and self.active_chest.get("rarity") in ("rare", "epic", "legendary"):
                reward += 50
            self.gold += reward
            self.audio.play("correct")
            self.audio.play("coin", 0.4)
            self.burst_fx(self.px, self.py - 10, C_GREEN_OK, n=16, speed=2.8, life=26)
            self.feedback_msg = "CORRECT!"
            self.feedback_col = C_GREEN_OK
            self.say("Correct! %s" % (self.quiz_fact[:60] if self.quiz_fact else "+%d gold" % reward))
            
            if self.active_chest is not None:
                chest = self.active_chest
                chest["opened"] = True
                if chest.get("from_house"):
                    self.house_chest_opened = True
                    val = chest.get("value", 25)
                    self.gold += val
                    self.say("Home chest opened! +%d gold" % (reward + val))
                    self.active_chest = None
                else:
                    self.chests_opened += 1
                    self.total_chests += 1
                    if not chest.get("required", True):
                        self.secret_chests_found += 1
                    val = chest["value"]
                    self.gold += val
                    # Chance for a resource find from the chest
                    if not hasattr(self, "resources"):
                        self.resources = {k: 0 for k in RESOURCE_TYPES}
                    roll = random.random()
                    if roll < 0.35:
                        rk = random.choice(["gem", "scroll", "relic", "nature"] + (["artifact"] if chest.get("rarity") in ("rare", "epic") else []))
                        self.resources[rk] = int(self.resources.get(rk, 0)) + 1
                        self.say("Chest held a %s!" % RESOURCE_TYPES[rk]["name"])
                    rarity_col = RARITY[chest["rarity"]][1]
                    self.burst_fx(chest["x"], chest["y"], rarity_col, n=22, speed=3.2, life=34)
                    self.ring_fx(chest["x"], chest["y"], C_GOLD, n=12)
                    self.audio.play("open")
                    self.audio.play("fanfare", 0.35)
                    self.active_chest = None
                    remaining = self.chests_left()
                    if remaining > 0:
                        self.say("Chest opened! +%d gold - %d chest(s) left" % (reward + val, remaining))
                    else:
                        self.say("All chests opened! Level complete! +%d gold" % (reward + val))
                        self.quiz_feedback_t = pygame.time.get_ticks() + 1500
                        return
        else:
            self.quiz_wrong += 1
            self.streak = 0
            self.lives -= 1
            self.gold = max(0, self.gold - 5)
            self.audio.play("wrong")
            # Do not reveal the correct answer — player must learn by trying again
            self.feedback_msg = "WRONG!"
            self.feedback_col = C_RED_BAD
            self.say("Wrong! -1 life, -5 gold. Try the next challenge!")
            if self.lives <= 0:
                self.state = "OVER"; return
                
        self.quiz_feedback_t = pygame.time.get_ticks() + 1500

    def update_npcs(self, dt):
        for n in self.npcs:
            # Rescue if somehow stuck in water
            if self.in_water(n["x"], n["y"], 8):
                self.rescue_npc_from_water(n)
            if self.dialog is n:
                n["phase"] += dt * 3
                continue
            n["timer"] -= dt
            st = n["state"]
            if st == "IDLE":
                n["phase"] += dt * 2
                if n["timer"] <= 0:
                    if self.pick_npc_target(n):
                        n["state"] = "WALKING"
                        n["timer"] = random.uniform(4.0, 7.0)
                    else:
                        n["timer"] = random.uniform(0.5, 1.2)
            elif st == "WALKING":
                dx, dy = n["tx"] - n["x"], n["ty"] - n["y"]
                dist = math.hypot(dx, dy)
                if dist < 8 or n["timer"] <= 0:
                    n["state"] = "WORKING"
                    n["timer"] = random.uniform(1.2, 2.5)
                    n["phase"] = 0.0
                else:
                    ux, uy = dx / dist, dy / dist
                    sp = n["speed"] * 1.15  # slightly faster so walks are visible
                    nx, ny = n["x"] + ux * sp, n["y"] + uy * sp
                    if self.npc_blocked(nx, ny):
                        moved = False
                        for side in (0.8, -0.8, 1.5, -1.5, 2.4, -2.4):
                            sa = math.atan2(uy, ux) + side
                            ax = n["x"] + math.cos(sa) * sp
                            ay = n["y"] + math.sin(sa) * sp
                            if not self.npc_blocked(ax, ay):
                                nx, ny = ax, ay
                                moved = True
                                break
                        if not moved:
                            # give up this target, pick a new one soon
                            n["state"] = "IDLE"
                            n["timer"] = random.uniform(0.3, 0.8)
                            continue
                    if abs(ux) > 0.15:
                        n["face"] = 1 if ux > 0 else -1
                    n["x"], n["y"] = nx, ny
                    n["phase"] += dt * 10
            elif st == "WORKING":
                n["phase"] += dt * 6
                if n["timer"] <= 0:
                    n["state"] = "IDLE"
                    n["timer"] = random.uniform(0.4, 1.2)

    def rescue_npc_from_water(self, n):
        """Push NPC to nearest dry ground near home."""
        hx, hy = n["home"]
        for d in range(20, 200, 15):
            for a in range(0, 360, 30):
                rad = math.radians(a)
                x = hx + math.cos(rad) * d
                y = hy + math.sin(rad) * d
                if not self.npc_blocked(x, y):
                    n["x"], n["y"] = x, y
                    n["tx"], n["ty"] = x, y
                    n["state"] = "IDLE"
                    n["timer"] = 0.4
                    return
        # fallback: home if dry, else fixed village
        if not self.npc_blocked(hx, hy):
            n["x"], n["y"] = float(hx), float(hy)
        else:
            n["x"], n["y"] = 430.0, 980.0

    def npc_blocked(self, x, y):
        if not (50 < x < WW - 50 and 50 < y < WH - 50):
            return True
        # stay clearly out of river / ponds
        if self.in_water(x, y, 12):
            return True
        if self.on_bridge(x, y):
            return True
        for cx, cy, cr in self.colliders:
            if (x - cx) ** 2 + (y - cy) ** 2 < (cr + 14) ** 2:
                return True
        for tx, ty in self.thorns:
            if (x - tx) ** 2 + (y - ty) ** 2 < 32 ** 2:
                return True
        return False

    def pick_npc_target(self, n):
        hx, hy = n["home"]
        R = n["radius"]
        # prefer dry spots around home; try many times
        for _ in range(60):
            a = random.uniform(0, 6.283)
            d = random.uniform(30, max(40, R))
            x = hx + math.cos(a) * d
            y = hy + math.sin(a) * d
            if not self.npc_blocked(x, y):
                n["tx"], n["ty"] = x, y
                return True
        # try along path near home
        if self.path_pts:
            near = [p for p in self.path_pts if math.hypot(p[0] - hx, p[1] - hy) < R + 80]
            random.shuffle(near)
            for px, py in near[:20]:
                a = random.uniform(0, 6.283)
                x = px + math.cos(a) * random.uniform(12, 28)
                y = py + math.sin(a) * random.uniform(10, 24)
                if not self.npc_blocked(x, y):
                    n["tx"], n["ty"] = x, y
                    return True
        n["tx"], n["ty"] = n["x"], n["y"]
        return False

    def update_creatures(self, now, dt):
        mult = 1 + (self.current_level - 1) * 0.07
        for e in self.enemies:
            e["t"] += dt
            sp = e["sp"] * mult
            lunging = e.get("lunge", 0) > 0
            espd = sp * (2.2 if lunging else 1.0)
            if e["type"] == "SNAKE":
                e["ph"] = e.get("ph", 0.0) + dt
                if not lunging: e["a"] += math.sin(e["ph"] * 2.0) * dt * 1.6
                nx, ny = e["x"] + math.cos(e["a"]) * espd, e["y"] + math.sin(e["a"]) * espd
                if not self.blocked_land(nx, ny, e["zone"]):
                    e["x"], e["y"] = nx, ny
                else:
                    e["a"] += 3.14
                e["seg"].insert(0, (e["x"], e["y"]))
                if len(e["seg"]) > 10: e["seg"] = e["seg"][:10]
            else:
                waiting = e.get("wait", 0.0) > 0 and not lunging
                if waiting:
                    e["wait"] = e.get("wait", 0.0) - dt
                else:
                    nx, ny = e["x"] + math.cos(e["a"]) * espd * 1.5, e["y"] + math.sin(e["a"]) * espd * 1.5
                    if not self.blocked_land(nx, ny, e["zone"]):
                        e["x"], e["y"] = nx, ny
                    else:
                        e["a"] += 2.4
                    e["mv"] = e.get("mv", 0.6) - dt
                    if e["mv"] <= 0:
                        e["wait"] = random.uniform(0.3, 0.8)
                        e["mv"] = random.uniform(0.4, 0.9)
                    if not lunging: e["a"] += random.uniform(-0.7, 0.7)
                    e["leg"] = e.get("leg", 0.0) + dt * (18 if (not waiting or lunging) else 3)
        for w in self.worms:
            w["ph"] += dt * 3
            if w.get("bur", 0) > 0:
                w["bur"] -= dt
            else:
                w["a"] += math.sin(w["ph"] * 0.5) * dt * 1.2
                nx = w["x"] + math.cos(w["a"]) * w["sp"] * dt
                ny = w["y"] + math.sin(w["a"]) * w["sp"] * dt
                if 60 < nx < WW-60 and 60 < ny < WH-60 and not self.in_water(nx, ny, -6):
                    w["x"], w["y"] = nx, ny
                else:
                    w["a"] += 3.14
                if random.random() < 0.002: w["bur"] = random.uniform(0.5, 1.2)
                w["seg"].insert(0, (w["x"], w["y"]))
                if len(w["seg"]) > 14: w["seg"] = w["seg"][:14]
        for b in self.bugs:
            b["ph"] += dt
            b["turn"] -= dt
            if b["turn"] <= 0:
                b["a"] += random.uniform(-1.0, 1.0)
                b["turn"] = random.uniform(0.3, 1.1)
            sp2 = b["sp"] * (0.5 + abs(math.sin(b["ph"] * 2)))
            nx = b["x"] + math.cos(b["a"]) * sp2 * dt
            ny = b["y"] + math.sin(b["a"]) * sp2 * dt
            if 60 < nx < WW-60 and 60 < ny < WH-60 and not self.in_water(nx, ny, -6):
                b["x"], b["y"] = nx, ny
            else:
                b["a"] += 3.14; b["turn"] = 0
        for r in self.rabbits:
            r["t"] += dt
            if r["hop"] > 0:
                r["hop"] -= dt
                nx, ny = r["x"] + math.cos(r["a"])*1.6, r["y"] + math.sin(r["a"])*1.6
                if not self.blocked_land(nx, ny, r["zone"]): r["x"], r["y"] = nx, ny
            elif r["t"] > 2.2:
                r["t"] = 0; r["hop"] = .4
                r["a"] = math.atan2(r["hy"]-r["y"], r["hx"]-r["x"]) + random.uniform(-1, 1)
        for b in self.birds:
            b["wing"] = b.get("wing", 0.0) + dt * 10
            d = math.hypot(self.px-b["x"], self.py-b["y"])
            if b["st"] == "perch":
                if b["t"] > 0: b["t"] -= dt
                if d < 60:
                    b["st"] = "fly"; b["t"] = 2.0
                    a = math.atan2(b["y"]-self.py, b["x"]-self.px)
                    b["vx"], b["vy"] = math.cos(a)*2.5, math.sin(a)*2.5 - 1
                elif b["t"] <= 0:
                    b["st"] = "fly"; b["t"] = 2.5
                    tgt = random.choice(self.trees)[:2] if self.trees else (b["hx"], b["hy"])
                    a = math.atan2(tgt[1]-b["y"], tgt[0]-b["x"])
                    b["vx"], b["vy"] = math.cos(a)*2.5, math.sin(a)*2.5
            else:
                b["x"] += b["vx"]; b["y"] += b["vy"]
                b["x"] = clamp(b["x"], 40, WW-40); b["y"] = clamp(b["y"], 40, WH-40)
                if b["t"] > 0: b["t"] -= dt
                else:
                    b["st"] = "perch"; b["t"] = random.uniform(2, 5); b["perch"] = (b["x"], b["y"])
        for bf in self.butterflies:
            bf["p"] += dt * 1.6
            bf["x"] = bf["hx"] + math.sin(bf["p"])*34; bf["y"] = bf["hy"] + math.cos(bf["p"]*1.2)*24
        for f in self.fish:
            f["t"] += f["sp"] * dt * 60
            if f["t"] < 6 or f["t"] > len(self.water)-6:
                f["sp"] *= -1; f["t"] = clamp(f["t"], 6, len(self.water)-6)
        for d in self.ducks:
            d["t"] += d["sp"] * dt * 60 * (1 if math.sin(now*.0004 + d["ph"]) > -.6 else -1)
            d["t"] = clamp(d["t"], 40, len(self.water)-40)
        for fl in self.float_leaves:
            fl["t"] += fl["sp"] * dt * 60
            if fl["t"] > len(self.water)-6: fl["t"] = 6
        for d in self.extra:
            if d["kind"] == "frog":
                d["t"] += dt
                if d["hop"] > 0:
                    d["hop"] -= dt; d["x"] += math.cos(d["a"])*1.2; d["y"] += math.sin(d["a"])*1.2
                elif d["t"] > 2.5:
                    d["t"] = 0; d["hop"] = .35; d["a"] = random.uniform(0, 6.28)
            elif d["kind"] == "bat":
                d["p"] += dt*2
                d["x"] = d["hx"] + math.sin(d["p"])*60; d["y"] = d["hy"] + math.sin(d["p"]*1.7)*30
            else:
                d["t"] += dt
                if d["t"] > 3:
                    d["t"] = 0; d["a"] = random.uniform(0, 6.28)
                    d["x"] = clamp(d["x"] + math.cos(d["a"])*.5, 60, WW-60)
                    d["y"] = clamp(d["y"] + math.sin(d["a"])*.5, 60, WH-60)
        amb = BIOMES[self.biome]["amb"]
        for lf in self.leaves:
            if amb == "snow" or self.weather == "snow":
                lf["y"] += lf["speed"]*0.8; lf["x"] += math.sin(lf["sway"])*0.6; lf["sway"] += 0.02
            elif amb == "ember":
                lf["y"] -= lf["speed"]*0.7; lf["x"] += math.sin(lf["sway"])*0.5; lf["sway"] += 0.05
            if lf["y"] < -20: lf["y"] = H+10; lf["x"] = random.randint(0, W)
            else:
                wf = 1.6 if self.weather == "wind" else 1.0
                lf["y"] += lf["speed"]; lf["x"] += math.sin(lf["sway"])*0.8*wf; lf["sway"] += 0.04
                if lf["y"] > H+20: lf["y"] = -20; lf["x"] = random.randint(0, W)

    def water_pos(self, t, lat):
        if not self.water or len(self.water) < 2:
            return 0.0, 0.0
        i = clamp(int(t), 0, len(self.water)-2); f = t - i
        x = lerp(self.water[i][0], self.water[i+1][0], f); y = lerp(self.water[i][1], self.water[i+1][1], f)
        r = lerp(self.water[i][2], self.water[i+1][2], f)
        dx = self.water[i+1][0]-self.water[i][0]; dy = self.water[i+1][1]-self.water[i][1]
        L = math.hypot(dx, dy) or 1
        return x + (-dy/L)*lat*r*.6, y + (dx/L)*lat*r*.6

    def update_water_fx(self, now):
        if len(getattr(self, "water", []) or []) < 8:
            return
        if hash01(now // 400) > .985 and len(self.ripples) < 9:
            i = random.randint(4, len(self.water)-4)
            self.ripples.append({"x": self.water[i][0], "y": self.water[i][1], "r": 2, "a": 70})
        for rp in self.ripples[:]:
            rp["r"] += .45; rp["a"] -= 1.4
            if rp["a"] <= 0: self.ripples.remove(rp)

    def draw_item_icon(self, iid, x, y, size=1.0):
        """Compact item glyph for shop cards (size scales radius-ish)."""
        s = size
        if iid in ("hint", "thint", "hint_scroll", "bundle_hints"):
            c = (140, 200, 230) if "hint" in iid or iid == "thint" else (235, 215, 130)
            pygame.draw.rect(self.screen, (70, 78, 95), (int(x - 8 * s), int(y - 9 * s), int(16 * s), int(18 * s)), border_radius=3)
            pygame.draw.rect(self.screen, (100, 110, 130), (int(x - 8 * s), int(y - 9 * s), int(16 * s), int(18 * s)), 1, border_radius=3)
            q = self.small.render("?", True, c)
            self.screen.blit(q, (x - q.get_width() // 2, y - q.get_height() // 2 - 1))
        elif iid in ("charm", "charm_nature"):
            pygame.draw.circle(self.screen, (40, 90, 100), (x, y + 1), int(9 * s))
            pygame.draw.circle(self.screen, (90, 190, 210), (x, y), int(8 * s))
            pygame.draw.circle(self.screen, (200, 240, 250), (x - 2, y - 2), int(3 * s))
            pygame.draw.circle(self.screen, C_GOLD, (x, y), int(8 * s), 1)
        elif iid in ("boots", "boots2", "boots2_gem"):
            c = (150, 110, 60) if iid == "boots" else (120, 125, 140)
            hi = lighten(c, 30)
            pygame.draw.rect(self.screen, darken(c, 25), (int(x - 7 * s), int(y - 6 * s), int(8 * s), int(10 * s)), border_radius=2)
            pygame.draw.rect(self.screen, c, (int(x - 7 * s), int(y + 2 * s), int(14 * s), int(6 * s)), border_radius=2)
            pygame.draw.rect(self.screen, hi, (int(x - 5 * s), int(y - 4 * s), int(4 * s), int(4 * s)), border_radius=1)
        elif iid in ("life", "life_relic"):
            pygame.draw.circle(self.screen, C_HEART, (int(x - 4 * s), int(y - 2 * s)), int(5 * s))
            pygame.draw.circle(self.screen, C_HEART, (int(x + 4 * s), int(y - 2 * s)), int(5 * s))
            pygame.draw.polygon(self.screen, C_HEART, [(int(x - 9 * s), y), (int(x + 9 * s), y), (x, int(y + 9 * s))])
            pygame.draw.circle(self.screen, lighten(C_HEART, 40), (int(x - 5 * s), int(y - 3 * s)), int(2 * s))
        elif iid in ("staff", "staff_gem"):
            pygame.draw.line(self.screen, (90, 60, 35), (int(x - 5 * s), int(y + 9 * s)), (int(x + 5 * s), int(y - 9 * s)), max(2, int(3 * s)))
            pygame.draw.line(self.screen, (160, 120, 70), (int(x - 4 * s), int(y + 8 * s)), (int(x + 4 * s), int(y - 8 * s)), max(1, int(2 * s)))
            pygame.draw.circle(self.screen, (180, 220, 230), (int(x + 5 * s), int(y - 9 * s)), int(3 * s))
            pygame.draw.circle(self.screen, C_GOLD, (int(x + 5 * s), int(y - 9 * s)), int(3 * s), 1)
        elif iid in ("amulet", "amulet_artifact"):
            pygame.draw.line(self.screen, C_GOLD, (x, int(y - 10 * s)), (x, int(y - 3 * s)), 2)
            pygame.draw.polygon(self.screen, (60, 160, 180), [
                (x, int(y - 3 * s)), (int(x + 7 * s), int(y + 3 * s)),
                (x, int(y + 9 * s)), (int(x - 7 * s), int(y + 3 * s))
            ])
            pygame.draw.polygon(self.screen, (120, 220, 235), [
                (x, int(y - 1 * s)), (int(x + 4 * s), int(y + 3 * s)),
                (x, int(y + 7 * s)), (int(x - 4 * s), int(y + 3 * s))
            ])
        elif iid == "legend_boost":
            pygame.draw.circle(self.screen, (80, 50, 120), (x, y), int(9 * s))
            pygame.draw.circle(self.screen, (180, 120, 220), (x, y), int(7 * s))
            mstar(self.screen, x, y, int(5 * s), C_GOLD)
        elif iid.startswith("skin_"):
            sid = iid.replace("skin_", "").replace("_trade", "").split("_")[0]
            if sid not in SKINS:
                sid = "classic"
            c = SKINS[sid]["robe"]
            sash = SKINS[sid].get("sash", C_GOLD)
            pygame.draw.rect(self.screen, darken(c, 30), (int(x - 8 * s), int(y - 8 * s), int(16 * s), int(16 * s)), border_radius=4)
            pygame.draw.rect(self.screen, c, (int(x - 7 * s), int(y - 7 * s), int(14 * s), int(14 * s)), border_radius=3)
            pygame.draw.line(self.screen, sash, (int(x - 6 * s), int(y - 5 * s)), (int(x + 6 * s), int(y + 5 * s)), 2)
            pygame.draw.rect(self.screen, C_GOLD, (int(x - 8 * s), int(y - 8 * s), int(16 * s), int(16 * s)), 1, border_radius=4)
        else:
            pygame.draw.circle(self.screen, (180, 140, 40), (x, y), int(8 * s))
            pygame.draw.circle(self.screen, C_GOLD, (x, y), int(6 * s))

    def draw_npc(self, n, now):
        ox, oy = int(W/2 - self.camx), int(H/2 - self.camy)
        sx, sy = int(n["x"]+ox), int(n["y"]+oy)
        vis = pygame.Rect(self.camx - W/2 - 60, self.camy - H/2 - 60, W + 120, H + 120)
        if not vis.collidepoint(n["x"], n["y"]): return
        st = n["state"]; f = n["face"]
        soft_shadow(self.screen, sx, sy - 2, 15, 7, 110)
        if st == "WALKING":
            bob = int(math.sin(n["phase"])*2); swing = int(math.sin(n["phase"])*3); lean = 0
        elif st == "WORKING":
            bob = int(abs(math.sin(n["phase"]))*-3); swing = 0; lean = int(math.sin(n["phase"])*4*f)
        else:
            bob = int(math.sin(n["phase"])*1); swing = 0; lean = 0
        robe = n["robe"]
        pygame.draw.rect(self.screen, darken((220,215,208), 25), (sx-6+swing, sy-8-bob, 5, 7))
        pygame.draw.rect(self.screen, (224,220,214), (sx+1-swing, sy-8-bob, 5, 7))
        pygame.draw.rect(self.screen, (30,30,34), (sx-7+swing, sy-3-bob, 6, 5), border_radius=1)
        pygame.draw.rect(self.screen, (35,35,40), (sx+1-swing, sy-3-bob, 6, 5), border_radius=1)
        pygame.draw.rect(self.screen, darken(robe, 25), (sx-10+lean, sy-30-bob, 20, 24), border_radius=4)
        pygame.draw.rect(self.screen, robe, (sx-8+lean, sy-30-bob, 16, 23), border_radius=4)
        pygame.draw.rect(self.screen, lighten(robe, 22), (sx-7+lean, sy-29-bob, 5, 20), border_radius=3)
        pygame.draw.rect(self.screen, (60,42,22), (sx-10+lean, sy-16-bob, 20, 4))
        if st == "WORKING":
            reach = int(math.sin(n["phase"])*6)
            if n["work"] == "chop":
                pygame.draw.line(self.screen, (150,110,70), (sx+8*f+lean, sy-22-bob), (sx+(20+reach)*f+lean, sy-30-bob-abs(reach)), 3)
                pygame.draw.rect(self.screen, (180,180,185), (sx+(18+reach)*f+lean-2, sy-34-bob-abs(reach), 5, 5))
            elif n["work"] == "gather":
                pygame.draw.rect(self.screen, robe, (sx+7*f+lean, sy-24-bob+reach, 6, 8))
                pygame.draw.circle(self.screen, (120,180,90), (sx+12*f+lean, sy-18-bob+reach), 3)
            else:
                pygame.draw.line(self.screen, (150,110,70), (sx+6*f+lean, sy-20-bob), (sx+10*f+lean, sy-2-bob+abs(reach)), 2)
                pygame.draw.circle(self.screen, (90,150,200), (sx+10*f+lean, sy-2-bob+abs(reach)), 2)
        else:
            pygame.draw.rect(self.screen, darken(robe, 15), (sx-13+lean, sy-22-bob+swing, 6, 8), border_radius=1)
            pygame.draw.rect(self.screen, lighten(robe, 15), (sx+7+lean, sy-22-bob-swing, 6, 8), border_radius=1)
        hx, hy = sx+lean, sy-38-bob
        pygame.draw.circle(self.screen, darken((250,214,180), 20), (hx, hy), 9)
        pygame.draw.circle(self.screen, (250,214,180), (hx-1, hy-1), 8)
        pygame.draw.circle(self.screen, lighten((250,214,180), 16), (hx-3, hy-3), 3)
        if n["headgear"] == "hat":
            pygame.draw.polygon(self.screen, (40,30,20), [(hx-9, sy-40-bob), (hx+9, sy-40-bob), (hx, sy-52-bob)])
            pygame.draw.line(self.screen, lighten((40,30,20), 40), (hx-1, sy-51-bob), (hx-6, sy-41-bob), 1)
        elif n["headgear"] == "hood":
            pygame.draw.arc(self.screen, (70,55,35), (hx-9, sy-46-bob, 18, 16), 0, 3.14, 4)
        else:
            pygame.draw.rect(self.screen, (200,70,60), (hx-8, sy-46-bob, 16, 5), border_radius=2)
        if st == "WORKING":
            lab = self.small.render(n["work_name"] + "...", True, (230,225,200))
            bg = pygame.Surface((lab.get_width()+10, 18), pygame.SRCALPHA); bg.fill((20,24,20,180))
            self.screen.blit(bg, (sx-lab.get_width()//2-5, sy-66))
            self.screen.blit(lab, (sx-lab.get_width()//2, sy-64))
        if math.hypot(self.px-n["x"], self.py-n["y"]) < 90:
            nm = self.small.render(n["name"], True, C_TEXT)
            self.screen.blit(nm, (sx-nm.get_width()//2, sy-78))

    def draw_dialog(self):
        line = self.dialog_lines[self.dialog_idx]
        font = self.small; pad = 14
        words = line.split(); lines = []; cur = ""
        for w in words:
            if len(cur) + len(w) + 1 > 52: lines.append(cur); cur = w
            else: cur = (cur + " " + w).strip()
        if cur: lines.append(cur)
        bw = max(font.size(l)[0] for l in lines) + pad*2
        bh = len(lines)*22 + pad*2 + 22
        bx, by = W//2 - bw//2, H - bh - 24
        box = pygame.Surface((bw, bh), pygame.SRCALPHA); box.fill((18, 22, 28, 235))
        self.screen.blit(box, (bx, by))
        pygame.draw.rect(self.screen, C_GOLD, (bx, by, bw, bh), 3, border_radius=10)
        n = self.dialog
        sk = SKINS.get(self.skin, SKINS["classic"])
        pygame.draw.circle(self.screen, sk["robe"], (bx+22, by+24), 12)
        pygame.draw.circle(self.screen, (250,214,180), (bx+22, by+18), 6)
        self.screen.blit(font.render(n["name"], True, C_GOLD), (bx+40, by+10))
        for i, l in enumerate(lines):
            self.screen.blit(font.render(l, True, C_TEXT), (bx+pad, by+34+i*22))
        hint = font.render("[E] continue   (%d/%d)" % (self.dialog_idx+1, len(self.dialog_lines)), True, (170,175,165))
        self.screen.blit(hint, (bx+bw-pad-hint.get_width(), by+bh-20))

    def draw_chest(self, sx, sy, chest, now):
        dist = math.hypot(self.px - chest["x"], self.py - chest["y"])
        near = dist < 80
        if near and not chest["opened"]:
            glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pulse = int(abs(math.sin(now * 0.005)) * 20)
            pygame.draw.circle(glow_surf, (255, 215, 0, 60), (40, 40), 35 + pulse)
            pygame.draw.circle(glow_surf, (255, 215, 0, 100), (40, 40), 25 + pulse//2)
            self.screen.blit(glow_surf, (sx - 40, sy - 40))
        if chest["opened"]:
            pygame.draw.rect(self.screen, (80, 60, 40), (sx - 14, sy - 8, 28, 16), border_radius=3)
            pygame.draw.rect(self.screen, (100, 75, 50), (sx - 12, sy - 6, 24, 12), border_radius=2)
            pygame.draw.polygon(self.screen, (90, 70, 45), [(sx-14, sy-8), (sx+14, sy-8), (sx+10, sy-18), (sx-10, sy-18)])
        else:
            rarity_col = RARITY[chest["rarity"]][1]
            pygame.draw.rect(self.screen, (110, 78, 40), (sx - 14, sy - 10, 28, 20), border_radius=3)
            pygame.draw.rect(self.screen, (130, 92, 48), (sx - 12, sy - 8, 24, 16), border_radius=2)
            pygame.draw.rect(self.screen, (100, 70, 38), (sx - 14, sy - 14, 28, 8), border_radius=3)
            pygame.draw.rect(self.screen, rarity_col, (sx - 14, sy - 14, 28, 4), border_radius=2)
            pygame.draw.rect(self.screen, C_GOLD, (sx - 3, sy - 6, 6, 6), border_radius=1)
            pygame.draw.circle(self.screen, (60, 40, 20), (sx, sy - 3), 2)
            pygame.draw.line(self.screen, (60, 40, 20), (sx - 14, sy - 4), (sx + 14, sy - 4), 2)
            pygame.draw.line(self.screen, (60, 40, 20), (sx - 14, sy + 4), (sx + 14, sy + 4), 2)
            if near:
                prompt = self.small.render("[E] Open Chest", True, C_GOLD)
                pw = prompt.get_width()
                pygame.draw.rect(self.screen, (0, 0, 0, 180), (sx - pw//2 - 6, sy - 35, pw + 12, 18), border_radius=4)
                self.screen.blit(prompt, (sx - pw//2, sy - 33))


    def draw_bridges(self, now, ox, oy, vis=None):
        """Fantasy highland wooden bridge — planks, rope rails, posts, stone bases, lanterns."""
        if not getattr(self, "bridges", None):
            return
        for br in self.bridges:
            bx = int(br.x + ox)
            by = int(br.y + oy)
            bw, bh = int(br.width), int(br.height)
            if bx + bw < -50 or by + bh < -50 or bx > W + 50 or by > H + 50:
                continue
            cx = bx + bw // 2
            # Soft shadow under span
            sh = pygame.Surface((bw + 20, bh + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 55), (4, bh // 2, bw + 8, 14))
            self.screen.blit(sh, (bx - 10, by + 4))

            # --- Stone bases at both ends ---
            for end_y in (by - 4, by + bh - 10):
                # grey stone blocks
                pygame.draw.rect(self.screen, (105, 110, 118), (bx - 10, end_y, bw + 20, 16), border_radius=3)
                pygame.draw.rect(self.screen, (140, 145, 152), (bx - 8, end_y + 2, bw + 16, 6), border_radius=2)
                # crack lines
                pygame.draw.line(self.screen, (80, 84, 90), (bx + 4, end_y + 4), (bx + bw // 3, end_y + 10), 1)
                pygame.draw.line(self.screen, (80, 84, 90), (bx + bw - 6, end_y + 3), (bx + 2 * bw // 3, end_y + 11), 1)

            # --- Deck with slight vertical curve (sag) ---
            plank_h = 7
            n_planks = max(6, bh // plank_h)
            for i in range(n_planks):
                t = i / max(1, n_planks - 1)
                # gentle middle sag for fantasy look
                sag = int(4 * math.sin(t * math.pi))
                py = by + int(t * (bh - plank_h)) + sag
                # alternate plank tones
                if i % 2 == 0:
                    base = (148, 108, 62)
                    edge = (100, 72, 38)
                    hi = (185, 145, 88)
                else:
                    base = (130, 95, 52)
                    edge = (88, 62, 32)
                    hi = (170, 130, 75)
                # plank width inset slightly near ends for perspective feel
                inset = 2 if (i < 2 or i > n_planks - 3) else 0
                px0, px1 = bx + 4 + inset, bx + bw - 4 - inset
                pygame.draw.rect(self.screen, base, (px0, py, px1 - px0, plank_h - 1), border_radius=1)
                pygame.draw.line(self.screen, edge, (px0, py + plank_h - 1), (px1, py + plank_h - 1), 1)
                pygame.draw.line(self.screen, hi, (px0 + 1, py + 1), (px1 - 1, py + 1), 1)
                # wood grain tick
                if i % 3 == 0:
                    gx = px0 + 6 + (i * 5) % max(1, px1 - px0 - 12)
                    pygame.draw.line(self.screen, edge, (gx, py + 2), (gx, py + plank_h - 3), 1)

            # --- Corner wooden pillars (thick posts) ---
            post_w, post_h = 12, 18
            posts = [
                (bx - 6, by - 8),
                (bx + bw - 6, by - 8),
                (bx - 6, by + bh - 12),
                (bx + bw - 6, by + bh - 12),
            ]
            for px, py in posts:
                # post body
                pygame.draw.rect(self.screen, (92, 64, 34), (px, py, post_w, post_h), border_radius=2)
                pygame.draw.rect(self.screen, (150, 112, 60), (px + 2, py + 2, post_w - 4, post_h - 5), border_radius=1)
                # top cap
                pygame.draw.rect(self.screen, (70, 48, 24), (px - 1, py - 3, post_w + 2, 5), border_radius=1)
                pygame.draw.rect(self.screen, (175, 135, 75), (px, py - 2, post_w, 3), border_radius=1)
                # rope wrap on post
                pygame.draw.arc(self.screen, (180, 150, 100), (px - 1, py + 4, post_w + 2, 8), 0.2, 2.9, 2)
                pygame.draw.arc(self.screen, (140, 110, 70), (px - 1, py + 8, post_w + 2, 8), 0.2, 2.9, 2)

            # --- Rope railings along both sides ---
            for side in (0, 1):
                rx = bx + 5 if side == 0 else bx + bw - 6
                # main rope (slight sag)
                pts = []
                for i in range(8):
                    t = i / 7.0
                    yy = by + 4 + int(t * (bh - 8))
                    sag = int(3 * math.sin(t * math.pi))
                    pts.append((rx + sag * (1 if side == 0 else -1) * 0, yy + sag))
                if len(pts) >= 2:
                    pygame.draw.lines(self.screen, (170, 140, 90), False, pts, 3)
                    pygame.draw.lines(self.screen, (120, 95, 55), False, pts, 1)
                # vertical rope ties to planks
                for i in range(1, 7):
                    t = i / 7.0
                    yy = by + 4 + int(t * (bh - 8))
                    pygame.draw.line(self.screen, (150, 120, 75), (rx, yy), (rx + (4 if side == 0 else -4), yy + 3), 1)

            # --- Decorative lanterns on near posts ---
            lanterns = [(bx - 2, by - 4), (bx + bw - 2, by + bh - 6)]
            pulse = 0.6 + 0.4 * abs(math.sin(now * 0.005))
            for lx, ly in lanterns:
                # bracket
                pygame.draw.line(self.screen, (90, 70, 40), (lx, ly), (lx + 3, ly - 8), 2)
                # lantern body
                pygame.draw.rect(self.screen, (60, 50, 35), (lx, ly - 14, 8, 10), border_radius=1)
                glow = pygame.Surface((16, 16), pygame.SRCALPHA)
                ga = int(50 * pulse)
                pygame.draw.circle(glow, (255, 200, 80, ga), (8, 8), 7)
                pygame.draw.circle(glow, (255, 230, 140, int(90 * pulse)), (8, 8), 3)
                self.screen.blit(glow, (lx - 4, ly - 16))
                pygame.draw.rect(self.screen, (255, 210, 100), (lx + 2, ly - 12, 4, 5), border_radius=1)

            # Outer outline for clarity
            pygame.draw.rect(self.screen, (55, 40, 22), (bx + 2, by + 2, bw - 4, bh - 4), 1)


    def draw_world(self, now):
        b = BIOMES[self.biome]
        ld, ll = b["leaf"]
        ox, oy = int(W/2 - self.camx), int(H/2 - self.camy)
        # Distant mountain skyline for mountain biomes – drawn first as background
        if b.get("mountains"):
            # fill a sky band so peaks read as far-off Himalayas
            sky_col = b.get("sky", (170, 195, 220))
            pygame.draw.rect(self.screen, sky_col, (0, 0, W, 220))
            par_x = int(ox * 0.12)
            peaks = [
                # (base_x, height, width, color) – heights grow downward from top
                (-100 + par_x, 150, 260, (100, 120, 140)),
                (120 + par_x, 200, 300, (85, 105, 125)),
                (360 + par_x, 170, 250, (95, 115, 135)),
                (580 + par_x, 230, 320, (78, 98, 118)),
                (860 + par_x, 160, 270, (90, 110, 130)),
                (1080 + par_x, 190, 280, (82, 102, 122)),
            ]
            for bx, ph, pw, mcol in peaks:
                tip_x = bx + pw // 2
                tip_y = 10 + ph
                pts = [
                    (bx, 0),
                    (bx + pw // 4, tip_y - 40),
                    (tip_x - 20, tip_y - 10),
                    (tip_x, tip_y),
                    (tip_x + 25, tip_y - 15),
                    (bx + 3 * pw // 4, tip_y - 50),
                    (bx + pw, 0),
                ]
                if bx + pw > -20 and bx < W + 20:
                    pygame.draw.polygon(self.screen, mcol, pts)
                    # snow cap
                    snow = [
                        (tip_x - 22, tip_y - 12),
                        (tip_x, tip_y),
                        (tip_x + 20, tip_y - 14),
                        (tip_x + 6, tip_y - 36),
                        (tip_x - 12, tip_y - 30),
                    ]
                    pygame.draw.polygon(self.screen, (240, 245, 250), snow)
                    # ridge highlight
                    pygame.draw.line(self.screen, lighten(mcol, 30), (tip_x - 10, tip_y - 18), (tip_x, tip_y), 2)
        self.screen.blit(self.terrain, (ox, oy))
        vis = pygame.Rect(self.camx - W/2 - 60, self.camy - H/2 - 60, W + 120, H + 120)
        wind_amp = 2.0 if self.weather == "wind" else 1.0
        for gx0, gy0, gs, gph in self.grass_tufts:
            if not vis.collidepoint(gx0, gy0): continue
            sw = math.sin(now*0.002 + gph) * 2 * wind_amp
            sx, sy = gx0+ox, gy0+oy
            for k in (-1, 0, 1):
                pygame.draw.line(self.screen, darken(b["grass"], 20), (int(sx+k*3), int(sy)), (int(sx+k*3+sw), int(sy-6*gs)), 1)
        for br in self.brambles:
            if not vis.collidepoint(br["x"], br["y"]): continue
            sx, sy = int(br["x"]+ox), int(br["y"]+oy)
            soft_shadow(self.screen, sx, sy+2, 14, 6, 80)
            bc = (44, 66, 40) if self.biome != 5 else (150, 170, 200)
            pygame.draw.circle(self.screen, bc, (sx, sy-6), 12)
            pygame.draw.circle(self.screen, lighten(bc, 14), (sx-6, sy-10), 7)
            pygame.draw.circle(self.screen, lighten(bc, 14), (sx+6, sy-9), 7)
            for k in (-8, 0, 8):
                pygame.draw.line(self.screen, darken(bc, 14), (sx+k, sy-12), (int(sx+k*1.4), sy-20), 1)
        if BIOMES[self.biome].get("mountains"):
            for r in self.rockfalls:
                age = (now - r["t"])/1000.0
                sx, sy = int(r["x"]+ox), int(r["y"]+oy)
                if age <= 1.1:
                    pygame.draw.circle(self.screen, (200,60,50), (sx, sy), int(8+age*14), 2)
                    hgt = int(max(0, (1.1-age)) * 120)
                    pygame.draw.circle(self.screen, (120,120,126), (sx, sy-hgt), 8)
        ws = pygame.Surface((W, H), pygame.SRCALPHA)
        flow = (now * .05) % 46
        for i in range(0, len(self.water)-1, 3):
            wx, wy, wr = self.water[i]
            if not vis.collidepoint(wx, wy): continue
            sx, sy = wx+ox, wy+oy
            nx, ny = self.water[i+1][0]+ox, self.water[i+1][1]+oy
            pygame.draw.line(ws, b["foam"] + (34,), (int(sx-(nx-sx)*flow*.4), int(sy-(ny-sy)*flow*.4)), (int(nx), int(ny)), 1)
            if hash01(i*13 + now//500) > .93:
                pygame.draw.circle(ws, b["foam"] + (120,), (int(sx), int(sy)), 1)
        for rp in self.ripples:
            if vis.collidepoint(rp["x"], rp["y"]):
                pygame.draw.circle(ws, b["foam"] + (int(rp["a"]),), (int(rp["x"]+ox), int(rp["y"]+oy)), int(rp["r"]), 1)
        sway_amp = 2.0 if self.weather == "wind" else 1.0
        for tr in self.trees:
            tx, ty, ts = tr[0], tr[1], tr[2]
            bi, bd = self.nearest_water(tx, ty)
            if bd < 90:
                wx, wy, _ = self.water[bi]
                if vis.collidepoint(wx, wy):
                    pygame.draw.ellipse(ws, (14, 40, 26, 50), (int(wx+ox-14*ts), int(wy+oy+4), int(28*ts), int(10*ts)))
        if self.biome != 6 and len(getattr(self, "water", []) or []) >= 2:
            for f in self.fish:
                fx, fy = self.water_pos(f["t"], f["lat"] + math.sin(now*.001+f["ph"])*.15)
                if vis.collidepoint(fx, fy):
                    pygame.draw.ellipse(ws, (20,40,55,110), (int(fx+ox-9), int(fy+oy-3), 18, 7))
            for fl in self.float_leaves:
                lx, ly = self.water_pos(fl["t"], fl["lat"])
                if vis.collidepoint(lx, ly):
                    pygame.draw.ellipse(ws, (140,160,80,200), (int(lx+ox-3), int(ly+oy-2), 6, 4))
            for lx, ly, ls in self.lily:
                if vis.collidepoint(lx, ly):
                    sx, sy = int(lx+ox), int(ly+oy)
                    bob = int(math.sin(now*.0015+lx)*1.5)
                    pygame.draw.circle(ws, (46, 128, 66, 230), (sx, sy+bob), int(8*ls))
                    pygame.draw.circle(ws, (70, 150, 80, 230), (sx-2, sy-2+bob), int(5*ls))
        self.screen.blit(ws, (0, 0))
        if self.biome != 6 and len(getattr(self, "water", []) or []) >= 2:
            for d in self.ducks:
                dxp, dyp = self.water_pos(d["t"], d["lat"])
                if vis.collidepoint(dxp, dyp):
                    sx, sy = int(dxp+ox), int(dyp+oy)
                    pygame.draw.ellipse(self.screen, (225,222,210), (sx-7, sy-4, 14, 9))
                    pygame.draw.circle(self.screen, (225,222,210), (sx+6, sy-6), 4)
                    pygame.draw.circle(self.screen, (200,140,60), (sx+9, sy-6), 2)
        for rx, ry in self.reeds:
            if vis.collidepoint(rx, ry):
                sw = math.sin(now*.002 + rx)*3*wind_amp
                pygame.draw.line(self.screen, REED_C, (int(rx+ox), int(ry+oy)), (int(rx+ox+sw), int(ry+oy-16)), 2)
                # Early bridge pass (solid deck over water)
                self.draw_bridges(now, ox, oy, vis)

        for chest in self.chests:
            if vis.collidepoint(chest["x"], chest["y"]):
                self.draw_chest(int(chest["x"]+ox), int(chest["y"]+oy), chest, now)
        for r in self.runes:
            if vis.collidepoint(r["x"], r["y"]):
                sx, sy = int(r["x"]+ox), int(r["y"]+oy)
                col = (100, 100, 120) if not r["used"] else (60, 60, 70)
                pygame.draw.rect(self.screen, col, (sx-8, sy-12, 16, 24), border_radius=2)
                pygame.draw.circle(self.screen, lighten(col, 30), (sx, sy-6), 4)
                
        eq = []
        for tr in self.trees: eq.append((tr[1], "tree", tr))
        for rk in self.rocks: eq.append((rk[1], "rock", rk))
        for lg in self.logs: eq.append((lg[1], "log", lg))
        for c in self.coins: eq.append((c[1], "coin", c))
        for drop in getattr(self, "loot_drops", []) or []:
            if not drop.get("got"):
                eq.append((drop["y"], "loot", drop))
        for tr in self.trash:
            if not tr["got"]: eq.append((tr["y"], "trash", tr))
        for s in self.saplings: eq.append((s["y"], "sapling", s))
        for lm in self.landmarks: eq.append((lm["y"], "landmark", lm))
        # Bhutanese decorations – houses always present (one per NPC + Mine House)
        binfo = BIOMES[self.biome]
        for h in self.houses:
            eq.append((h["y"], "house", h))
        if binfo.get("flags"):
            for f in self.prayer_flags: eq.append((f[1], "flags", f))
        if binfo.get("chortens"):
            for c in self.chortens: eq.append((c[1], "chorten", c))
        # goal marker removed — no on-map treasure indicator
        for r in self.rabbits: eq.append((r["y"], "rabbit", r))
        for b2 in self.birds: eq.append((b2["y"], "bird", b2))
        for n in self.npcs: eq.append((n["y"], "npc", n))
        for e in self.enemies: eq.append((e["y"], "enemy", e))
        for w in self.worms: eq.append((w["y"], "worm", w))
        for bg2 in self.bugs: eq.append((bg2["y"], "bug", bg2))
        for d in self.extra: eq.append((d["y"], "extra", d))
        eq.append((self.py, "player", None))
        eq.sort(key=lambda e: e[0])
        blink = now < self.inv and (now // 100) % 2 == 0
        tc = (40,35,35) if "Bamboo" in binfo["name"] or "Misty" in binfo["name"] else (96,72,48)
        for _, kind, d in eq:
            if kind == "tree":
                tx, ty, ts, k = d[0], d[1], d[2], d[3]
                shape = d[4] if len(d) > 4 else 0.5
                if not vis.collidepoint(tx, ty): continue
                sx, sy = tx + ox, ty + oy
                sway = math.sin(now * 0.0011 + tx * 0.025) * (1.8 * ts) * sway_amp
                # ground shadow
                soft_shadow(self.screen, sx, sy + 3, int(12 * ts + 4), int(5 * ts + 2), 80)
                # --- trunk ---
                tw = max(3, int(4.5 * ts + 1))
                th = int((16 + shape * 6) * ts)
                trunk_col = tc
                if k == "birch":
                    trunk_col = (235, 232, 222) if self.biome != 6 else tc
                elif k == "cedar":
                    trunk_col = darken(tc, 18)
                # tapered trunk look
                pygame.draw.rect(self.screen, darken(trunk_col, 30), (int(sx - tw // 2 - 1), int(sy - th), tw + 2, th))
                pygame.draw.rect(self.screen, trunk_col, (int(sx - tw // 2), int(sy - th), tw, th))
                pygame.draw.rect(self.screen, lighten(trunk_col, 25), (int(sx - tw // 2), int(sy - th), max(1, tw // 3), th))
                if k == "birch" and self.biome != 6:
                    for bi in range(3):
                        byy = int(sy - th + 4 + bi * (th / 3.5))
                        pygame.draw.line(self.screen, (70, 70, 75), (int(sx - tw // 2 + 1), byy), (int(sx + tw // 2 - 1), byy), 1)
                else:
                    for bi in range(2):
                        byy = int(sy - th + 5 + bi * (th / 2.5))
                        pygame.draw.line(self.screen, darken(trunk_col, 40), (int(sx - tw // 2), byy), (int(sx + tw // 2), byy), 1)

                if k in ("pine", "tall_pine", "cedar"):
                    # Classic layered pine – overlapping triangles with depth
                    layers = 6 if k == "tall_pine" else 5
                    base_h = (62 if k == "tall_pine" else 52) * ts
                    for i in range(layers):
                        t = i / max(1, layers - 1)
                        # each layer sits lower and wider
                        top_y = sy - base_h + i * (7.5 + shape * 2) * ts
                        half_w = (8 + i * 4.2 + shape * 3) * ts
                        # dark back layer slightly offset
                        col_back = darken(ld, 20)
                        col_mid = ld if i % 2 == 0 else darken(ll, 5)
                        col_hi = lighten(ll, 10)
                        if k == "cedar":
                            col_back = darken(col_back, 8)
                            col_mid = darken(col_mid, 8)
                        # back silhouette
                        pygame.draw.polygon(self.screen, col_back, [
                            (int(sx + sway * 0.3), int(top_y - 10 * ts)),
                            (int(sx - half_w - 2), int(top_y + 14 * ts)),
                            (int(sx + half_w + 2), int(top_y + 14 * ts)),
                        ])
                        # main body
                        pygame.draw.polygon(self.screen, col_mid, [
                            (int(sx + sway * 0.5), int(top_y - 12 * ts)),
                            (int(sx - half_w), int(top_y + 13 * ts)),
                            (int(sx + half_w), int(top_y + 13 * ts)),
                        ])
                        # left highlight edge
                        pygame.draw.polygon(self.screen, col_hi, [
                            (int(sx + sway * 0.5), int(top_y - 12 * ts)),
                            (int(sx - half_w * 0.15), int(top_y - 2 * ts)),
                            (int(sx - half_w * 0.55), int(top_y + 10 * ts)),
                        ])
                    # sharp tip
                    tip_y = sy - base_h - 8 * ts
                    pygame.draw.polygon(self.screen, lighten(ll, 18), [
                        (int(sx + sway * 0.4), int(tip_y)),
                        (int(sx - 6 * ts), int(tip_y + 14 * ts)),
                        (int(sx + 6 * ts), int(tip_y + 14 * ts)),
                    ])
                else:
                    # Deciduous: clustered canopy (oak / birch / round / bushy)
                    r = int((18 + shape * 5) * ts)
                    if k == "birch":
                        r = int((15 + shape * 4) * ts)
                    elif k == "bushy":
                        r = int((17 + shape * 5) * ts)
                    cy = sy - 22 * ts
                    # dark under-canopy
                    pygame.draw.circle(self.screen, darken(ld, 18), (int(sx + sway * 0.2), int(cy + 4 * ts)), int(r * 0.95))
                    # main lobes – organic cluster, not one blob
                    lobes = [
                        (sx + sway * 0.3, cy - 2 * ts, r),
                        (sx + sway - 9 * ts, cy - 4 * ts, int(r * 0.72)),
                        (sx + sway + 9 * ts, cy - 2 * ts, int(r * 0.68)),
                        (sx + sway * 0.2, cy - 12 * ts, int(r * 0.55)),
                        (sx + sway + 3 * ts, cy + 6 * ts, int(r * 0.4)),
                        (sx + sway - 5 * ts, cy + 5 * ts, int(r * 0.38)),
                    ]
                    for i, (lx, ly, lr) in enumerate(lobes):
                        col = ld if i % 2 == 0 else ll
                        pygame.draw.circle(self.screen, col, (int(lx), int(ly)), lr)
                    # bright top highlights
                    pygame.draw.circle(self.screen, lighten(ll, 22), (int(sx + sway - 5 * ts), int(cy - 10 * ts)), int(r * 0.32))
                    pygame.draw.circle(self.screen, lighten(ll, 12), (int(sx + sway + 4 * ts), int(cy - 6 * ts)), int(r * 0.22))

            elif kind == "rock":
                rx, ry, rr = d[0], d[1], d[2]
                if not vis.collidepoint(rx, ry): continue
                sx, sy = rx+ox, ry+oy
                rc = (128,130,136) if self.biome != 6 else (60,55,58)
                soft_shadow(self.screen, sx, sy + rr * 0.2, int(rr * 1.1), int(rr * 0.45), 85)
                pygame.draw.ellipse(self.screen, darken(rc, 18), (int(sx-rr), int(sy-rr*.65), int(rr*2), int(rr*1.35)))
                pygame.draw.ellipse(self.screen, rc, (int(sx-rr*0.92), int(sy-rr*.72), int(rr*1.85), int(rr*1.25)))
                pygame.draw.ellipse(self.screen, lighten(rc, 28), (int(sx-rr*.55), int(sy-rr*.95), int(rr*1.05), int(rr*.6)))
                # small moss patch
                if rr > 10:
                    pygame.draw.ellipse(self.screen, (55, 110, 60), (int(sx - rr * 0.2), int(sy - rr * 0.3), int(rr * 0.45), int(rr * 0.25)))
            elif kind == "log":
                lx, ly, la = d
                sx, sy = lx+ox, ly+oy
                pygame.draw.line(self.screen, tc, (int(sx-math.cos(la)*22), int(sy-math.sin(la)*10)), (int(sx+math.cos(la)*22), int(sy+math.sin(la)*10)), 10)
            elif kind == "house":
                # Traditional house – style shifts slightly by level theme
                hx, hy, hs = d["x"], d["y"], d["s"]
                if not vis.collidepoint(hx, hy): continue
                sx, sy = int(hx+ox), int(hy+oy)
                theme = d.get("theme", "village")
                wall = {
                    "forest": (225, 220, 200),
                    "village": (235, 228, 210),
                    "mountain": (210, 215, 220),
                    "desert": (210, 190, 155),
                    "temple": (240, 235, 220),
                }.get(theme, (235, 228, 210))
                roof = {
                    "forest": (90, 55, 35),
                    "village": (140, 45, 35),
                    "mountain": (100, 70, 55),
                    "desert": (150, 110, 60),
                    "temple": (130, 40, 35),
                }.get(theme, (140, 45, 35))
                if d.get("is_player"):
                    roof = lighten(roof, 20)
                soft_shadow(self.screen, sx, sy+4, int(28*hs), int(12*hs), 120)
                pygame.draw.rect(self.screen, wall, (sx-int(22*hs), sy-int(34*hs), int(44*hs), int(34*hs)))
                pygame.draw.rect(self.screen, (90, 55, 30), (sx-int(22*hs), sy-int(14*hs), int(44*hs), int(6*hs)))
                pygame.draw.rect(self.screen, (40, 70, 90), (sx-int(14*hs), sy-int(27*hs), int(9*hs), int(9*hs)))
                pygame.draw.rect(self.screen, (40, 70, 90), (sx+int(5*hs), sy-int(27*hs), int(9*hs), int(9*hs)))
                pygame.draw.rect(self.screen, (160, 50, 40), (sx-int(14*hs), sy-int(27*hs), int(9*hs), int(9*hs)), 2)
                pygame.draw.rect(self.screen, (160, 50, 40), (sx+int(5*hs), sy-int(27*hs), int(9*hs), int(9*hs)), 2)
                door_col = (110, 70, 40) if not d.get("is_player") else (140, 90, 50)
                pygame.draw.rect(self.screen, door_col, (sx-int(5*hs), sy-int(12*hs), int(10*hs), int(12*hs)))
                pygame.draw.rect(self.screen, (180, 140, 60), (sx-int(5*hs), sy-int(12*hs), int(10*hs), int(12*hs)), 1)
                pygame.draw.polygon(self.screen, roof, [
                    (sx-int(28*hs), sy-int(34*hs)),
                    (sx+int(28*hs), sy-int(34*hs)),
                    (sx+int(18*hs), sy-int(52*hs)),
                    (sx-int(18*hs), sy-int(52*hs))
                ])
                pygame.draw.line(self.screen, (180, 140, 50), (sx-int(16*hs), sy-int(50*hs)), (sx+int(16*hs), sy-int(50*hs)), 3)
                if d.get("is_player"):
                    label = self.small.render("Mine House", True, C_GOLD)
                    self.screen.blit(label, (sx - label.get_width()//2, sy + 6))
            elif kind == "flags":
                # Prayer flag pole with colored flags
                fx, fy, fs, nflags = d
                if not vis.collidepoint(fx, fy): continue
                sx, sy = int(fx+ox), int(fy+oy)
                soft_shadow(self.screen, sx, sy+2, 6, 4, 70)
                # pole
                pygame.draw.line(self.screen, (120, 90, 50), (sx, sy), (sx, sy-int(48*fs)), 3)
                # colored flags (blue, white, red, green, yellow)
                flag_cols = [(40, 90, 180), (240, 240, 235), (190, 40, 40), (40, 140, 60), (220, 180, 40)]
                for i in range(nflags):
                    col = flag_cols[i % 5]
                    fy2 = sy - int(12*fs) - i * int(7*fs)
                    wave = int(math.sin(now*0.008 + i*0.9)*3)
                    pygame.draw.polygon(self.screen, col, [
                        (sx+2, fy2),
                        (sx+int(16*fs)+wave, fy2-2),
                        (sx+int(16*fs)+wave, fy2+5),
                        (sx+2, fy2+4)
                    ])
            elif kind == "chorten":
                # Simple chorten / stupa
                cx, cy, cs = d
                if not vis.collidepoint(cx, cy): continue
                sx, sy = int(cx+ox), int(cy+oy)
                soft_shadow(self.screen, sx, sy+2, int(14*cs), int(7*cs), 90)
                # base
                pygame.draw.rect(self.screen, (210, 200, 180), (sx-int(14*cs), sy-int(10*cs), int(28*cs), int(12*cs)))
                # stepped levels
                pygame.draw.rect(self.screen, (200, 190, 170), (sx-int(11*cs), sy-int(18*cs), int(22*cs), int(9*cs)))
                pygame.draw.rect(self.screen, (190, 180, 160), (sx-int(8*cs), sy-int(25*cs), int(16*cs), int(8*cs)))
                # dome
                pygame.draw.ellipse(self.screen, (230, 220, 200), (sx-int(7*cs), sy-int(36*cs), int(14*cs), int(14*cs)))
                # spire
                pygame.draw.line(self.screen, (180, 150, 60), (sx, sy-int(36*cs)), (sx, sy-int(48*cs)), 2)
                pygame.draw.circle(self.screen, (200, 160, 50), (sx, sy-int(48*cs)), 3)
            elif kind == "loot":
                if not vis.collidepoint(d["x"], d["y"]): continue
                sx, sy = int(d["x"] + ox), int(d["y"] + oy)
                col = RESOURCE_TYPES.get(d["kind"], {}).get("color", (200, 200, 200))
                pulse = 1.0 + 0.12 * math.sin(now * 0.006 + d["x"])
                soft_shadow(self.screen, sx, sy + 2, 10, 5, 70)
                if d["kind"] == "gem":
                    pts = [(sx, sy - int(8 * pulse)), (sx + 6, sy), (sx, sy + 6), (sx - 6, sy)]
                    pygame.draw.polygon(self.screen, col, pts)
                    pygame.draw.polygon(self.screen, lighten(col, 40), [(sx, sy - int(5 * pulse)), (sx + 3, sy), (sx, sy + 2)])
                elif d["kind"] == "scroll":
                    pygame.draw.rect(self.screen, col, (sx - 6, sy - 8, 12, 14), border_radius=2)
                    pygame.draw.line(self.screen, darken(col, 40), (sx - 4, sy - 4), (sx + 4, sy - 4), 1)
                    pygame.draw.line(self.screen, darken(col, 40), (sx - 4, sy), (sx + 4, sy), 1)
                elif d["kind"] == "relic":
                    pygame.draw.circle(self.screen, col, (sx, sy - 2), 7)
                    pygame.draw.circle(self.screen, lighten(col, 30), (sx - 2, sy - 4), 3)
                    pygame.draw.rect(self.screen, darken(col, 20), (sx - 5, sy + 4, 10, 3))
                elif d["kind"] == "nature":
                    pygame.draw.circle(self.screen, col, (sx, sy - 4), 6)
                    pygame.draw.circle(self.screen, lighten(col, 25), (sx - 4, sy), 4)
                    pygame.draw.circle(self.screen, lighten(col, 15), (sx + 4, sy), 4)
                else:  # artifact
                    pygame.draw.polygon(self.screen, col, [(sx, sy - 9), (sx + 7, sy - 2), (sx + 4, sy + 6), (sx - 4, sy + 6), (sx - 7, sy - 2)])
                    pygame.draw.circle(self.screen, (255, 230, 120), (sx, sy - 1), 3)
            elif kind == "coin":
                if not vis.collidepoint(d[0], d[1]): continue
                sx, sy = d[0]+ox, d[1]+oy
                sp = abs(math.sin(now*.006 + d[0]))
                pygame.draw.ellipse(self.screen, C_GOLD, (int(sx-6*sp), int(sy-7), max(2, int(12*sp)), 14))
            elif kind == "trash":
                sx, sy = d["x"]+ox, d["y"]+oy
                pygame.draw.ellipse(self.screen, (90,88,80), (int(sx-9), int(sy-5), 18, 10))
                pygame.draw.rect(self.screen, (160,165,170), (int(sx-3), int(sy-10), 6, 8))
            elif kind == "sapling":
                sx, sy = d["x"]+ox, d["y"]+oy
                if d["planted"]:
                    pygame.draw.line(self.screen, (70,150,70), (sx, sy), (sx, sy-12), 2)
                    pygame.draw.circle(self.screen, (110,200,100), (sx-4, sy-10), 4)
                    pygame.draw.circle(self.screen, (110,200,100), (sx+4, sy-12), 4)
                else:
                    pygame.draw.ellipse(self.screen, (110,90,60), (sx-8, sy-4, 16, 8))
            elif kind == "landmark":
                sx, sy = int(d["x"]+ox), int(d["y"]+oy)
                if d["kind"] == "spring":
                    pygame.draw.ellipse(self.screen, (120,190,200), (sx-16, sy-8, 32, 16))
                    pygame.draw.ellipse(self.screen, (180,230,240), (sx-10, sy-5, 20, 10))
                    for i in range(3):
                        off = (now*0.05 + i*10) % 24
                        pygame.draw.circle(self.screen, (230,245,250), (sx-6+i*6, sy-10-int(off)), 2)
                else:
                    pygame.draw.rect(self.screen, (150,150,158), (sx-8, sy-34, 16, 34))
                    pygame.draw.circle(self.screen, (170,170,178), (sx, sy-40), 8)
            elif kind == "goal":
                pass
            elif kind == "rabbit":
                if not vis.collidepoint(d["x"], d["y"]): continue
                sx, sy = d["x"]+ox, d["y"]+oy
                soft_shadow(self.screen, sx, sy - 2, 10, 5, 90)
                hop = 3 if d["hop"] > 0 else 0
                pygame.draw.ellipse(self.screen, (205,200,192), (int(sx-6), int(sy-6-hop), 12, 8))
                pygame.draw.circle(self.screen, (205,200,192), (int(sx+6), int(sy-8-hop)), 4)
            elif kind == "bird":
                sx, sy = int(d["x"]+ox), int(d["y"]+oy)
                wing = math.sin(d.get("wing", 0)*2) * 4
                if d["st"] == "fly":
                    pygame.draw.ellipse(self.screen, (140,116,86), (sx-5, sy-4, 10, 7))
                    pygame.draw.line(self.screen, (120,100,80), (sx-2, sy-2), (sx-8, sy-6-int(wing)), 2)
                    pygame.draw.line(self.screen, (120,100,80), (sx+2, sy-2), (sx+8, sy-6-int(wing)), 2)
                    pygame.draw.circle(self.screen, (140,116,86), (sx+5, sy-6), 3)
                else:
                    soft_shadow(self.screen, sx, sy, 6, 3, 70)
                    pygame.draw.ellipse(self.screen, (140,116,86), (sx-5, sy-6, 10, 7))
                    pygame.draw.circle(self.screen, (140,116,86), (sx+4, sy-8), 3)
                    pygame.draw.circle(self.screen, (240,180,60), (sx+7, sy-8), 1)
            elif kind == "worm":
                if not vis.collidepoint(d["x"], d["y"]): continue
                if d.get("bur", 0) > 0:
                    sx, sy = int(d["x"]+ox), int(d["y"]+oy)
                    pygame.draw.ellipse(self.screen, (120, 78, 66), (sx-4, sy-2, 8, 4))
                    continue
                for i, (wx2, wy2) in enumerate(d["seg"]):
                    px2, py2 = int(wx2+ox), int(wy2+oy)
                    rad = max(1, 4 - i * 0.25)
                    pygame.draw.circle(self.screen, darken((150, 95, 80), i * 4), (px2, py2), int(rad))
                if d["seg"]:
                    hx2, hy2 = int(d["seg"][0][0]+ox), int(d["seg"][0][1]+oy)
                    pygame.draw.circle(self.screen, lighten((150,95,80), 25), (hx2, hy2), 3)
            elif kind == "bug":
                if not vis.collidepoint(d["x"], d["y"]): continue
                sx, sy = int(d["x"]+ox), int(d["y"]+oy)
                a = d["a"]; leg_phase = math.sin(d["ph"] * 8)
                pygame.draw.ellipse(self.screen, (40, 30, 22), (sx-4, sy-3, 8, 6))
                for side in (-1, 1):
                    for k in (-1, 0, 1):
                        lp = leg_phase * side * (1 if k == 0 else -1)
                        lx = sx + math.cos(a + math.pi/2 * side) * (4 + k) + math.cos(a) * k * 2
                        ly = sy + math.sin(a + math.pi/2 * side) * (4 + k) + math.sin(a) * k * 2 + lp
                        pygame.draw.line(self.screen, (30, 22, 16), (sx, sy), (int(lx), int(ly)), 1)
            elif kind == "extra":
                sx, sy = int(d["x"]+ox), int(d["y"]+oy)
                if d["kind"] == "frog":
                    hop = 2 if d["hop"] > 0 else 0
                    pygame.draw.ellipse(self.screen, (90, 160, 80), (sx-6, sy-5-hop, 12, 8))
                    pygame.draw.circle(self.screen, (120, 190, 110), (sx-3, sy-9-hop), 2)
                    pygame.draw.circle(self.screen, (120, 190, 110), (sx+3, sy-9-hop), 2)
                elif d["kind"] in ("goat", "yak"):
                    soft_shadow(self.screen, sx, sy, 12, 5, 80)
                    body = (235,232,225) if d["kind"]=="goat" else (90,70,50)
                    pygame.draw.ellipse(self.screen, body, (sx-9, sy-8, 18, 10))
                    pygame.draw.circle(self.screen, lighten(body,10), (sx+8, sy-12), 5)
                    pygame.draw.line(self.screen, (120,110,90), (sx+10, sy-16), (sx+13, sy-20), 2)
                elif d["kind"] == "bat":
                    wg = int(math.sin(now*.03 + d["p"])*4)
                    pygame.draw.ellipse(self.screen, (40, 35, 50), (sx-3, sy-3, 6, 5))
                    pygame.draw.line(self.screen, (40, 35, 50), (sx-3, sy), (sx-9, sy-wg), 2)
                    pygame.draw.line(self.screen, (40, 35, 50), (sx+3, sy), (sx+9, sy-wg), 2)
                else:
                    soft_shadow(self.screen, sx, sy, 10, 4, 80)
                    pygame.draw.ellipse(self.screen, (230, 140, 80), (sx-8, sy-6, 16, 9))
                    pygame.draw.circle(self.screen, (240, 235, 225), (sx+7, sy-8), 4)
                    pygame.draw.line(self.screen, (230, 140, 80), (sx-8, sy-2), (sx-14, sy+2), 3)
            elif kind == "npc":
                self.draw_npc(d, now)
            elif kind == "enemy":
                if not vis.collidepoint(d["x"], d["y"]): continue
                sx, sy = int(d["x"]+ox), int(d["y"]+oy)
                soft_shadow(self.screen, sx, sy - 2, 12, 6, 100)
                lung = d.get("lunge", 0) > 0
                if d["type"] == "SNAKE":
                    scol = {0:(80,140,70),1:(70,130,90),2:(110,110,125),3:(120,100,140),4:(120,110,90),5:(215,220,235),6:(220,110,50),7:(90,120,80),8:(140,150,70),9:(70,130,75)}.get(self.biome, (80,140,70))
                    for i, (wx2, wy2) in enumerate(d.get("seg", [])):
                        px2, py2 = int(wx2+ox), int(wy2+oy)
                        rad = max(2, 5 - i * 0.3)
                        pygame.draw.circle(self.screen, darken(scol, i * 4), (px2, py2), int(rad))
                    hr = 6 if lung else 5
                    pygame.draw.circle(self.screen, lighten(scol, 20), (sx, sy-1), hr)
                    pygame.draw.circle(self.screen, (20, 20, 20), (sx-2, sy-2), 1)
                    if lung or (now // 900) % 3 == 0:
                        pygame.draw.line(self.screen, (220, 60, 60), (sx-5, sy-1), (sx-10, sy-3), 1)
                        pygame.draw.line(self.screen, (220, 60, 60), (sx-5, sy-1), (sx-10, sy+1), 1)
                else:
                    leg = math.sin(d.get("leg", now*.01)) * 3
                    claw = 4 if lung else 2
                    pygame.draw.ellipse(self.screen, (190,60,50), (sx-10, sy-6, 20, 12))
                    pygame.draw.ellipse(self.screen, lighten((190,60,50), 30), (sx-8, sy-5, 10, 5))
                    for side in (-1, 1):
                        pygame.draw.line(self.screen, (190,60,50), (sx+side*9, sy-2), (sx+side*16, sy-8+leg*side), 2)
                        pygame.draw.line(self.screen, (190,60,50), (sx+side*8, sy+2), (sx+side*15, sy+6-leg*side), 2)
                        pygame.draw.circle(self.screen, (220,90,70), (sx+side*16, sy-8+leg*side), claw)
                    pygame.draw.circle(self.screen, (230,230,225), (sx-4, sy-2), 2)
                    pygame.draw.circle(self.screen, (230,230,225), (sx+4, sy-2), 2)
            elif kind == "player" and not blink:
                sx, sy = int(self.px+ox), int(self.py+oy)
                skin_data = SKINS.get(self.skin, SKINS["classic"])
                draw_anime_player(self.screen, sx, sy, self.direction, int(self.walk), self.moving, skin_data, self.gender if hasattr(self, "gender") else "male")
        for bf in self.butterflies:
            if vis.collidepoint(bf["x"], bf["y"]):
                fl = math.sin(now * .025 + bf["p"]) * 4
                sz = bf.get("sz", 1.0)
                w, h = max(3, int(5 * sz)), max(3, int(6 * sz))
                sx, sy = int(bf["x"] + ox), int(bf["y"] + oy - fl / 2)
                # wings
                pygame.draw.ellipse(self.screen, bf["c"], (sx - w - 1, sy - h // 2, w, h))
                pygame.draw.ellipse(self.screen, bf["c"], (sx + 1, sy - h // 2, w, h))
                # body
                pygame.draw.line(self.screen, darken(bf["c"], 40), (sx, sy - 2), (sx, sy + 2), 1)
        for p in self.parts:
            pygame.draw.circle(self.screen, p["c"], (int(p["x"]+ox), int(p["y"]+oy)), 2)
        for i in range(3):
            mx = ((now*.012*(i+1)) % (WW+600)) - 300
            my = 300 + i*420
            sx, sy = mx+ox, my+oy
            if -400 < sx < W+400:
                m = pygame.Surface((420, 140), pygame.SRCALPHA)
                pygame.draw.ellipse(m, (220,240,220,16), (0, 0, 420, 140))
                self.screen.blit(m, (int(sx-210), int(sy-70)))
        if self.weather in ("rain", "thunderstorm"):
            for r in self.rain:
                pygame.draw.line(self.screen, (180,200,220), (r["x"], r["y"]), (r["x"]-2, r["y"]+6), 1)
        if self.weather == "thunderstorm" and now < self.flash_white:
            fo = pygame.Surface((W, H), pygame.SRCALPHA); fo.fill((240,240,255,110)); self.screen.blit(fo, (0, 0))
        if self.weather == "fog":
            for i in range(3):
                fx = ((now*0.02*(i+1)) % (W+400)) - 200
                fo = pygame.Surface((400, 120), pygame.SRCALPHA)
                pygame.draw.ellipse(fo, (220,225,230,60), (0, 0, 400, 120))
                self.screen.blit(fo, (int(fx-200), 120+i*160))
        if self.weather == "snow":
            for r in self.rain:
                pygame.draw.circle(self.screen, (250,252,255), (int(r["x"]), int(r["y"])), 1)
        if self.weather == "sunshine":
            pygame.draw.circle(self.screen, (255,240,160), (W-120, 90), 60, 4)
        if self.biome in (0,3) and self.weather not in ("rain","thunderstorm"):
            for ff in self.fireflies:
                pygame.draw.circle(self.screen, (255, 240, 140), (int(ff["x"]), int(ff["y"])), 1)
        self.screen.blit(self.light, (0, 0))
        if now < self.flash:
            f = pygame.Surface((W, H), pygame.SRCALPHA); f.fill((180,40,40,70)); self.screen.blit(f, (0, 0))

    def draw_compass(self, now):
        # Treasure compass / off-screen arrows removed — explore to discover chests.
        return

        # Draw bridges LAST so they stay clearly visible over water and props
        vis2 = pygame.Rect(self.camx - W/2 - 80, self.camy - H/2 - 80, W + 160, H + 160)
        ox2, oy2 = int(W/2 - self.camx), int(H/2 - self.camy)
        self.draw_bridges(now, ox2, oy2, vis2)


    def draw_ui(self, now):
        # Top bar — fixed left→right layout so nothing overlaps at any level
        top = pygame.Surface((W, 40), pygame.SRCALPHA); top.fill((14,18,16,200))
        self.screen.blit(top, (0, 0))

        n_hearts = min(self.lives, 10)
        for i in range(n_hearts):
            hx = 14 + i * 18
            pygame.draw.circle(self.screen, C_HEART, (hx, 16), 5)
            pygame.draw.circle(self.screen, C_HEART, (hx + 7, 16), 5)
            pygame.draw.polygon(self.screen, C_HEART, [(hx - 5, 18), (hx + 12, 18), (hx + 3, 27)])

        gx = 14 + max(n_hearts, 1) * 18 + 16
        pygame.draw.circle(self.screen, C_GOLD, (gx, 20), 7)
        gold_txt = self.font.render(str(self.gold), True, C_TEXT)
        self.screen.blit(gold_txt, (gx + 12, 10))
        cursor = gx + 12 + gold_txt.get_width() + 18

        res = getattr(self, "resources", None)
        if res:
            for k, meta in list(RESOURCE_TYPES.items())[:5]:
                n = int(res.get(k, 0))
                if n <= 0:
                    continue
                pygame.draw.circle(self.screen, meta["color"], (cursor, 18), 5)
                nt = self.small.render(str(n), True, meta["color"])
                self.screen.blit(nt, (cursor + 7, 10))
                cursor += 7 + nt.get_width() + 12

        tcol = C_GREEN_OK if self.chests_left() == 0 else C_CYAN
        pygame.draw.polygon(self.screen, tcol, [
            (cursor, 12), (cursor + 6, 20), (cursor, 28), (cursor - 6, 20)
        ])
        tr_txt = self.small.render("Treasures: %d/%d" % (self.chests_opened, self.required_chests), True, tcol)
        self.screen.blit(tr_txt, (cursor + 10, 12))

        lvl_txt = self.small.render(
            "L%d/%d %s" % (self.current_level, NUM_LEVELS, BIOMES[self.biome]["name"]),
            True, (180, 210, 230)
        )
        self.screen.blit(lvl_txt, (W - lvl_txt.get_width() - 14, 12))

        if self.weapon:
            wx = W - lvl_txt.get_width() - 28
            pygame.draw.line(self.screen, (140, 100, 60), (wx, 26), (wx + 8, 12), 3)

        if getattr(self, "beacon_t", 0) > now and getattr(self, "beacon_chest", None) and not self.beacon_chest.get("opened"):
            bc = self.beacon_chest
            dx, dy = bc["x"] - self.px, bc["y"] - self.py
            dist = math.hypot(dx, dy)
            if dist > 1:
                ang = math.atan2(dy, dx)
                ax = W // 2 + int(math.cos(ang) * 70)
                ay = 88 + int(math.sin(ang) * 28)
                tip = (ax + int(math.cos(ang) * 18), ay + int(math.sin(ang) * 18))
                left = (ax + int(math.cos(ang + 2.5) * 10), ay + int(math.sin(ang + 2.5) * 10))
                right = (ax + int(math.cos(ang - 2.5) * 10), ay + int(math.sin(ang - 2.5) * 10))
                pygame.draw.polygon(self.screen, (255, 210, 60), [tip, left, right])
                pygame.draw.polygon(self.screen, (120, 80, 20), [tip, left, right], 2)
                dtxt = self.small.render("%dm" % int(dist / 12), True, (255, 220, 100))
                self.screen.blit(dtxt, (ax - dtxt.get_width() // 2, ay + 16))

        obj = "Find the treasure chest and answer its question correctly."
        o = self.font.render("Objective: " + obj, True, M_YELLOW)
        pill_w = o.get_width() + 30
        pill_x = W // 2 - pill_w // 2
        pill_y = 46
        pill = pygame.Surface((pill_w, 30), pygame.SRCALPHA)
        pill.fill((14, 18, 16, 185))
        self.screen.blit(pill, (pill_x, pill_y))
        pygame.draw.rect(self.screen, M_YELLOW, (pill_x, pill_y, pill_w, 30), 2, border_radius=8)
        self.screen.blit(o, (W // 2 - o.get_width() // 2, pill_y + 4))

        mx, my = W - 162, H - 124
        self.screen.blit(self.mm_base, (mx, my))
        pygame.draw.rect(self.screen, (210, 205, 180), (mx - 1, my - 1, 152, 114), 2)
        pygame.draw.circle(self.screen, (235, 90, 80), (mx + int(self.px / WW * 150), my + int(self.py / WH * 112)), 3)
        if self.prompt and self.dialog is None:
            p = self.small.render("[E] " + self.prompt, True, C_TEXT)
            b = pygame.Surface((p.get_width() + 24, 30), pygame.SRCALPHA); b.fill((14, 18, 16, 200))
            self.screen.blit(b, (W // 2 - p.get_width() // 2 - 12, H - 96))
            pygame.draw.rect(self.screen, C_GOLD, (W // 2 - p.get_width() // 2 - 12, H - 96, p.get_width() + 24, 30), 2, border_radius=6)
            self.screen.blit(p, (W // 2 - p.get_width() // 2, H - 91))
        if self.toast and now - self.toast_t < 4500:
            fnt = self.small if len(self.toast) > 64 else self.font
            t = fnt.render(self.toast, True, C_TEXT)
            b = pygame.Surface((t.get_width() + 30, 40), pygame.SRCALPHA); b.fill((14, 18, 16, 215))
            self.screen.blit(b, (W // 2 - t.get_width() // 2 - 15, H - 150))
            pygame.draw.rect(self.screen, (120, 140, 120), (W // 2 - t.get_width() // 2 - 15, H - 150, t.get_width() + 30, 40), 2, border_radius=8)
            self.screen.blit(t, (W // 2 - t.get_width() // 2, H - 142))
        if self.dash_cd > 0:
            pygame.draw.rect(self.screen, (60, 60, 60), (W - 162, H - 140, 150, 5))
            pygame.draw.rect(self.screen, (140, 200, 200), (W - 162, H - 140, int(150 * (1 - self.dash_cd / 2.5)), 5))
        if self.near_house is not None:
            owner = self.near_house["owner"]
            is_mine = self.near_house.get("is_player", False)
            label = "Mine House" if is_mine else owner + "'s House"
            col = C_GOLD if is_mine else (210, 200, 170)
            nm = self.font.render(label, True, col)
            panel_w = nm.get_width() + 28
            panel = pygame.Surface((panel_w, 36), pygame.SRCALPHA)
            panel.fill((14, 18, 16, 210))
            self.screen.blit(panel, (18, 110))
            pygame.draw.rect(self.screen, col, (18, 110, panel_w, 36), 2, border_radius=6)
            self.screen.blit(nm, (32, 117))

    def draw_button(self, rect, label, mpos, base=(70,90,70)):
        hov = rect.collidepoint(mpos)
        pygame.draw.rect(self.screen, C_GOLD if hov else base, rect, border_radius=10)
        t = self.font.render(label, True, (20,20,20) if hov else C_TEXT)
        self.screen.blit(t, (rect.centerx-t.get_width()//2, rect.centery-t.get_height()//2))

    def get_clicked_level(self, pos):
        mx, my = pos
        for lvl in range(1, NUM_LEVELS + 1):
            x, y = level_positions[lvl - 1]
            if math.hypot(mx - x, my - y) <= 40:
                return lvl if self.level_unlocked[lvl - 1] else None
        return None

    def draw_level_badge(self, s, x, y, biome):
        """Cute stone level node – mossy forest style with depth."""
        # soft ground shadow
        sh = pygame.Surface((70, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (40, 55, 30, 70), (0, 4, 70, 22))
        s.blit(sh, (x - 35, y + 18))
        # outer dark rim
        pygame.draw.circle(s, (55, 70, 45), (x, y + 2), 34)
        # stone body – cool blue-grey like reference, tinted with forest
        base = (110, 130, 150)
        pygame.draw.circle(s, (70, 85, 100), (x, y + 1), 30)
        pygame.draw.circle(s, base, (x, y), 30)
        # moss edge
        pygame.draw.arc(s, (70, 130, 75), (x - 28, y - 28, 56, 56), 3.6, 5.6, 4)
        # top gloss
        pygame.draw.circle(s, (160, 180, 200), (x - 8, y - 10), 10)
        pygame.draw.circle(s, (220, 235, 245), (x - 10, y - 12), 4)
        # thin rim
        pygame.draw.circle(s, (90, 110, 125), (x, y), 30, 2)

    def draw_map(self):
        """Attractive mobile-style winding forest level map."""
        s = self.screen
        Wmap, Hmap = MAP_W, MAP_H

        # === Warm sandy / dirt ground (matches reference) but greener highland tint ===
        for i in range(Hmap):
            t = i / max(1, Hmap)
            r = int(210 - t * 25)
            g = int(185 - t * 20)
            b = int(120 - t * 15)
            pygame.draw.line(s, (r, g, b), (0, i), (Wmap, i))

        # subtle terrain noise dots
        rnd = random.Random(42)
        for _ in range(180):
            px, py = rnd.randint(0, Wmap - 1), rnd.randint(0, Hmap - 1)
            pygame.draw.circle(s, shade((200, 175, 110), rnd.choice([-18, -10, 8, 14])), (px, py), rnd.randint(1, 3))

        # === Green meadow islands (forest patches) ===
        meadows = [
            (60, 80, 140, 100), (200, 40, 160, 90), (400, 60, 180, 110),
            (620, 30, 150, 95), (850, 70, 170, 100), (980, 200, 140, 120),
            (40, 280, 120, 100), (50, 480, 130, 110), (300, 200, 110, 90),
            (500, 250, 140, 100), (720, 180, 130, 95), (900, 350, 150, 110),
            (200, 650, 180, 90), (450, 620, 160, 100), (700, 600, 170, 110),
            (950, 550, 140, 100), (100, 360, 100, 80), (580, 380, 120, 90),
        ]
        for mx, my, mw, mh in meadows:
            # soft shadow
            pygame.draw.ellipse(s, (160, 140, 90), (mx + 6, my + 8, mw, mh))
            # main green
            pygame.draw.ellipse(s, (70, 150, 75), (mx, my, mw, mh))
            pygame.draw.ellipse(s, (95, 175, 95), (mx + 10, my + 8, mw - 24, mh - 22))
            # darker edge moss
            pygame.draw.ellipse(s, (50, 120, 60), (mx, my, mw, mh), 3)

        # === Cute trees on meadows ===
        def map_pine(x, y, sc=1.0):
            pygame.draw.rect(s, (90, 60, 40), (int(x - 3 * sc), int(y), max(2, int(6 * sc)), int(14 * sc)))
            for i, (hh, hw, col) in enumerate([
                (22, 16, (35, 105, 50)), (16, 12, (45, 125, 60)), (10, 8, (55, 145, 70))
            ]):
                top = y - (i + 1) * 10 * sc
                pygame.draw.polygon(s, col, [
                    (int(x), int(top)),
                    (int(x - hw * sc), int(top + hh * sc * 0.55)),
                    (int(x + hw * sc), int(top + hh * sc * 0.55)),
                ])

        def map_round_tree(x, y, sc=1.0):
            pygame.draw.rect(s, (95, 65, 40), (int(x - 3 * sc), int(y), max(2, int(5 * sc)), int(12 * sc)))
            pygame.draw.circle(s, (40, 120, 55), (int(x), int(y - 10 * sc)), int(14 * sc))
            pygame.draw.circle(s, (60, 150, 75), (int(x - 5 * sc), int(y - 14 * sc)), int(9 * sc))
            pygame.draw.circle(s, (70, 160, 80), (int(x + 5 * sc), int(y - 12 * sc)), int(8 * sc))

        for tx, ty, sc, kind in [
            (80, 120, 1.1, "pine"), (160, 90, 0.9, "round"), (280, 100, 1.2, "pine"),
            (420, 85, 1.0, "round"), (560, 70, 1.15, "pine"), (700, 95, 0.95, "round"),
            (880, 110, 1.2, "pine"), (1000, 240, 1.0, "round"), (70, 330, 0.9, "pine"),
            (320, 240, 1.0, "round"), (520, 290, 1.1, "pine"), (760, 220, 0.95, "round"),
            (940, 400, 1.15, "pine"), (120, 530, 1.0, "round"), (280, 680, 0.9, "pine"),
            (500, 660, 1.1, "round"), (740, 640, 1.0, "pine"), (980, 600, 0.95, "round"),
            (180, 300, 0.8, "pine"), (620, 420, 0.85, "round"),
        ]:
            if kind == "pine":
                map_pine(tx, ty, sc)
            else:
                map_round_tree(tx, ty, sc)

        # === Rocks / stones scattered ===
        for rx, ry, rw, rh, col in [
            (340, 250, 36, 28, (150, 120, 90)), (480, 180, 30, 24, (140, 115, 85)),
            (600, 300, 40, 30, (155, 125, 95)), (820, 280, 34, 26, (145, 118, 88)),
            (150, 200, 28, 22, (135, 110, 80)), (920, 480, 38, 28, (150, 122, 92)),
            (400, 420, 32, 24, (140, 112, 82)), (700, 360, 30, 22, (148, 120, 90)),
        ]:
            pygame.draw.ellipse(s, darken(col, 25), (rx + 2, ry + 4, rw, rh))
            pygame.draw.ellipse(s, col, (rx, ry, rw, rh))
            pygame.draw.ellipse(s, lighten(col, 30), (rx + 6, ry + 4, rw // 3, rh // 3))

        # === White daisies ===
        def flower(fx, fy, scale=1.0):
            for a in range(0, 360, 60):
                rad = math.radians(a)
                px = fx + math.cos(rad) * 5 * scale
                py = fy + math.sin(rad) * 5 * scale
                pygame.draw.circle(s, (250, 250, 245), (int(px), int(py)), max(2, int(3 * scale)))
            pygame.draw.circle(s, (255, 210, 70), (int(fx), int(fy)), max(2, int(3 * scale)))

        for fx, fy in [
            (50, 140), (120, 100), (250, 70), (380, 120), (500, 50), (650, 90),
            (800, 60), (960, 150), (100, 400), (280, 280), (450, 340), (600, 200),
            (750, 300), (900, 450), (80, 600), (350, 640), (550, 680), (800, 620),
            (980, 580), (200, 480), (420, 200), (680, 500),
        ]:
            flower(fx, fy, 0.9 + (fx % 5) * 0.05)

        # === Winding path under levels (thick orange dirt trail) ===
        # Build smooth path through all level nodes
        pts = list(level_positions)
        # draw as overlapping thick circles + segments for a soft trail
        path_col_outer = (180, 120, 55)
        path_col_mid = (220, 155, 70)
        path_col_inner = (235, 185, 100)

        def path_point(t):
            """t in [0, NUM_LEVELS-1] interpolate along nodes."""
            if t <= 0:
                return pts[0]
            if t >= len(pts) - 1:
                return pts[-1]
            i = int(t)
            f = t - i
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            # slight curve via perpendicular offset
            dx, dy = x2 - x1, y2 - y1
            ox, oy = -dy * 0.12 * math.sin(f * math.pi), dx * 0.12 * math.sin(f * math.pi)
            return (lerp(x1, x2, f) + ox, lerp(y1, y2, f) + oy)

        # fat trail
        for step in range(0, (NUM_LEVELS - 1) * 20 + 1):
            t = step / 20.0
            px, py = path_point(t)
            pygame.draw.circle(s, path_col_outer, (int(px), int(py)), 28)
        for step in range(0, (NUM_LEVELS - 1) * 20 + 1):
            t = step / 20.0
            px, py = path_point(t)
            pygame.draw.circle(s, path_col_mid, (int(px), int(py)), 20)
        for step in range(0, (NUM_LEVELS - 1) * 20 + 1):
            t = step / 20.0
            px, py = path_point(t)
            pygame.draw.circle(s, path_col_inner, (int(px), int(py)), 12)

        # footstep / pebble marks on path
        for step in range(0, (NUM_LEVELS - 1) * 8 + 1):
            t = step / 8.0
            px, py = path_point(t)
            pygame.draw.circle(s, (200, 150, 70), (int(px + 6), int(py + 3)), 3)
            pygame.draw.circle(s, (190, 140, 60), (int(px - 5), int(py - 2)), 2)

        # === Treasure gift landmark near mid path (cute box like reference) ===
        gx, gy = 500, 300
        # green hill under gift
        pygame.draw.ellipse(s, (60, 140, 70), (gx - 70, gy - 20, 140, 90))
        pygame.draw.ellipse(s, (85, 165, 90), (gx - 55, gy - 10, 110, 70))
        # box
        pygame.draw.rect(s, (50, 130, 200), (gx - 28, gy - 10, 56, 42), border_radius=6)
        pygame.draw.rect(s, (70, 160, 230), (gx - 28, gy - 10, 56, 14), border_radius=4)
        # ribbon
        pygame.draw.rect(s, (200, 60, 160), (gx - 5, gy - 10, 10, 42))
        pygame.draw.rect(s, (200, 60, 160), (gx - 28, gy + 6, 56, 10))
        # bow
        pygame.draw.circle(s, (230, 80, 180), (gx - 12, gy - 18), 10)
        pygame.draw.circle(s, (230, 80, 180), (gx + 12, gy - 18), 10)
        pygame.draw.circle(s, (255, 120, 200), (gx, gy - 14), 7)
        # little tree beside gift
        map_round_tree(gx + 55, gy + 25, 0.85)

        # === UI header panels ===
        def panel(rect, title, cx, cy, font):
            pygame.draw.rect(s, (40, 28, 18), (rect[0] - 3, rect[1] - 3, rect[2] + 6, rect[3] + 6), border_radius=16)
            pygame.draw.rect(s, M_BROWN, rect, border_radius=14)
            pygame.draw.rect(s, (180, 140, 70), rect, 2, border_radius=14)
            if title:
                mtext(s, title, font, M_YELLOW if "BRAIN" in title else M_WHITE, cx, cy)

        panel((20, 18, 250, 68), "TREKKER", 145, 52, self.map_level_f)
        panel((385, 16, 330, 76), "BRAIN TREK", 550, 54, self.map_title_f)
        total = sum(self.level_stars)
        panel((850, 18, 220, 60), "", 960, 48, self.map_level_f)
        mstar(s, 885, 48, 15, M_YELLOW)
        mtext(s, "%d/%d" % (total, NUM_LEVELS * 3), self.map_level_f, M_WHITE, 970, 48)

        # === Level nodes ===
        for lvl in range(1, NUM_LEVELS + 1):
            x, y = level_positions[lvl - 1]
            biome = biome_for(lvl)
            unlocked = self.level_unlocked[lvl - 1]
            if unlocked:
                # warm glow for unlocked
                for rr, aa in [(42, 35), (36, 55)]:
                    g = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                    pygame.draw.circle(g, (255, 220, 120, aa), (rr, rr), rr)
                    s.blit(g, (x - rr, y - rr))
                # bright ring when this level is selected for START
                if getattr(self, "map_selected_level", None) == lvl:
                    pygame.draw.circle(s, C_GOLD, (x, y), 36, 3)
                    pygame.draw.circle(s, (255, 240, 160), (x, y), 40, 2)
                self.draw_level_badge(s, x, y, biome)
                mtext(s, str(lvl), self.map_level_f, M_WHITE, x, y)
                # stars under node
                stars = self.level_stars[lvl - 1]
                for i in range(3):
                    sx = x - 22 + i * 22
                    sy = y + 42
                    col = M_YELLOW if i < stars else (140, 140, 130)
                    mstar(s, sx, sy, 9, col)
                # tiny biome label
                short_name = BIOMES[biome]["name"].split()[0]
                nm = self.small.render(short_name, True, (40, 60, 35))
                bgw = nm.get_width() + 10
                pygame.draw.rect(s, (230, 240, 210), (x - bgw // 2, y + 54, bgw, 16), border_radius=6)
                s.blit(nm, (x - nm.get_width() // 2, y + 55))
            else:
                # locked – muted stone + padlock
                sh = pygame.Surface((70, 28), pygame.SRCALPHA)
                pygame.draw.ellipse(sh, (40, 55, 30, 50), (0, 4, 70, 22))
                s.blit(sh, (x - 35, y + 18))
                pygame.draw.circle(s, (70, 75, 80), (x, y + 2), 32)
                pygame.draw.circle(s, (100, 108, 118), (x, y), 30)
                pygame.draw.circle(s, (80, 88, 98), (x, y), 30, 2)
                # padlock
                pygame.draw.rect(s, (45, 50, 55), (x - 9, y - 2, 18, 14), border_radius=3)
                pygame.draw.arc(s, (45, 50, 55), (x - 7, y - 14, 14, 16), math.pi, 2 * math.pi, 3)
                pygame.draw.circle(s, (200, 190, 100), (x, y + 4), 2)

        tip = self.small.render("Explore each highland to find hidden treasure chests and answer their questions!", True, (60, 80, 50))
        # tip on light strip
        pygame.draw.rect(s, (230, 215, 160), (0, Hmap - 28, Wmap, 28))
        s.blit(tip, (Wmap // 2 - tip.get_width() // 2, Hmap - 22))
        m = pygame.mouse.get_pos()
        # START — dark/inactive until a level is selected, then normal active look
        btn = getattr(self, "map_start_btn", pygame.Rect(MAP_W - 360, MAP_H - 78, 150, 46))
        self.map_start_btn = btn
        sel = getattr(self, "map_selected_level", None)
        active = sel is not None and 1 <= sel <= NUM_LEVELS and self.level_unlocked[sel - 1]
        hov = btn.collidepoint(m) and active
        if active:
            pygame.draw.rect(s, (50, 35, 20), (btn.x - 2, btn.y - 2, btn.w + 4, btn.h + 4), border_radius=12)
            pygame.draw.rect(s, (150, 100, 45) if hov else M_BROWN, btn, border_radius=10)
            pygame.draw.rect(s, C_GOLD, btn, 2, border_radius=10)
            st = self.font.render("START", True, M_YELLOW if hov else (255, 230, 140))
        else:
            pygame.draw.rect(s, (25, 22, 20), (btn.x - 2, btn.y - 2, btn.w + 4, btn.h + 4), border_radius=12)
            pygame.draw.rect(s, (55, 50, 48), btn, border_radius=10)
            pygame.draw.rect(s, (80, 75, 70), btn, 2, border_radius=10)
            st = self.font.render("START", True, (110, 105, 100))
        s.blit(st, (btn.centerx - st.get_width() // 2, btn.centery - st.get_height() // 2))
        self.draw_button(self.map_shop, "SHOP", m, base=(110, 80, 40))

    def draw_customize(self, now):
        """Character customization – gender + skin selection."""
        self.screen.fill((22, 32, 28))
        # panel
        panel = pygame.Rect(180, 40, 740, 620)
        pygame.draw.rect(self.screen, (28, 36, 32), panel, border_radius=16)
        pygame.draw.rect(self.screen, C_GOLD, panel, 3, border_radius=16)

        title = self.title_f.render("CUSTOMIZE", True, C_GOLD)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 60))

        # --- Gender selection ---
        g_label = self.font.render("Gender", True, C_TEXT)
        self.screen.blit(g_label, (240, 140))

        male_r = pygame.Rect(240, 175, 160, 48)
        female_r = pygame.Rect(420, 175, 160, 48)
        m = pygame.mouse.get_pos()
        for r, label, g in [(male_r, "MALE", "male"), (female_r, "FEMALE", "female")]:
            active = self.gender == g
            hov = r.collidepoint(m)
            col = C_GOLD if active else ((90, 110, 80) if hov else (50, 60, 55))
            pygame.draw.rect(self.screen, col, r, border_radius=10)
            pygame.draw.rect(self.screen, C_GOLD if active else (100, 100, 90), r, 2, border_radius=10)
            t = self.font.render(label, True, (20, 20, 20) if active or hov else C_TEXT)
            self.screen.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))
        self.custom_male_r = male_r
        self.custom_female_r = female_r

        # --- Preview ---
        pygame.draw.rect(self.screen, (18, 24, 20), (680, 140, 180, 220), border_radius=12)
        pygame.draw.rect(self.screen, C_GOLD, (680, 140, 180, 220), 2, border_radius=12)
        skin_data = SKINS.get(self.skin, SKINS["classic"])
        # draw larger preview
        px, py = 770, 300
        # scale-like by drawing twice offset for thickness
        draw_anime_player(self.screen, px, py, "down", int(now * 0.01), False, skin_data, self.gender)
        prev_label = self.small.render("Preview", True, (180, 180, 160))
        self.screen.blit(prev_label, (770 - prev_label.get_width() // 2, 150))

        # --- Skin selection ---
        s_label = self.font.render("Outfit / Skin", True, C_TEXT)
        self.screen.blit(s_label, (240, 250))
        self.custom_skin_rects = []
        y0 = 290
        for i, (sid, sdata) in enumerate(SKINS.items()):
            owned = sid in self.skins_owned
            r = pygame.Rect(240, y0 + i * 52, 400, 46)
            self.custom_skin_rects.append((r, sid))
            active = self.skin == sid
            hov = r.collidepoint(m)
            if not owned:
                pygame.draw.rect(self.screen, (40, 40, 45), r, border_radius=8)
                pygame.draw.rect(self.screen, (80, 80, 80), r, 1, border_radius=8)
                t = self.small.render("%s  (buy in Shop – %dg)" % (sdata["name"], sdata["price"]), True, (120, 120, 120))
            else:
                col = C_GOLD if active else ((70, 90, 70) if hov else (45, 55, 50))
                pygame.draw.rect(self.screen, col, r, border_radius=8)
                pygame.draw.rect(self.screen, C_GOLD if active else (100, 110, 90), r, 2, border_radius=8)
                # color swatch
                pygame.draw.rect(self.screen, sdata["robe"], (r.x + 12, r.centery - 10, 20, 20), border_radius=3)
                t = self.font.render(sdata["name"], True, (20, 20, 20) if active or hov else C_TEXT)
            self.screen.blit(t, (r.x + 40, r.centery - t.get_height() // 2))

        # note
        note = self.small.render("Female characters wear the traditional Bhutanese Kira. Male characters wear the Gho.", True, (160, 165, 150))
        self.screen.blit(note, (W // 2 - note.get_width() // 2, 560))

        # Back button — return to pause / title / map
        back_r = pygame.Rect(W // 2 - 120, 600, 240, 44)
        src = getattr(self, "customize_from", "MAP")
        back_label = "BACK TO PAUSE" if src == "PAUSE" else ("BACK TO TITLE" if src == "TITLE" else "BACK TO MAP")
        self.draw_button(back_r, back_label, m, base=(60, 80, 100))
        self.custom_back_r = back_r

    def enter_house_interior(self):
        """Switch into walkable Mine House interior."""
        self.house_out_px, self.house_out_py = self.px, self.py
        self.hx_pos, self.hy_pos = float(W // 2), float(H - 130)
        self.hx_vx = self.hy_vy = 0.0
        self.house_walk = 0.0
        self.house_dir = "up"
        self.house_moving = False
        self.house_chest_opened = getattr(self, "house_chest_opened", False)
        self.state = "HOUSE"
        self.audio.play("open")
        self.say("Welcome home. Walk around — press M near the door to leave.")

    def update_house(self, now, dt):
        """Player movement inside Mine House (faster)."""
        keys = pygame.key.get_pressed()
        dx = (1 if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) else 0) - (1 if (keys[pygame.K_a] or keys[pygame.K_LEFT]) else 0)
        dy = (1 if (keys[pygame.K_s] or keys[pygame.K_DOWN]) else 0) - (1 if (keys[pygame.K_w] or keys[pygame.K_UP]) else 0)
        running = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        sp = 10.0 if running else 8.0   # 2x faster movement inside
        if dx or dy:
            L = math.hypot(dx, dy)
            self.hx_vx = lerp(self.hx_vx, dx / L * sp, .4)
            self.hy_vy = lerp(self.hy_vy, dy / L * sp, .4)
            if dx > 0: self.house_dir = "right"
            elif dx < 0: self.house_dir = "left"
            elif dy > 0: self.house_dir = "down"
            elif dy < 0: self.house_dir = "up"
        else:
            self.hx_vx *= .7
            self.hy_vy *= .7
        self.house_moving = math.hypot(self.hx_vx, self.hy_vy) > .3
        # Room walkable area (inside walls)
        margin_l, margin_r = 55, 55
        margin_t, margin_b = 175, 55
        nx = clamp(self.hx_pos + self.hx_vx, margin_l, W - margin_r)
        ny = clamp(self.hy_pos + self.hy_vy, margin_t, H - margin_b)
        # Block walking through the low table
        tx, ty, tw, th = W // 2 - 55, H // 2 - 25, 110, 55
        if tx < nx < tx + tw and ty < ny < ty + th:
            nx, ny = self.hx_pos, self.hy_pos
        self.hx_pos, self.hy_pos = nx, ny
        if self.house_moving:
            self.house_walk += dt * 10
        door_x, door_y = W // 2, H - 40
        self.house_near_door = math.hypot(self.hx_pos - door_x, self.hy_pos - door_y) < 90
        # Near question chest
        cx, cy = W // 2 + 180, H // 2 + 40
        self.house_near_chest = (not getattr(self, "house_chest_opened", False)
                                 and math.hypot(self.hx_pos - cx, self.hy_pos - cy) < 55)

    def draw_house(self, now):
        """Walkable 3D-style Mine House interior – realistic timber room, no king portraits."""
        # Sky / exterior hint above walls
        self.screen.fill((55, 70, 85))

        # === Perspective floor (darker at top = farther) ===
        for i in range(20):
            t = i / 20.0
            y0 = 155 + int(t * (H - 195))
            y1 = 155 + int((t + 1/20) * (H - 195))
            shade_v = int(75 + t * 35)
            pygame.draw.rect(self.screen, (shade_v, shade_v - 18, shade_v - 30), (0, y0, W, y1 - y0 + 1))
        # Floor boards with perspective taper
        for i in range(12):
            t = i / 12.0
            y = 160 + int(t * (H - 210))
            inset = int(40 + (1 - t) * 50)
            col = (95 + int(t * 25), 70 + int(t * 15), 42)
            pygame.draw.line(self.screen, col, (inset, y), (W - inset, y), 2)
        for i in range(8):
            x = 80 + i * ((W - 160) // 8)
            pygame.draw.line(self.screen, (55, 40, 28), (x, 160), (x + int((x - W/2) * 0.08), H - 50), 1)

        # === Back wall (far wall – lighter = depth) ===
        pygame.draw.rect(self.screen, (92, 68, 48), (30, 40, W - 60, 120))
        # wall gradient (top darker under roof)
        for i in range(8):
            a = 18 - i * 2
            s = pygame.Surface((W - 60, 12), pygame.SRCALPHA)
            s.fill((30, 20, 12, a))
            self.screen.blit(s, (30, 40 + i * 12))
        # traditional red-green cornice
        for i in range(0, W - 60, 18):
            col = (175, 45, 38) if (i // 18) % 2 == 0 else (45, 110, 55)
            pygame.draw.rect(self.screen, col, (30 + i, 148, 18, 10))
        # timber beams on back wall
        for bx in (80, W // 2, W - 80):
            pygame.draw.rect(self.screen, (60, 42, 28), (bx - 6, 45, 12, 100))
            pygame.draw.rect(self.screen, (85, 62, 40), (bx - 4, 47, 4, 96))

        # Window with light (left)
        pygame.draw.rect(self.screen, (40, 30, 20), (70, 55, 90, 70), border_radius=2)
        pygame.draw.rect(self.screen, (160, 200, 220), (76, 60, 78, 58))
        pygame.draw.line(self.screen, (50, 40, 28), (115, 60), (115, 118), 3)
        pygame.draw.line(self.screen, (50, 40, 28), (76, 89), (154, 89), 3)
        # soft light pool on floor from window
        light = pygame.Surface((140, 90), pygame.SRCALPHA)
        pygame.draw.ellipse(light, (255, 240, 200, 35), (0, 0, 140, 90))
        self.screen.blit(light, (55, 160))

        # Window (right)
        pygame.draw.rect(self.screen, (40, 30, 20), (W - 160, 55, 90, 70), border_radius=2)
        pygame.draw.rect(self.screen, (160, 200, 220), (W - 154, 60, 78, 58))
        pygame.draw.line(self.screen, (50, 40, 28), (W - 115, 60), (W - 115, 118), 3)
        pygame.draw.line(self.screen, (50, 40, 28), (W - 154, 89), (W - 76, 89), 3)
        light2 = pygame.Surface((140, 90), pygame.SRCALPHA)
        pygame.draw.ellipse(light2, (255, 240, 200, 30), (0, 0, 140, 90))
        self.screen.blit(light2, (W - 180, 160))

        # Center wall hanging – mandala (keeps Bhutanese feel, no kings)
        pygame.draw.rect(self.screen, (35, 25, 18), (W // 2 - 55, 48, 110, 95), border_radius=3)
        pygame.draw.rect(self.screen, (200, 160, 50), (W // 2 - 55, 48, 110, 95), 3, border_radius=3)
        for r, col in [(38, (160, 100, 40)), (26, (210, 170, 70)), (14, (240, 210, 120))]:
            pygame.draw.circle(self.screen, col, (W // 2, 95), r, 3 if r > 18 else 0)
        pygame.draw.circle(self.screen, (200, 55, 45), (W // 2, 95), 7)

        # Ceiling beam
        pygame.draw.rect(self.screen, (45, 32, 20), (0, 0, W, 42))
        pygame.draw.rect(self.screen, (70, 50, 32), (0, 38, W, 6))
        title = self.font.render("Mine House", True, C_GOLD)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 8))

        # === Side walls with depth (angled look via color) ===
        # Left wall
        pygame.draw.polygon(self.screen, (72, 52, 36), [(0, 40), (30, 40), (30, H - 40), (0, H - 40)])
        pygame.draw.polygon(self.screen, (58, 42, 28), [(0, 40), (30, 40), (30, H - 40), (0, H - 40)], 2)
        for yy in range(55, H - 55, 48):
            pygame.draw.polygon(self.screen, (130, 95, 55), [
                (14, yy), (24, yy + 10), (14, yy + 20), (4, yy + 10)
            ])
        # Right wall
        pygame.draw.polygon(self.screen, (72, 52, 36), [(W, 40), (W - 30, 40), (W - 30, H - 40), (W, H - 40)])
        for yy in range(55, H - 55, 48):
            pygame.draw.polygon(self.screen, (130, 95, 55), [
                (W - 14, yy), (W - 4, yy + 10), (W - 14, yy + 20), (W - 24, yy + 10)
            ])

        # === Bottom threshold / door ===
        pygame.draw.rect(self.screen, (48, 34, 22), (0, H - 45, W, 45))
        for i in range(0, W, 16):
            col = (175, 45, 38) if (i // 16) % 2 == 0 else (45, 110, 55)
            pygame.draw.rect(self.screen, col, (i, H - 45, 16, 8))
        # Door with depth
        door_rect = pygame.Rect(W // 2 - 42, H - 70, 84, 55)
        pygame.draw.rect(self.screen, (55, 38, 22), (door_rect.x - 4, door_rect.y - 4, door_rect.w + 8, door_rect.h + 6))
        pygame.draw.rect(self.screen, (110, 78, 45), door_rect, border_radius=3)
        pygame.draw.rect(self.screen, (145, 105, 60), door_rect, 3, border_radius=3)
        pygame.draw.line(self.screen, (80, 55, 30), (W // 2, H - 66), (W // 2, H - 20), 2)
        pygame.draw.circle(self.screen, C_GOLD, (W // 2 + 28, H - 42), 5)
        pygame.draw.circle(self.screen, (180, 140, 50), (W // 2 + 28, H - 42), 3)
        self.house_exit_rect = door_rect

        if getattr(self, "house_near_door", False):
            p = self.small.render("[M] Exit House", True, C_GOLD)
            bg = pygame.Surface((p.get_width() + 20, 28), pygame.SRCALPHA)
            bg.fill((14, 18, 16, 220))
            self.screen.blit(bg, (W // 2 - p.get_width() // 2 - 10, H - 105))
            self.screen.blit(p, (W // 2 - p.get_width() // 2, H - 100))

        # === Furniture with simple 3D (shadow + top) ===
        # Low table
        tx, ty, tw, th = W // 2 - 55, H // 2 - 18, 110, 48
        soft_shadow(self.screen, tx + tw // 2, ty + th, tw // 2 + 8, 12, 90)
        pygame.draw.rect(self.screen, (70, 48, 28), (tx, ty + 8, tw, th - 4), border_radius=3)  # body
        pygame.draw.rect(self.screen, (120, 90, 55), (tx - 4, ty, tw + 8, 14), border_radius=3)  # top surface
        pygame.draw.rect(self.screen, (150, 115, 70), (tx - 4, ty, tw + 8, 14), 2, border_radius=3)
        # Cushions with volume
        soft_shadow(self.screen, W // 2 - 75, H // 2 + 55, 22, 10, 70)
        pygame.draw.ellipse(self.screen, (140, 40, 35), (W // 2 - 95, H // 2 + 42, 44, 26))
        pygame.draw.ellipse(self.screen, (175, 55, 48), (W // 2 - 93, H // 2 + 40, 40, 20))
        soft_shadow(self.screen, W // 2 + 75, H // 2 + 55, 22, 10, 70)
        pygame.draw.ellipse(self.screen, (35, 85, 55), (W // 2 + 51, H // 2 + 42, 44, 26))
        pygame.draw.ellipse(self.screen, (50, 120, 75), (W // 2 + 53, H // 2 + 40, 40, 20))

        # Shelf on left wall
        pygame.draw.rect(self.screen, (80, 55, 35), (40, 200, 50, 8))
        pygame.draw.rect(self.screen, (100, 70, 45), (42, 185, 14, 16), border_radius=2)
        pygame.draw.rect(self.screen, (90, 65, 40), (60, 188, 18, 13), border_radius=2)

        # === Question chest / quiz box ===
        cx, cy = W // 2 + 180, H // 2 + 40
        opened = getattr(self, "house_chest_opened", False)
        soft_shadow(self.screen, cx, cy + 8, 28, 12, 100)
        if opened:
            pygame.draw.rect(self.screen, (90, 65, 40), (cx - 22, cy - 8, 44, 22), border_radius=3)
            pygame.draw.polygon(self.screen, (110, 80, 50), [
                (cx - 22, cy - 8), (cx + 22, cy - 8), (cx + 16, cy - 28), (cx - 16, cy - 28)
            ])
        else:
            rarity_col = (120, 220, 235)
            pygame.draw.rect(self.screen, (120, 85, 45), (cx - 22, cy - 12, 44, 28), border_radius=3)
            pygame.draw.rect(self.screen, (145, 105, 55), (cx - 18, cy - 8, 36, 20), border_radius=2)
            pygame.draw.rect(self.screen, rarity_col, (cx - 22, cy - 16, 44, 6), border_radius=2)
            pygame.draw.rect(self.screen, C_GOLD, (cx - 5, cy - 4, 10, 10), border_radius=1)
            pygame.draw.circle(self.screen, (50, 35, 20), (cx, cy + 1), 3)
            # pulse glow
            pulse = int(abs(math.sin(now * 0.006)) * 18)
            g = pygame.Surface((70, 70), pygame.SRCALPHA)
            pygame.draw.circle(g, (120, 220, 235, 50), (35, 35), 28 + pulse // 2)
            self.screen.blit(g, (cx - 35, cy - 35))
        if getattr(self, "house_near_chest", False) and not opened:
            p = self.small.render("[E] Open Question Chest", True, C_CYAN)
            bg = pygame.Surface((p.get_width() + 16, 24), pygame.SRCALPHA)
            bg.fill((10, 14, 18, 220))
            self.screen.blit(bg, (cx - p.get_width() // 2 - 8, cy - 48))
            self.screen.blit(p, (cx - p.get_width() // 2, cy - 45))

        # === Player ===
        skin_data = SKINS.get(self.skin, SKINS["classic"])
        draw_anime_player(
            self.screen,
            int(self.hx_pos), int(self.hy_pos),
            getattr(self, "house_dir", "down"),
            int(getattr(self, "house_walk", 0)),
            getattr(self, "house_moving", False),
            skin_data,
            self.gender if hasattr(self, "gender") else "male"
        )

        hint = self.small.render("WASD walk  •  Shift run  •  M exit door  •  E open chest", True, (190, 185, 170))
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 22))

    def _finish_intro(self):
        if self.intro_done:
            return
        self.intro_done = True
        self.state = "TITLE"
        try:
            self.audio.play("quest")
        except Exception:
            pass

    def draw_intro(self, now):
        """Intro: image3.png with large title + bottom-center poem, stanza by stanza."""
        elapsed = (now - self.intro_start) / 1000.0

        bg = getattr(self, "intro_bg_scaled", None)
        if bg is not None:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill((22, 48, 32))
            tip = self.small.render("Place image3.png in assets/images", True, (220, 230, 210))
            self.screen.blit(tip, (W // 2 - tip.get_width() // 2, H // 2 - 10))

        # Soft vignette (edges only — keep center art clear)
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(90):
            a = int(120 * (1.0 - i / 90.0) ** 1.3)
            pygame.draw.line(overlay, (6, 14, 10, a), (0, i), (W, i))
            pygame.draw.line(overlay, (6, 14, 10, a), (0, H - 1 - i), (W, H - 1 - i))
        # Stronger bottom panel for poem readability
        for i in range(160):
            a = int(200 * (i / 160.0) ** 1.4)
            pygame.draw.line(overlay, (8, 16, 12, a), (0, H - 160 + i), (W, H - 160 + i))
        self.screen.blit(overlay, (0, 0))

        def fade_alpha(local_t, fade_in=0.9, hold=3.2, fade_out=0.7):
            if local_t < 0:
                return 0
            if local_t < fade_in:
                return int(255 * (local_t / max(0.01, fade_in)))
            if local_t < fade_in + hold:
                return 255
            remaining = fade_in + hold + fade_out - local_t
            return max(0, int(255 * (remaining / max(0.01, fade_out))))

        def text_shadow(font, txt, color, x, y, alpha, center=False):
            if alpha <= 0:
                return 0
            img = font.render(txt, True, color)
            sh = font.render(txt, True, (12, 18, 14))
            if center:
                x = x - img.get_width() // 2
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-2, -1), (2, 1)):
                s = sh.copy()
                s.set_alpha(min(255, alpha))
                self.screen.blit(s, (x + dx, y + dy))
            img = img.copy()
            img.set_alpha(alpha)
            self.screen.blit(img, (x, y))
            return img.get_height()

        # Professional palette on green art
        gold = (242, 210, 110)
        cream = (255, 248, 230)
        soft_gold = (220, 195, 130)

        try:
            f_title = pygame.font.SysFont("Arial", 52, bold=True)
            f_tag = pygame.font.SysFont("Arial", 20, bold=True)
            f_poem = pygame.font.SysFont("Arial", 22, bold=True)
            f_skip = pygame.font.SysFont("Arial", 16, bold=True)
        except Exception:
            f_title, f_tag, f_poem, f_skip = self.title_f, self.font, self.font, self.small

        # Title — top center (larger)
        a = fade_alpha(elapsed - 0.0, 0.8, 12.0, 1.0)
        text_shadow(f_title, "BRAIN TREK", gold, W // 2, 28, a, center=True)
        text_shadow(f_tag, "EXPLORE  ·  LEARN  ·  PROTECT", soft_gold, W // 2, 88, a, center=True)

        # Poem stanzas — bottom middle, one after another
        stanzas = [
            [
                "In the heart of a mysterious highland forest,",
                "ancient treasures lie hidden among the trees.",
            ],
            [
                "A young explorer sets out to uncover them —",
                "but knowledge is the true key.",
            ],
            [
                "Science · Math · History · Ecology",
            ],
            [
                "Answer wisely. Survive the wild.",
                "Protect the land. Help the people.",
            ],
            [
                "The adventure begins...",
            ],
        ]
        # Timing: each stanza fades in, holds, then next starts (overlap slightly)
        stanza_starts = [2.0, 5.2, 8.4, 10.8, 13.6]
        stanza_hold = 3.0

        base_y = H - 150
        for i, stanza in enumerate(stanzas):
            t0 = stanza_starts[i]
            alpha = fade_alpha(elapsed - t0, 0.7, stanza_hold, 0.6)
            if alpha <= 0:
                continue
            # Stack lines of this stanza centered
            line_h = 28
            total_h = len(stanza) * line_h
            # Show only the current/active stanza in the bottom center
            # (previous ones fade out via fade_alpha)
            sy = base_y + (40 - total_h) // 2
            col = gold if i >= 3 else cream
            for j, line in enumerate(stanza):
                text_shadow(f_poem, line, col, W // 2, sy + j * line_h, alpha, center=True)

        # Skip hint
        skip = f_skip.render("Click or press SPACE to continue", True, cream)
        sh = f_skip.render("Click or press SPACE to continue", True, (0, 0, 0))
        sx = W - 20 - skip.get_width()
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            self.screen.blit(sh, (sx + dx, 12 + dy))
        self.screen.blit(skip, (sx, 12))

        dur = getattr(self, "intro_duration", 16.0) or 16.0
        if elapsed >= dur and not self.intro_done:
            self._finish_intro()

    def draw_title(self, now):
        """Home screen: image2.png full-bleed. Click anywhere to start."""
        bg = getattr(self, "title_bg_scaled", None)
        if bg is None:
            # try load image2 on the fly
            for p in (
                os.path.join(IMAGE_DIR, "image2.png"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ".", "image2.png"),
                os.path.join(os.getcwd(), "image2.png"),
                "/home/workdir/artifacts/image2.png",
                "/home/workdir/attachments/image2.png",
                "image2.png",
            ):
                try:
                    if os.path.isfile(p):
                        img = pygame.image.load(p).convert()
                        self.title_bg = img
                        self.title_bg_scaled = pygame.transform.smoothscale(img, (W, H))
                        bg = self.title_bg_scaled
                        break
                except Exception:
                    pass
        if bg is not None:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill((20, 40, 30))
            t = self.title_f.render("BRAIN TREK", True, C_GOLD)
            self.screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 40))
            s = self.small.render("Place image2.png in assets/images", True, (180, 190, 180))
            self.screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 + 20))
        # Hint
        tip = self.small.render("Start Exploration  ·  How to Play  ·  Customize   |   ENTER = start", True, (255, 255, 240))
        bar = pygame.Surface((tip.get_width() + 28, 30), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 140))
        self.screen.blit(bar, (W // 2 - tip.get_width() // 2 - 14, H - 48))
        self.screen.blit(tip, (W // 2 - tip.get_width() // 2, H - 42))

    def draw_howto(self, now):
        """Clean adventure-themed How to Play — sections, icons, green/cream/gold."""
        # Background
        self.screen.fill((16, 28, 22))
        for i in range(H):
            t = i / max(1, H)
            c = (int(18 + t * 8), int(32 + t * 12), int(24 + t * 6))
            pygame.draw.line(self.screen, c, (0, i), (W, i))
        # Soft mountain silhouettes
        pygame.draw.polygon(self.screen, (22, 42, 30), [
            (0, H), (0, 420), (180, 360), (320, 400), (480, 340), (640, 390),
            (820, 330), (980, 380), (W, 350), (W, H)
        ])
        pygame.draw.polygon(self.screen, (28, 52, 36), [
            (0, H), (120, 480), (300, 440), (500, 500), (700, 450), (900, 490), (W, 460), (W, H)
        ])

        cream = (245, 238, 220)
        gold = C_GOLD
        soft = (190, 200, 185)
        panel_bg = (28, 42, 34)
        panel_edge = (70, 100, 75)

        def mk(size, bold=False):
            try:
                return pygame.font.SysFont("Arial", size, bold=bold)
            except Exception:
                return self.small

        f_title = mk(40, True)
        f_sec = mk(16, True)
        f_key = mk(15, True)
        f_body = mk(14, False)
        f_tip = mk(13, False)

        # Title
        title = f_title.render("How to Play", True, gold)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 28))
        sub = f_tip.render("Brain Trek  ·  Highland Expedition Guide", True, soft)
        self.screen.blit(sub, (W // 2 - sub.get_width() // 2, 72))
        pygame.draw.line(self.screen, gold, (W // 2 - 120, 92), (W // 2 + 120, 92), 1)

        # Two-column panel layout
        left_x, right_x = 48, W // 2 + 16
        col_w = W // 2 - 64
        y0 = 108

        def section_panel(x, y, w, h, heading, icon_char):
            pygame.draw.rect(self.screen, panel_bg, (x, y, w, h), border_radius=12)
            pygame.draw.rect(self.screen, panel_edge, (x, y, w, h), 1, border_radius=12)
            # header bar
            pygame.draw.rect(self.screen, (36, 55, 42), (x + 4, y + 4, w - 8, 28), border_radius=8)
            # simple icon circle
            pygame.draw.circle(self.screen, (50, 80, 55), (x + 22, y + 18), 10)
            ic = f_key.render(icon_char, True, gold)
            self.screen.blit(ic, (x + 22 - ic.get_width() // 2, y + 18 - ic.get_height() // 2))
            ht = f_sec.render(heading, True, cream)
            self.screen.blit(ht, (x + 38, y + 10))
            return y + 38

        def row(x, y, key, desc, max_w):
            k = f_key.render(key, True, gold)
            self.screen.blit(k, (x + 16, y))
            d = f_body.render(desc, True, soft)
            self.screen.blit(d, (x + 16 + max(110, k.get_width() + 12), y))
            return y + 22

        # --- CONTROLS ---
        h = 200
        cy = section_panel(left_x, y0, col_w, h, "CONTROLS", "C")
        for key, desc in [
            ("WASD / Arrows", "Move your explorer"),
            ("Shift", "Run faster"),
            ("Space", "Dash (short cooldown)"),
            ("F", "Attack with staff (if owned)"),
            ("E", "Chests, forage, plant, landmarks"),
            ("C", "Talk to NPCs"),
            ("H", "Quiz hint (2 free, then shop)"),
            ("P / Esc", "Pause menu"),
        ]:
            cy = row(left_x, cy, key, desc, col_w)

        # --- LEVEL SELECTION ---
        y1 = y0 + h + 14
        h2 = 118
        cy = section_panel(left_x, y1, col_w, h2, "LEVEL SELECTION", "L")
        for key, desc in [
            ("Map nodes", "Click a level to select it"),
            ("START", "Opens the selected level"),
            ("Stars", "Earn up to 3 stars per level"),
            ("Unlocks", "Finish a level to open the next"),
        ]:
            cy = row(left_x, cy, key, desc, col_w)

        # --- MOVEMENT ---
        cy = section_panel(right_x, y0, col_w, 118, "MOVEMENT", "M")
        for key, desc in [
            ("Explore freely", "Paths, forests, rivers & bridges"),
            ("Stay on land", "Water slows or blocks travel"),
            ("Dash wisely", "Short burst — then a cooldown"),
            ("Shift run", "Cover ground faster when safe"),
        ]:
            cy = row(right_x, cy, key, desc, col_w)

        # --- QUESTIONS ---
        yq = y0 + 118 + 14
        cy = section_panel(right_x, yq, col_w, 118, "QUESTIONS", "?")
        for key, desc in [
            ("Treasure chests", "Hold quiz challenges"),
            ("Correct answer", "Opens the chest — earn gold"),
            ("Wrong answer", "Lose 1 life and some gold"),
            ("Hints (H)", "Remove a wrong option"),
        ]:
            cy = row(right_x, cy, key, desc, col_w)

        # --- OBJECTIVES (full width) ---
        yo = y1 + h2 + 14
        hw = W - 96
        cy = section_panel(left_x, yo, hw, 88, "OBJECTIVES", "O")
        goals = [
            "Explore each highland level and find the treasure chests.",
            "Answer quizzes, help NPCs, and survive enemies.",
            "Earn gold for the merchant shop, skins, and gear.",
        ]
        for g in goals:
            t = f_body.render("•  " + g, True, soft)
            self.screen.blit(t, (left_x + 18, cy))
            cy += 20

        # --- TIPS strip ---
        ty = yo + 88 + 12
        pygame.draw.rect(self.screen, (32, 48, 38), (left_x, ty, hw, 52), border_radius=10)
        pygame.draw.rect(self.screen, gold, (left_x, ty, hw, 52), 1, border_radius=10)
        tip_h = f_sec.render("TIPS", True, gold)
        self.screen.blit(tip_h, (left_x + 16, ty + 8))
        tips = "Select a level before START  ·  Save often from the pause menu  ·  Buy hints & gear at the Merchant  ·  Customize your hero anytime"
        tip_t = f_tip.render(tips, True, cream)
        self.screen.blit(tip_t, (left_x + 16, ty + 28))

        m = pygame.mouse.get_pos()
        self.howto_back = pygame.Rect(W // 2 - 120, H - 52, 240, 40)
        self.draw_button(self.howto_back, "BACK", m, base=(55, 85, 65))

    def draw_pause(self, now):
        o = pygame.Surface((W, H), pygame.SRCALPHA); o.fill((10,14,12,170)); self.screen.blit(o, (0, 0))
        p = self.title_f.render("PAUSED", True, C_TEXT)
        self.screen.blit(p, (W//2-p.get_width()//2, 130))
        m = pygame.mouse.get_pos()
        self.draw_button(self.p_resume, "RESUME", m)
        self.draw_button(self.p_shop, "MERCHANT SHOP", m, base=(110,80,40))
        self.draw_button(self.p_save, "SAVE PROGRESS", m, base=(50,80,110))
        self.draw_button(self.p_mute, "SOUND: OFF" if self.audio.muted else "SOUND: ON", m, base=(70,75,90))
        self.draw_button(self.p_custom, "CUSTOMIZE HERO", m, base=(120,75,40))
        self.draw_button(self.p_map, "LEVEL MAP", m, base=(60,90,110))
        inv = ", ".join(sorted(set(self.inventory))) if self.inventory else "empty"
        self.screen.blit(self.small.render("Inventory: " + inv, True, (180,180,170)), (W//2-160, 460))
        self.screen.blit(self.small.render("Gold (permanent): %d" % self.gold, True, C_GOLD), (W//2-160, 482))

    def _shop_icon_key(self, iid):
        """Map shop item id → draw_item_icon key (functionality unchanged)."""
        if iid.startswith("skin_"):
            return iid  # full skin id for color
        for suf in ("_scroll", "_nature", "_relic", "_gem", "_artifact", "_trade"):
            if iid.endswith(suf) or suf in iid:
                pass
        if iid.startswith("hint"):
            return "hint"
        if iid.startswith("charm"):
            return "charm"
        if iid.startswith("life"):
            return "life"
        if iid.startswith("staff"):
            return "staff"
        if iid.startswith("boots2"):
            return "boots2"
        if iid.startswith("boots"):
            return "boots"
        if iid.startswith("amulet"):
            return "amulet"
        if iid == "legend_boost":
            return "legend_boost"
        if iid == "bundle_hints":
            return "bundle_hints"
        return iid

    def draw_shop(self):
        """Polished highland merchant shop — Bhutanese / fantasy styling."""
        # Dim world behind
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((8, 12, 10, 220))
        self.screen.blit(o, (0, 0))

        # Main panel
        panel = pygame.Rect(90, 16, 920, 668)
        # Outer wood frame
        pygame.draw.rect(self.screen, (48, 34, 22), panel.inflate(10, 10), border_radius=18)
        pygame.draw.rect(self.screen, (28, 36, 30), panel, border_radius=16)
        # Gold + green border (dzong style)
        pygame.draw.rect(self.screen, (160, 120, 45), panel, 3, border_radius=16)
        pygame.draw.rect(self.screen, (55, 100, 65), panel.inflate(-8, -8), 2, border_radius=12)

        # Header banner
        hdr = pygame.Rect(panel.x + 20, panel.y + 14, panel.width - 40, 52)
        pygame.draw.rect(self.screen, (40, 28, 16), hdr, border_radius=10)
        pygame.draw.rect(self.screen, C_GOLD, hdr, 2, border_radius=10)
        # decorative corners
        for cx, cy in [(hdr.left + 10, hdr.top + 10), (hdr.right - 10, hdr.top + 10),
                       (hdr.left + 10, hdr.bottom - 10), (hdr.right - 10, hdr.bottom - 10)]:
            pygame.draw.circle(self.screen, C_GOLD, (cx, cy), 3)
        title = self.font.render("MERCHANT DAWA  ·  Highland Trader", True, C_GOLD)
        self.screen.blit(title, (hdr.centerx - title.get_width() // 2, hdr.y + 8))
        sub = self.small.render("Trade gold & finds for gear, charms, and traditional outfits", True, (190, 185, 160))
        self.screen.blit(sub, (hdr.centerx - sub.get_width() // 2, hdr.y + 30))

        # Wallet strip
        res = getattr(self, "resources", {k: 0 for k in RESOURCE_TYPES})
        wallet = pygame.Rect(panel.x + 20, panel.y + 76, panel.width - 40, 36)
        pygame.draw.rect(self.screen, (18, 24, 20), wallet, border_radius=8)
        pygame.draw.rect(self.screen, (70, 90, 70), wallet, 1, border_radius=8)
        # Gold pip
        pygame.draw.circle(self.screen, C_GOLD, (wallet.x + 18, wallet.centery), 8)
        pygame.draw.circle(self.screen, (255, 230, 140), (wallet.x + 16, wallet.centery - 2), 3)
        gtxt = self.font.render(str(self.gold), True, C_GOLD)
        self.screen.blit(gtxt, (wallet.x + 32, wallet.centery - gtxt.get_height() // 2))
        rx = wallet.x + 32 + gtxt.get_width() + 22
        for k, meta in RESOURCE_TYPES.items():
            n = int(res.get(k, 0))
            pygame.draw.circle(self.screen, meta["color"], (rx, wallet.centery), 6)
            pygame.draw.circle(self.screen, lighten(meta["color"], 40), (rx - 2, wallet.centery - 2), 2)
            lab = self.small.render("%s %d" % (meta["label"][:6], n), True, meta["color"])
            self.screen.blit(lab, (rx + 10, wallet.centery - lab.get_height() // 2))
            rx += lab.get_width() + 22

        # Item catalog (same ids / buy() mapping — UI only)
        catalog = [
            ("QUIZ AIDS", [
                ("hint", "Quiz Hint", "1200g", "1 bought hint for quizzes"),
                ("hint_scroll", "Hint (Scroll)", "400g + 1 Scroll", "Cheaper hint with a scroll"),
                ("bundle_hints", "Hint Bundle", "2 Scroll + 1 Gem", "+3 quiz hints"),
            ]),
            ("CHARMS & VITALITY", [
                ("charm", "River Charm", "1500g", "6s protection"),
                ("charm_nature", "Nature Charm", "500g + 2 Nature", "6s protection"),
                ("life", "Herbal Charm", "2500g", "+1 life"),
                ("life_relic", "Relic Tonic", "800g + 1 Relic", "+1 life"),
                ("boots", "Swift Boots", "1800g", "6s speed boost"),
            ]),
            ("GEAR", [
                ("staff", "Wooden Staff", "3500g", "Press F to swing"),
                ("staff_gem", "Gem Staff", "1500g + 3 Gems", "Press F to swing"),
                ("boots2", "Iron Boots", "4500g", "Permanent +10% speed"),
                ("boots2_gem", "Gem Boots", "2000g + 4 Gems", "Permanent +10% speed"),
                ("amulet", "Turquoise Amulet", "5500g", "+1 max life"),
                ("amulet_artifact", "Artifact Amulet", "2500g + 1 Art + 2 Gem", "+1 max life"),
            ]),
            ("LEGENDARY", [
                ("legend_boost", "Legendary Blessing", "1 Art + 3 Gem + 1 Relic", "Speed + shield burst"),
            ]),
            ("OUTFITS", []),  # filled below
        ]
        outfits = []
        for sid in ("red", "saffron", "green"):
            if sid not in self.skins_owned:
                outfits.append(("skin_" + sid, "Skin: %s" % SKINS[sid]["name"], "%dg" % SKINS[sid]["price"], "Gold only"))
                outfits.append(("skin_%s_trade" % sid, "Skin: %s (trade)" % SKINS[sid]["name"], "Trade finds", "Use relics & scrolls"))
            else:
                outfits.append(("skin_" + sid, "Skin: %s" % SKINS[sid]["name"], "Owned", "Click to wear"))
        catalog[-1] = ("OUTFITS", outfits)

        self.shop_rects = []
        self.shop_items = []
        m = pygame.mouse.get_pos()

        # Two-column card grid
        content_top = panel.y + 124
        content_bottom = panel.bottom - 64
        col_w = (panel.width - 56) // 2
        col_gap = 12
        left_x = panel.x + 22
        right_x = left_x + col_w + col_gap
        card_h = 52
        y = content_top
        col = 0  # 0 left, 1 right
        cat_color = (180, 150, 70)

        for cat_name, items in catalog:
            if not items:
                continue
            # Category header spans full width — force new row
            if col == 1:
                y += card_h + 8
                col = 0
            if y + 22 > content_bottom:
                break
            # header bar
            hx = left_x
            hw = panel.width - 44
            pygame.draw.rect(self.screen, (36, 48, 38), (hx, y, hw, 22), border_radius=6)
            pygame.draw.line(self.screen, cat_color, (hx + 8, y + 21), (hx + hw - 8, y + 21), 1)
            ct = self.small.render(cat_name, True, cat_color)
            self.screen.blit(ct, (hx + 12, y + 3))
            y += 28
            col = 0

            for iid, name, cost, desc in items:
                if y + card_h > content_bottom:
                    break
                cx = left_x if col == 0 else right_x
                r = pygame.Rect(cx, y, col_w, card_h - 4)
                self.shop_rects.append(r)
                self.shop_items.append(iid)
                hov = r.collidepoint(m)

                # Card body
                base = (42, 52, 46) if hov else (26, 34, 30)
                pygame.draw.rect(self.screen, base, r, border_radius=10)
                # Hover glow
                if hov:
                    glow = pygame.Surface((r.w + 8, r.h + 8), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (212, 172, 82, 45), (0, 0, r.w + 8, r.h + 8), border_radius=12)
                    self.screen.blit(glow, (r.x - 4, r.y - 4))
                    pygame.draw.rect(self.screen, C_GOLD, r, 2, border_radius=10)
                else:
                    pygame.draw.rect(self.screen, (70, 85, 70), r, 1, border_radius=10)

                # Icon plate
                ix, iy = r.x + 26, r.centery
                pygame.draw.circle(self.screen, (18, 24, 20), (ix, iy), 16)
                pygame.draw.circle(self.screen, (90, 110, 80) if not hov else C_GOLD, (ix, iy), 16, 1)
                self.draw_item_icon(self._shop_icon_key(iid), ix, iy, size=1.05)

                # Name + cost
                nm = self.small.render(name, True, C_TEXT if not hov else (255, 245, 210))
                self.screen.blit(nm, (r.x + 50, r.y + 8))
                cost_col = C_GOLD if "Owned" not in cost else C_GREEN_OK
                cs = self.small.render(cost, True, cost_col)
                self.screen.blit(cs, (r.x + 50, r.y + 26))
                # Description right side of card
                ds = self.small.render(desc, True, (150, 160, 145))
                # clip if needed
                max_dw = r.w - 60 - cs.get_width()
                if ds.get_width() < r.w - 58:
                    self.screen.blit(ds, (r.right - ds.get_width() - 12, r.y + 26))

                col = 1 - col
                if col == 0:
                    y += card_h + 6

            if col == 1:
                y += card_h + 6
                col = 0
            y += 4  # gap after category

        # Back button
        self.sh_back = pygame.Rect(panel.x + 24, panel.bottom - 52, 160, 40)
        self.draw_button(self.sh_back, "BACK", m, base=(60, 80, 70))
        tip = self.small.render("Click a card to buy  ·  Explore highlands for gems, scrolls, relics & artifacts", True, (140, 150, 140))
        self.screen.blit(tip, (self.sh_back.right + 20, self.sh_back.centery - tip.get_height() // 2))

    def draw_quiz(self, now):
        o = pygame.Surface((W, H), pygame.SRCALPHA); o.fill((10,12,14,225)); self.screen.blit(o, (0, 0))
        card = pygame.Rect(180, 50, 740, 600)
        pygame.draw.rect(self.screen, (24,28,26), card, border_radius=18)
        pygame.draw.rect(self.screen, (140,200,230), card, 3, border_radius=18)
        header = "TREASURE CHEST QUIZ - %s - streak x%d" % (self.quiz_subj.upper(), self.streak)
        self.screen.blit(self.small.render(header, True, (140,200,230)), (card.x+24, card.y+16))
        # optional subject image (right side, does not cover question/answers)
        img = getattr(self, "quiz_image", None)
        q_x = card.x + 24
        if img is not None:
            self.screen.blit(img, (card.right - 172, card.y + 38))
            pygame.draw.rect(self.screen, (120, 180, 160), (card.right - 172, card.y + 38, 160, 120), 2, border_radius=8)
        # question text — same readable size for all questions (word-wrap, never shrink to tiny)
        max_w = card.width - 220 if img is not None else card.width - 48
        q_font = self.font
        words = (self.quiz_question or "").split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if q_font.render(trial, True, C_TEXT).get_width() <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if not lines:
            lines = [self.quiz_question or ""]
        # Cap to 3 lines; if still overflowing, use slightly smaller but still readable font
        if len(lines) > 3:
            try:
                q_font = pygame.font.SysFont("Arial", max(18, self.font.get_height() - 4), bold=True)
            except Exception:
                q_font = self.font
            lines, cur = [], ""
            for w in words:
                trial = (cur + " " + w).strip()
                if q_font.render(trial, True, C_TEXT).get_width() <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
        qy = card.y + 44
        for line in lines[:4]:
            q_txt = q_font.render(line, True, C_TEXT)
            self.screen.blit(q_txt, (q_x, qy))
            qy += q_txt.get_height() + 2
        # Timer + answers sit below the question block (no overlap)
        body_y = max(qy + 10, card.y + 100)
        rem = max(0, 20 - (now - self.quiz_start)/1000)
        pygame.draw.rect(self.screen, (60,60,60), (card.x+24, body_y, 560, 12), border_radius=6)
        bar_col = C_GREEN_OK if rem > 8 else (C_GOLD if rem > 4 else C_RED_BAD)
        pygame.draw.rect(self.screen, bar_col, (card.x+24, body_y, int(560*rem/20), 12), border_radius=6)
        self.screen.blit(self.small.render("%ds" % int(rem + .999), True, C_TEXT), (card.x+590, body_y - 4))
        self.quiz_rects = []
        m = pygame.mouse.get_pos()
        letters = ["A", "B", "C", "D"]
        opt_top = body_y + 28
        # Fit 4 options in remaining card space
        opt_h = 64
        gap = 8
        for i, opt in enumerate(self.quiz_opts):
            r = pygame.Rect(card.x+24, opt_top + i * (opt_h + gap), 690, opt_h)
            self.quiz_rects.append(r)
            if i in self.hint_removed:
                pygame.draw.rect(self.screen, (26,28,34), r, border_radius=10)
                self.screen.blit(self.font.render("[ faded by hint ]", True, (90,95,105)), (r.x+24, r.centery-11))
                continue
            hov = r.collidepoint(m)
            pygame.draw.rect(self.screen, (50,58,80) if hov else (32,38,52), r, border_radius=10)
            pygame.draw.rect(self.screen, C_GOLD if hov else (90,90,90), r, 2, border_radius=10)
            self.screen.blit(self.font.render("%s.  %s" % (letters[i], opt), True, C_TEXT), (r.x+24, r.centery-11))
        self.screen.blit(self.small.render("Correct = open chest. Wrong = -1 life, -5 gold.", True, (150,160,150)), (card.x+24, card.y+560))
        if len(self.hint_removed) < 2:
            total_h = self.hints_available()
            if total_h > 0:
                h_txt = self.small.render(
                    "Press [H] for hint  |  free: %d  bought: %d" % (
                        getattr(self, "free_hints_left", 0), getattr(self, "hint_charges", 0)),
                    True, C_CYAN)
            else:
                h_txt = self.small.render("No hints left — buy Quiz Hint in the shop (1200g)", True, (200, 160, 120))
            self.screen.blit(h_txt, (card.x+24, card.y+530))
        if self.quiz_feedback_t > 0:
            fb_surf = pygame.Surface((card.width, 100), pygame.SRCALPHA)
            fb_surf.fill((20, 20, 20, 200))
            self.screen.blit(fb_surf, (card.x, card.y + 220))
            # Never display the correct answer text on wrong (or correct) feedback
            msg = self.feedback_msg or ""
            if "→" in msg or "->" in msg:
                msg = "WRONG!" if self.feedback_col == C_RED_BAD else "CORRECT!"
            # Strip accidental answer leak
            ans = getattr(self, "quiz_answer", None)
            if ans and ans in msg and self.feedback_col == C_RED_BAD:
                msg = "WRONG!"
            fb_txt = self.title_f.render(msg, True, self.feedback_col)
            self.screen.blit(fb_txt, (W//2 - fb_txt.get_width()//2, card.y + 245))

    def draw_level_done(self, now):
        self.draw_world(now)
        o = pygame.Surface((W, H), pygame.SRCALPHA); o.fill((10,14,12,215)); self.screen.blit(o, (0, 0))
        panel = pygame.Rect(W//2-280, 60, 560, 580)
        pygame.draw.rect(self.screen, (20, 28, 24), panel, border_radius=18)
        pygame.draw.rect(self.screen, C_GOLD, panel, 3, border_radius=18)
        t = self.title_f.render("LEVEL %d COMPLETE!" % self.current_level, True, C_GREEN_OK)
        self.screen.blit(t, (W//2-t.get_width()//2, 82))
        sub = self.small.render("Level %d - %s" % (self.current_level, BIOMES[self.biome]["name"]), True, (180,185,175))
        self.screen.blit(sub, (W//2-sub.get_width()//2, 140))
        stars = self.level_stars[self.current_level - 1]
        elapsed = now - self.done_t
        for i in range(3):
            if i < stars and elapsed > 500 + i * 450:
                pop = min(1.0, (elapsed - (500 + i * 450)) / 250)
                mstar(self.screen, W//2 - 70 + i*70, 190, int(26 * pop), M_YELLOW)
        if elapsed < 4000:
            rndc = random.Random(77)
            cols = [(235,90,110),(240,200,60),(120,200,255),(140,220,140)]
            for i in range(24):
                cx = panel.x + 40 + rndc.randint(0, panel.width-80)
                cy = panel.y + ((elapsed//10 + rndc.randint(0, 400)) % (panel.height-40))
                pygame.draw.rect(self.screen, cols[i % 4], (cx, cy, 4, 6))
        rows = [
            ("Lives remaining", "%d" % self.lives, C_TEXT),
            ("Treasures collected", "%d / %d" % (self.chests_opened, self.required_chests), C_GREEN_OK),
            ("Questions answered", "%d" % self.quiz_correct, C_GREEN_OK),
            ("Best streak", "x%d" % self.best_streak, C_GOLD),
            ("Wrong answers", "%d" % self.quiz_wrong, C_RED_BAD),
            ("Gold earned", "%d" % self.gold, C_GOLD),
            ("Completion bonus", "+%d gold" % self.reward_bonus, C_GOLD),
        ]
        for i, (k, v, c) in enumerate(rows):
            yy = 235 + i*30
            self.screen.blit(self.font.render(k, True, (180,190,180)), (panel.x+44, yy))
            vt = self.font.render(v, True, c)
            self.screen.blit(vt, (panel.right-44-vt.get_width(), yy))
        ay = 235 + len(rows)*30 + 6
        for i in self.ach_this_level[:3]:
            self.screen.blit(self.small.render("* " + ACH[i][0] + " - " + ACH[i][1], True, M_YELLOW), (panel.x+44, ay)); ay += 20
        self.screen.blit(self.small.render("Achievements: %d/%d" % (len(self.ach), len(ACH)), True, (180,180,170)), (panel.x+44, ay+4))
        m = pygame.mouse.get_pos()
        if self.current_level < NUM_LEVELS:
            self.draw_button(self.lc_next, "NEXT LEVEL - " + BIOMES[biome_for(self.current_level + 1)]["name"], m, base=(40,140,60))
        self.draw_button(self.lc_map, "BACK TO MAP", m, base=(60,90,110))
        self.draw_button(self.lc_retry, "REPLAY", m, base=(110,80,40))

    def draw_game_complete(self, now):
        self.draw_world(now)
        o = pygame.Surface((W, H), pygame.SRCALPHA); o.fill((10,14,12,230)); self.screen.blit(o, (0, 0))
        panel = pygame.Rect(W//2-300, 40, 600, 620)
        pygame.draw.rect(self.screen, (20, 28, 24), panel, border_radius=18)
        pygame.draw.rect(self.screen, C_GOLD, panel, 4, border_radius=18)
        t = self.title_f.render("BRAIN TREK COMPLETE!", True, M_YELLOW)
        self.screen.blit(t, (W//2-t.get_width()//2, 70))
        sub = self.small.render("You have conquered the highlands and mastered its secrets!", True, (180,185,175))
        self.screen.blit(sub, (W//2-sub.get_width()//2, 130))
        
        elapsed = now - self.done_t
        if elapsed < 6000:
            rndc = random.Random(99)
            cols = [(235,90,110),(240,200,60),(120,200,255),(140,220,140),(255,215,0)]
            for i in range(40):
                cx = panel.x + 40 + rndc.randint(0, panel.width-80)
                cy = panel.y + ((elapsed//8 + rndc.randint(0, 600)) % (panel.height-40))
                pygame.draw.rect(self.screen, cols[i % 5], (cx, cy, 5, 7))
                
        rows = [
            ("Total Gold", "%d" % self.gold, C_GOLD),
            ("Total Treasures", "%d" % self.total_chests, C_CYAN),
            ("Questions Correct", "%d" % self.total_correct, C_GREEN_OK),
            ("Secrets Found", "%d" % self.secret_chests_found, M_PURPLE),
            ("Levels Completed", "%d / %d" % (NUM_LEVELS, NUM_LEVELS), C_GREEN_OK),
            ("Achievements", "%d / %d" % (len(self.ach), len(ACH)), M_YELLOW),
        ]
        for i, (k, v, c) in enumerate(rows):
            yy = 180 + i*35
            self.screen.blit(self.font.render(k, True, (180,190,180)), (panel.x+60, yy))
            vt = self.font.render(v, True, c)
            self.screen.blit(vt, (panel.right-60-vt.get_width(), yy))
            
        m = pygame.mouse.get_pos()
        self.gc_cert = pygame.Rect(W//2-260, 500, 520, 46)
        self.gc_play = pygame.Rect(W//2-260, 560, 520, 46)
        self.draw_button(self.gc_cert, "GET CERTIFICATE", m, base=(40, 120, 160))
        self.draw_button(self.gc_play, "PLAY AGAIN", m, base=(40,140,60))

    def draw_cert_form(self, now):
        """Certificate details form — date & ID are assigned automatically (not editable)."""
        self.draw_world(now)
        o = pygame.Surface((W, H), pygame.SRCALPHA); o.fill((8, 12, 14, 235)); self.screen.blit(o, (0, 0))
        panel = pygame.Rect(W // 2 - 320, 70, 640, 560)
        pygame.draw.rect(self.screen, (22, 28, 26), panel, border_radius=16)
        pygame.draw.rect(self.screen, C_GOLD, panel, 3, border_radius=16)
        title = self.title_f.render("Certificate Form", True, C_GOLD)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 90))
        sub = self.small.render("Fill in your details. Date and Certificate ID are assigned automatically.", True, (190, 195, 185))
        self.screen.blit(sub, (W // 2 - sub.get_width() // 2, 145))

        fields = [
            ("name", "Full name", self.cert_name, "Your full name"),
            ("grade", "Grade / Class", self.cert_grade, "e.g. Grade 8 / Class A"),
            ("school", "School / Organization", self.cert_school, "School or organization"),
            ("country", "Country", self.cert_country, "Country"),
        ]
        self.cert_field_rects = {}
        m = pygame.mouse.get_pos()
        y0 = 185
        for i, (key, label, val, ph) in enumerate(fields):
            yy = y0 + i * 70
            lab = self.small.render(label, True, (180, 190, 180))
            self.screen.blit(lab, (panel.x + 40, yy))
            field = pygame.Rect(panel.x + 40, yy + 22, panel.width - 80, 38)
            self.cert_field_rects[key] = field
            focused = (getattr(self, "cert_focus", "name") == key)
            pygame.draw.rect(self.screen, (35, 42, 40), field, border_radius=8)
            border = C_GOLD if focused else (90, 95, 90)
            pygame.draw.rect(self.screen, border, field, 2, border_radius=8)
            shown = val if val else ph
            col = C_TEXT if val else (110, 115, 110)
            nt = self.font.render(shown[:48], True, col)
            self.screen.blit(nt, (field.x + 12, field.y + 8))
            if focused and (now // 500) % 2 == 0:
                cx = field.x + 12 + (self.font.render(val[:48], True, C_TEXT).get_width() if val else 0) + 2
                pygame.draw.line(self.screen, C_GOLD, (cx, field.y + 7), (cx, field.y + 31), 2)

        hint = self.small.render("Click a field to type  ·  Tab / Shift+Tab to move  ·  Enter submits when name is filled", True, (150, 155, 145))
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, 480))
        note = self.small.render("Date of completion & Certificate ID are generated automatically on submit.", True, (140, 160, 150))
        self.screen.blit(note, (W // 2 - note.get_width() // 2, 505))

        self.cert_submit_btn = pygame.Rect(W // 2 - 160, 530, 320, 48)
        self.cert_back_btn = pygame.Rect(W // 2 - 160, 585, 320, 42)
        can = bool(self.cert_name.strip())
        self.draw_button(self.cert_submit_btn, "SUBMIT", m, base=(40, 140, 90) if can else (60, 60, 60))
        self.draw_button(self.cert_back_btn, "BACK", m, base=(70, 80, 90))

    def _cert_field_order(self):
        return ["name", "grade", "school", "country"]

    def _cert_get_set(self, key, value=None):
        attr = {
            "name": "cert_name", "grade": "cert_grade", "school": "cert_school",
            "country": "cert_country",
        }[key]
        if value is None:
            return getattr(self, attr, "")
        setattr(self, attr, value)

    def _title_case_name(self, s):
        """Title-case each word: 'bikash dahal' → 'Bikash Dahal', 'bhutan' → 'Bhutan'."""
        if not s:
            return s
        out = []
        cap_next = True
        for ch in s:
            if ch.isspace() or ch in "-'/.":
                out.append(ch)
                cap_next = True
            elif cap_next and ch.isalpha():
                out.append(ch.upper())
                cap_next = False
            elif ch.isalpha():
                out.append(ch.lower())
            else:
                out.append(ch)
        return "".join(out)

    def _finalize_cert_fields(self):
        """Format player fields + assign date & certificate ID (not player-editable)."""
        import time as _time
        self.cert_name = self._title_case_name(self.cert_name.strip())
        self.cert_grade = self._title_case_name(self.cert_grade.strip())
        self.cert_school = self._title_case_name(self.cert_school.strip())
        self.cert_country = self._title_case_name(self.cert_country.strip())
        self.cert_date = _time.strftime("%d %b %Y")
        tag = "".join(c for c in self.cert_name.upper() if c.isalnum())[:4] or "BT"
        stamp = int(_time.time()) % 100000
        self.cert_id = "BT-%s-%05d" % (tag, stamp)

    def download_certificate(self):
        """Save the certificate document area as a PNG on the player's computer."""
        import time as _time
        try:
            frame = getattr(self, "_cert_frame", None)
            if frame:
                cx0, cy0, cw, ch = frame
                # Redraw once without UI buttons is already on screen; crop document
                rect = pygame.Rect(cx0, cy0, cw, ch)
                cert_surf = self.screen.subsurface(rect).copy()
            else:
                cert_surf = self.screen.copy()
            # Prefer Downloads folder, then Desktop, then home, then cwd
            home = os.path.expanduser("~")
            candidates = [
                os.path.join(home, "Downloads"),
                os.path.join(home, "Desktop"),
                home,
                os.getcwd(),
            ]
            folder = None
            for c in candidates:
                try:
                    if os.path.isdir(c) and os.access(c, os.W_OK):
                        folder = c
                        break
                except Exception:
                    continue
            if folder is None:
                folder = os.getcwd()
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (self.cert_name or "Explorer"))[:24]
            fname = "BrainTrek_Certificate_%s_%s.png" % (safe or "Explorer", _time.strftime("%Y%m%d_%H%M%S"))
            out = os.path.join(folder, fname)
            pygame.image.save(cert_surf, out)
            self.say("Certificate saved: %s" % out)
            self.audio.play("fanfare")
            return out
        except Exception as e:
            self.say("Could not save certificate. Try again.")
            try:
                self.audio.play("hurt")
            except Exception:
                pass
            return None

    def draw_certificate(self, now):
        """Official Brain Trek Certificate of Completion — polished document, not a menu."""
        self.screen.fill((8, 12, 10))

        margin = 16
        cw = W - margin * 2
        ch = H - margin * 2 - 44
        cx0 = margin
        cy0 = max(4, (H - ch - 44) // 2)

        # === Document frame ===
        pygame.draw.rect(self.screen, (25, 55, 35), (cx0 - 4, cy0 - 4, cw + 8, ch + 8), border_radius=8)
        parchment = (250, 243, 225)
        pygame.draw.rect(self.screen, parchment, (cx0, cy0, cw, ch), border_radius=6)
        # Fine paper lines
        for i in range(0, ch, 5):
            shade = 244 + (i * 2) % 4
            pygame.draw.line(self.screen, (shade, shade - 5, shade - 16),
                             (cx0 + 10, cy0 + i), (cx0 + cw - 10, cy0 + i), 1)
        # Double border (official certificate)
        pygame.draw.rect(self.screen, (160, 125, 50), (cx0 + 5, cy0 + 5, cw - 10, ch - 10), 2, border_radius=4)
        pygame.draw.rect(self.screen, (40, 90, 50), (cx0 + 10, cy0 + 10, cw - 20, ch - 20), 1, border_radius=3)
        # Corner ornaments
        for ox, oy in ((14, 14), (cw - 26, 14), (14, ch - 26), (cw - 26, ch - 26)):
            pygame.draw.polygon(self.screen, (160, 125, 50), [
                (cx0 + ox + 6, cy0 + oy), (cx0 + ox + 12, cy0 + oy + 6),
                (cx0 + ox + 6, cy0 + oy + 12), (cx0 + ox, cy0 + oy + 6)
            ])

        # Subtle Bhutanese adventure background (mountains + forest wash, low opacity)
        bg = pygame.Surface((cw - 24, ch - 24), pygame.SRCALPHA)
        # distant mountains
        pygame.draw.polygon(bg, (180, 200, 185, 35), [
            (0, int(ch * 0.55)), (int(cw * 0.15), int(ch * 0.35)), (int(cw * 0.28), int(ch * 0.50)),
            (int(cw * 0.45), int(ch * 0.30)), (int(cw * 0.62), int(ch * 0.48)),
            (int(cw * 0.78), int(ch * 0.32)), (cw, int(ch * 0.52)), (cw, ch), (0, ch)
        ])
        # soft forest band
        pygame.draw.ellipse(bg, (100, 140, 90, 28), (int(cw * 0.05), int(ch * 0.72), int(cw * 0.4), int(ch * 0.35)))
        pygame.draw.ellipse(bg, (90, 130, 85, 28), (int(cw * 0.5), int(ch * 0.70), int(cw * 0.45), int(ch * 0.38)))
        self.screen.blit(bg, (cx0 + 12, cy0 + 12))

        ink = (35, 55, 42)
        deep = (25, 85, 48)
        gold = (155, 120, 40)
        label_c = (70, 95, 75)
        muted = (105, 120, 105)
        cream = (255, 250, 238)

        def mkfont(size, bold=False):
            try:
                return pygame.font.SysFont("Georgia", max(10, int(size)), bold=bold)
            except Exception:
                try:
                    return pygame.font.SysFont("Arial", max(10, int(size)), bold=bold)
                except Exception:
                    return self.small

        def blit_c(s, f, col, x, y, center=False):
            img = f.render(str(s), True, col)
            rx = x - img.get_width() // 2 if center else x
            self.screen.blit(img, (rx, y))
            return img

        mid_x = cx0 + cw // 2
        pad = 48
        content_w = cw - pad * 2
        y = cy0 + int(ch * 0.035)

        f_brand = mkfont(ch * 0.044, True)
        f_tag = mkfont(ch * 0.014, False)
        f_head = mkfont(ch * 0.032, True)
        f_sub = mkfont(ch * 0.015, False)
        f_name = mkfont(ch * 0.042, True)
        f_body = mkfont(ch * 0.018, False)
        f_label = mkfont(ch * 0.014, True)
        f_val = mkfont(ch * 0.022, True)
        f_tiny = mkfont(ch * 0.014, False)

        # Top-left logo (image5.png) — small badge; reload if missing
        logo = getattr(self, "cert_logo", None)
        if logo is None:
            for _lp in (
                os.path.join(IMAGE_DIR, "image5.png"),
                os.path.join(IMAGE_DIR, "image5.jpg"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ".", "image5.png"),
                os.path.join(os.getcwd(), "image5.png"),
                os.path.join(os.getcwd(), "image5.jpg"),
                "/home/workdir/artifacts/image5.png",
                "/home/workdir/attachments/image5.png",
                "image5.png",
                "image5.jpg",
            ):
                try:
                    if os.path.isfile(_lp):
                        logo = pygame.image.load(_lp).convert_alpha()
                        self.cert_logo = logo
                        break
                except Exception:
                    pass
        logo_h = 0
        if logo is not None:
            max_lw = max(70, int(ch * 0.15))
            max_lh = max(70, int(ch * 0.15))
            lw, lh = logo.get_width(), logo.get_height()
            sc = min(max_lw / float(max(1, lw)), max_lh / float(max(1, lh)), 1.0)
            nw, nh = max(1, int(lw * sc)), max(1, int(lh * sc))
            try:
                logo_s = pygame.transform.smoothscale(logo, (nw, nh))
            except Exception:
                logo_s = pygame.transform.scale(logo, (nw, nh))
            self.screen.blit(logo_s, (cx0 + pad, cy0 + int(ch * 0.032)))
            logo_h = nh

        # Top-right medal
        medal_r = max(22, int(min(ch * 0.055, 32)))
        medal_cx = cx0 + cw - pad - medal_r - 6
        medal_cy = cy0 + int(ch * 0.055) + medal_r
        pygame.draw.circle(self.screen, (120, 90, 30), (medal_cx, medal_cy), medal_r + 3)
        pygame.draw.circle(self.screen, (210, 175, 65), (medal_cx, medal_cy), medal_r)
        pygame.draw.circle(self.screen, (230, 200, 90), (medal_cx, medal_cy), medal_r - 3)
        pygame.draw.circle(self.screen, (140, 105, 35), (medal_cx, medal_cy), medal_r - 5, 2)
        pygame.draw.polygon(self.screen, (50, 100, 55), [
            (medal_cx - 10, medal_cy + 4), (medal_cx, medal_cy - 10), (medal_cx + 10, medal_cy + 4)
        ])
        rbn = medal_cy + medal_r - 1
        pygame.draw.polygon(self.screen, deep, [
            (medal_cx - 11, rbn), (medal_cx - 4, rbn + 12), (medal_cx, rbn + 5),
            (medal_cx + 4, rbn + 12), (medal_cx + 11, rbn)
        ])

        # Center title block (between logo and medal)
        y = cy0 + int(ch * 0.040)
        brand = blit_c("BRAIN TREK", f_brand, deep, mid_x, y, center=True)
        y += brand.get_height() + 4
        tag = blit_c("EXPLORE  ·  LEARN  ·  PROTECT", f_tag, gold, mid_x, y, center=True)
        y += tag.get_height() + 10
        # elegant divider
        pygame.draw.line(self.screen, gold, (cx0 + pad + 20, y), (mid_x - 14, y), 1)
        pygame.draw.line(self.screen, gold, (mid_x + 14, y), (cx0 + cw - pad - 20, y), 1)
        pygame.draw.circle(self.screen, gold, (mid_x, y), 3)
        y += 14

        head = blit_c("CERTIFICATE OF COMPLETION", f_head, deep, mid_x, y, center=True)
        y += head.get_height() + 6
        y += 6

        # Player fields — already title-cased in _finalize_cert_fields
        name = (self.cert_name or "Explorer").strip()
        grade = (self.cert_grade or "").strip() or "—"
        school = (self.cert_school or "").strip() or "—"
        country = (self.cert_country or "").strip() or "—"
        date = (self.cert_date or "").strip() or "—"
        cid = (self.cert_id or "").strip() or "—"

        y += 8

        for line in (
            "for successfully completing all levels of Brain Trek and",
            "demonstrating outstanding knowledge, exploration,",
            "problem-solving and environmental responsibility.",
        ):
            blit_c(line, f_body, ink, mid_x, y, center=True)
            y += int(ch * 0.026)
        y += int(ch * 0.028)

        # Detail grid
        col_gap = 28
        col_w = (content_w - col_gap) // 2
        left_x = cx0 + pad
        right_x = left_x + col_w + col_gap
        box_h = max(28, int(ch * 0.038))

        def detail(x, yy, w, label, value):
            blit_c(label, f_label, label_c, x, yy)
            by = yy + int(ch * 0.015)
            pygame.draw.line(self.screen, (170, 150, 110), (x, by + box_h - 2), (x + w, by + box_h - 2), 1)
            fs = max(12, int(ch * 0.022))
            val = value
            while fs >= 11:
                f = mkfont(fs, True)
                s = f.render(val, True, ink)
                if s.get_width() <= w - 4:
                    break
                fs -= 1
            else:
                s = f_val.render(val[:40], True, ink)
            self.screen.blit(s, (x + 2, by + 4))
            return by + box_h

        detail(left_x, y, col_w, "FULL NAME", name)
        detail(right_x, y, col_w, "GRADE / CLASS", grade)
        y += int(ch * 0.072)
        bottom = detail(left_x, y, col_w, "SCHOOL / ORGANIZATION", school)
        detail(right_x, y, col_w, "COUNTRY", country)
        y = bottom + int(ch * 0.050)

        # Date | seal | ID
        seal_r = max(26, int(min(ch * 0.058, 34)))
        side_w = int(content_w * 0.28)
        date_x = left_x
        id_x = left_x + side_w + (content_w - side_w * 2)
        seal_cx = mid_x

        blit_c("DATE OF COMPLETION", f_label, label_c, date_x + side_w // 2, y, center=True)
        blit_c(date, f_val, ink, date_x + side_w // 2, y + int(ch * 0.018), center=True)
        line_y = y + int(ch * 0.042)
        pygame.draw.line(self.screen, (80, 110, 90), (date_x, line_y), (date_x + side_w - 10, line_y), 2)

        blit_c("CERTIFICATE ID", f_label, label_c, id_x + side_w // 2, y, center=True)
        blit_c(cid, f_val, ink, id_x + side_w // 2, y + int(ch * 0.018), center=True)
        pygame.draw.line(self.screen, (80, 110, 90), (id_x + 10, line_y), (id_x + side_w, line_y), 2)

        # Signatures anchored toward bottom so the page is balanced
        fy = max(line_y + int(ch * 0.055), cy0 + ch - int(ch * 0.20))
        fy = min(fy, cy0 + ch - int(ch * 0.14))
        pygame.draw.line(self.screen, gold, (cx0 + pad, fy), (cx0 + cw - pad, fy), 1)
        fy += 8

        def blit_sig(sig, x, y, max_w, max_h):
            if sig is None:
                return 0
            sw, sh = sig.get_width(), sig.get_height()
            sc = min(max_w / float(max(1, sw)), max_h / float(max(1, sh)), 1.0)
            nw, nh = max(1, int(sw * sc)), max(1, int(sh * sc))
            try:
                s = pygame.transform.smoothscale(sig, (nw, nh))
            except Exception:
                s = pygame.transform.scale(sig, (nw, nh))
            self.screen.blit(s, (x, y))
            return nh

        sig_w = int(content_w * 0.22)
        sig_hmax = int(ch * 0.11)

        # Game Creator — image.png
        left_fx = cx0 + pad
        sh = blit_sig(getattr(self, "cert_signature", None), left_fx, fy, sig_w, sig_hmax)
        if sh == 0:
            pygame.draw.line(self.screen, (120, 110, 90), (left_fx, fy + 32), (left_fx + 100, fy + 32), 1)
            sh = 32
        else:
            pygame.draw.line(self.screen, (120, 110, 90), (left_fx, fy + sh + 2), (left_fx + max(90, sig_w - 10), fy + sh + 2), 1)
        blit_c("GAME CREATOR", f_label, label_c, left_fx, fy + sh + 6)
        blit_c("Brain Trek Team", f_tiny, ink, left_fx, fy + sh + 20)

        # Adventure Guide — image4.png
        right_fx = cx0 + cw - pad - sig_w
        gh = blit_sig(getattr(self, "cert_guide_signature", None), right_fx, fy, sig_w, sig_hmax)
        if gh == 0:
            pygame.draw.line(self.screen, (120, 110, 90), (right_fx, fy + 32), (right_fx + 100, fy + 32), 1)
            gh = 32
        else:
            pygame.draw.line(self.screen, (120, 110, 90), (right_fx, fy + gh + 2), (right_fx + max(90, sig_w - 10), fy + gh + 2), 1)
        blit_c("ADVENTURE GUIDE", f_label, label_c, right_fx, fy + gh + 6)
        blit_c("Keep Exploring!", f_tiny, ink, right_fx, fy + gh + 20)

        blit_c("Discover Bhutan. Grow Your Mind. Protect Our Future.", f_tiny, gold, mid_x, fy + 8, center=True)

        # UI chrome below document — not part of the saved certificate image
        m = pygame.mouse.get_pos()
        self.cert_done_btn = pygame.Rect(W // 2 - 310, H - 42, 200, 34)
        self.cert_download_btn = pygame.Rect(W // 2 - 90, H - 42, 200, 34)
        self.draw_button(self.cert_done_btn, "CONTINUE", m, base=(40, 130, 60))
        self.draw_button(self.cert_download_btn, "DOWNLOAD", m, base=(50, 90, 130))
        # Store certificate frame for download crop
        self._cert_frame = (cx0, cy0, cw, ch)

    def draw_end(self, now):
        self.draw_world(now)
        o = pygame.Surface((W, H), pygame.SRCALPHA); o.fill((10,14,12,205)); self.screen.blit(o, (0, 0))
        panel = pygame.Rect(W//2-240, 150, 480, 360)
        pygame.draw.rect(self.screen, (22, 26, 24), panel, border_radius=18)
        pygame.draw.rect(self.screen, C_RED_BAD, panel, 3, border_radius=18)
        t = self.title_f.render("OUT OF LIVES", True, C_RED_BAD)
        self.screen.blit(t, (W//2-t.get_width()//2, 185))
        sub = self.small.render("The highlands rest... but every mistake taught you something.", True, (190,190,180))
        self.screen.blit(sub, (W//2-sub.get_width()//2, 250))
        if self.last_quiz:
            ft = self.small.render("Last fact: " + self.last_quiz[1], True, C_CYAN)
            self.screen.blit(ft, (W//2-ft.get_width()//2, 290))
        rows = [("Gold", "%d" % self.gold, C_GOLD), ("Treasures", "%d/%d" % (self.chests_opened, self.required_chests), C_CYAN)]
        for i, (k, v, c) in enumerate(rows):
            yy = 330 + i*30
            self.screen.blit(self.font.render(k, True, (180,185,175)), (panel.x+40, yy))
            vt = self.font.render(v, True, c)
            self.screen.blit(vt, (panel.right-40-vt.get_width(), yy))
        s2 = self.small.render("Click or ENTER to return to the map", True, (170,170,160))
        self.screen.blit(s2, (W//2-s2.get_width()//2, 470))

    def run(self):
        while True:
            dt = min(.05, self.clock.tick(FPS)/1000)
            now = pygame.time.get_ticks()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_F11:
                        try: pygame.display.toggle_fullscreen()
                        except Exception: pass
                    # Mute with U
                    elif ev.key == pygame.K_u: self.audio.mute()
                    # --- Cinematic Intro skip ---
                    if self.state == "INTRO" and ev.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        self._finish_intro()
                    elif self.state == "TITLE" and ev.key == pygame.K_RETURN: self.state = "MAP"
                    elif self.state in ("LEVEL_DONE", "OVER") and ev.key == pygame.K_RETURN: 
                        if self.state == "LEVEL_DONE" and self.current_level < NUM_LEVELS:
                            self.start_level(self.current_level + 1)
                        else:
                            self.state = "MAP"
                    elif self.state == "GAME_COMPLETE" and ev.key == pygame.K_RETURN:
                        self.state = "CERT_FORM"
                    elif self.state == "CERT_FORM":
                        order = self._cert_field_order()
                        focus = getattr(self, "cert_focus", "name")
                        if focus not in order:
                            focus = "name"
                            self.cert_focus = focus
                        if ev.key == pygame.K_RETURN:
                            if self.cert_name.strip():
                                self._finalize_cert_fields()
                                self.cert_submitted = True
                                self.state = "CERTIFICATE"
                                self.audio.play("fanfare")
                        elif ev.key == pygame.K_ESCAPE:
                            self.state = "GAME_COMPLETE"
                        elif ev.key == pygame.K_TAB:
                            mods = pygame.key.get_mods()
                            if mods & pygame.KMOD_SHIFT:
                                self.cert_focus = order[(order.index(focus) - 1) % len(order)]
                            else:
                                self.cert_focus = order[(order.index(focus) + 1) % len(order)]
                        elif ev.key == pygame.K_BACKSPACE:
                            cur = self._cert_get_set(focus)
                            self._cert_get_set(focus, cur[:-1])
                        else:
                            ch = ev.unicode if hasattr(ev, "unicode") else ""
                            if ch and ch.isprintable() and len(self._cert_get_set(focus)) < 48:
                                cur = self._cert_get_set(focus) + ch
                                # Auto-capitalize each word of the full name as the player types
                                if focus == "name":
                                    cur = self._title_case_name(cur)
                                self._cert_get_set(focus, cur)
                    elif self.state == "CERTIFICATE" and ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                        self.state = "MAP"
                    elif self.state == "PLAY":
                        if self.dialog is not None:
                            if ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE, pygame.K_c):
                                self.advance_dialog()
                        else:
                            if ev.key in (pygame.K_ESCAPE, pygame.K_p): self.state = "PAUSE"
                            elif ev.key == pygame.K_e and self.interact: self.do_interact()
                            elif ev.key == pygame.K_c and self.near_npc is not None:
                                # Talk to NPC with C
                                self.interact = ("talk", self.near_npc)
                                self.do_interact()
                            elif ev.key == pygame.K_f: self.try_attack()
                            elif ev.key == pygame.K_h:
                                self.reveal_hint()
                    elif self.state == "QUIZ":
                        if ev.key == pygame.K_h and self.quiz_feedback_t == 0:
                            self.use_quiz_hint()
                    elif self.state == "PAUSE" and ev.key in (pygame.K_ESCAPE, pygame.K_p): self.state = "PLAY"
                    elif self.state == "SHOP" and ev.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.state = getattr(self, "shop_from", "PAUSE")
                    elif self.state == "CUSTOMIZE" and ev.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.state = getattr(self, "customize_from", "MAP")
                    elif self.state == "HOWTO" and ev.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN):
                        self.state = "TITLE"
                    elif self.state == "MAP" and ev.key == pygame.K_ESCAPE: self.state = "TITLE"
                    
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 2, 3):
                    m = ev.pos
                    # --- Intro skip (any click) ---
                    if self.state == "INTRO":
                        self._finish_intro()
                        continue
                    elif self.state == "TITLE":
                        # Exact mapping to painted buttons
                        if self.title_play.collidepoint(m):
                            self.state = "MAP"
                            self.audio.play("click")
                            try:
                                self.audio.update_for_state("MAP")
                            except Exception:
                                pass
                        elif self.title_howto.collidepoint(m):
                            self.state = "HOWTO"
                            self.audio.play("click")
                        elif self.title_custom.collidepoint(m):
                            self.customize_from = "TITLE"
                            self.state = "CUSTOMIZE"
                            self.audio.play("click")
                    elif self.state == "HOWTO":
                        if getattr(self, "howto_back", None) and self.howto_back.collidepoint(m):
                            self.state = "TITLE"
                            self.audio.play("click")
                    elif self.state == "MAP":
                        if self.map_shop.collidepoint(m):
                            self.shop_from = "MAP"
                            self.state = "SHOP"
                            self.audio.play("click")
                        elif getattr(self, "map_start_btn", None) and self.map_start_btn.collidepoint(m):
                            sel = getattr(self, "map_selected_level", None)
                            if sel is not None and 1 <= sel <= NUM_LEVELS and self.level_unlocked[sel - 1]:
                                self.start_level(sel)
                                self.audio.play("click")
                            else:
                                self.audio.play("hurt")
                                self.say("Select a level first, then press START.")
                        else:
                            # Select level only — does not start until START is pressed
                            mx, my = m
                            picked = None
                            for lvl in range(1, NUM_LEVELS + 1):
                                x, y = level_positions[lvl - 1]
                                if math.hypot(mx - x, my - y) <= 40:
                                    picked = lvl
                                    break
                            if picked is not None:
                                if self.level_unlocked[picked - 1]:
                                    self.map_selected_level = picked
                                    self.audio.play("click")
                                    self.say("Level %d selected — press START." % picked)
                                else:
                                    self.audio.play("hurt")
                                    self.say_locked = now
                    elif self.state == "LEVEL_DONE":
                        if self.current_level < NUM_LEVELS and self.lc_next.collidepoint(m):
                            self.start_level(self.current_level + 1)
                        elif self.lc_map.collidepoint(m): self.state = "MAP"
                        elif self.lc_retry.collidepoint(m): self.start_level(self.current_level)
                    elif self.state == "GAME_COMPLETE":
                        if getattr(self, "gc_cert", pygame.Rect(0,0,0,0)).collidepoint(m):
                            self.state = "CERT_FORM"
                            self.audio.play("click")
                        elif self.gc_play.collidepoint(m):
                            self.level_stars = [0] * NUM_LEVELS
                            self.level_unlocked = [False] * NUM_LEVELS
                            self.level_unlocked[0] = True
                            self.current_level = 1
                            self.state = "MAP"
                    elif self.state == "CERT_FORM":
                        for key, rect in getattr(self, "cert_field_rects", {}).items():
                            if rect.collidepoint(m):
                                self.cert_focus = key
                                self.audio.play("click")
                                break
                        else:
                            if getattr(self, "cert_submit_btn", pygame.Rect(0,0,0,0)).collidepoint(m):
                                if self.cert_name.strip():
                                    self._finalize_cert_fields()
                                    self.cert_submitted = True
                                    self.state = "CERTIFICATE"
                                    self.audio.play("fanfare")
                            elif getattr(self, "cert_back_btn", pygame.Rect(0,0,0,0)).collidepoint(m):
                                self.state = "GAME_COMPLETE"
                    elif self.state == "CERTIFICATE":
                        if getattr(self, "cert_download_btn", pygame.Rect(0,0,0,0)).collidepoint(m):
                            self.download_certificate()
                            self.audio.play("click")
                        elif getattr(self, "cert_done_btn", pygame.Rect(0,0,0,0)).collidepoint(m):
                            self.state = "MAP"
                    elif self.state == "OVER": self.state = "MAP"
                    elif self.state == "PAUSE":
                        if self.p_resume.collidepoint(m): self.state = "PLAY"
                        elif self.p_shop.collidepoint(m):
                            self.shop_from = "PAUSE"
                            self.state = "SHOP"
                        elif self.p_save.collidepoint(m): self.save_progress()
                        elif self.p_mute.collidepoint(m): self.audio.mute()
                        elif getattr(self, "p_custom", None) and self.p_custom.collidepoint(m):
                            self.customize_from = "PAUSE"
                            self.state = "CUSTOMIZE"
                            self.audio.play("click")
                        elif self.p_map.collidepoint(m): self.state = "MAP"
                    elif self.state == "SHOP":
                        if self.sh_back.collidepoint(m):
                            self.state = getattr(self, "shop_from", "PAUSE")
                            self.audio.play("click")
                        else:
                            for i, r in enumerate(self.shop_rects):
                                if r.collidepoint(m): self.buy(self.shop_items[i]); break
                    elif self.state == "QUIZ":
                        if self.quiz_feedback_t == 0:
                            for i, r in enumerate(self.quiz_rects):
                                if r.collidepoint(m) and i not in self.hint_removed:
                                    self.resolve_quiz(i); break
                        elif now > self.quiz_feedback_t:
                            if self.chests_left() == 0:
                                self.complete_level()
                            else:
                                self.state = "PLAY"
                                self.active_chest = None
                    elif self.state == "CUSTOMIZE":
                        if hasattr(self, "custom_back_r") and self.custom_back_r.collidepoint(m):
                            self.state = getattr(self, "customize_from", "MAP")
                            self.audio.play("click")
                        elif hasattr(self, "custom_male_r") and self.custom_male_r.collidepoint(m):
                            self.gender = "male"
                            self.audio.play("click")
                            self.save_progress()
                        elif hasattr(self, "custom_female_r") and self.custom_female_r.collidepoint(m):
                            self.gender = "female"
                            self.audio.play("click")
                            self.save_progress()
                        elif hasattr(self, "custom_skin_rects"):
                            for r, sid in self.custom_skin_rects:
                                if r.collidepoint(m) and sid in self.skins_owned:
                                    self.skin = sid
                                    self.audio.play("click")
                                    break
                            
            if self.state == "PLAY":
                self.update_play(now, dt)
                self.draw_world(now)
                self.draw_ui(now)
                if self.dialog is not None: self.draw_dialog()
                el = now - self.fade_t
                if el < 700:
                    f = pygame.Surface((W, H)); f.fill((0, 0, 0)); f.set_alpha(int(255 * (1 - el/700)))
                    self.screen.blit(f, (0, 0))
            elif self.state == "PAUSE":
                self.draw_world(now); self.draw_pause(now)
            elif self.state == "SHOP":
                self.draw_world(now); self.draw_shop()
            elif self.state == "QUIZ":
                self.draw_world(now)
                self.draw_quiz(now)
                if self.quiz_feedback_t > 0 and now > self.quiz_feedback_t:
                    if self.chests_left() == 0:
                        self.complete_level()
                    else:
                        self.state = "PLAY"
                        self.active_chest = None
            elif self.state == "CUSTOMIZE":
                self.draw_customize(now)
            elif self.state == "INTRO":
                self.draw_intro(now)
            elif self.state == "TITLE":
                self.draw_title(now)
            elif self.state == "HOWTO":
                self.draw_howto(now)
            elif self.state == "MAP":
                self.draw_map()
                if hasattr(self, "say_locked") and now - self.say_locked < 1800:
                    t = self.small.render("Finish the current level first!", True, (255,200,120))
                    self.screen.blit(t, (W//2-t.get_width()//2, MAP_H-55))
            elif self.state == "LEVEL_DONE":
                self.draw_level_done(now)
            elif self.state == "GAME_COMPLETE":
                self.draw_game_complete(now)
            elif self.state == "CERT_FORM":
                self.draw_cert_form(now)
            elif self.state == "CERTIFICATE":
                self.draw_certificate(now)
            else:
                self.draw_end(now)
            try:
                self.audio.update_for_state(self.state)
            except Exception:
                pass
            pygame.display.flip()

if __name__ == "__main__":
    Game().run()
