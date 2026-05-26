import pygame
import sys
import random
import math
import json
import os

# --- Window & Map Configurations ---
WIDTH = 1000
HEIGHT = 700
WORLD_SIZE = 2400  
FPS = 60
SAVE_FILE = "braintrek_save.json"

# --- Advanced Color Palette Overhaul ---
C_GOLD = (245, 185, 35)
C_RED = (240, 60, 60)
C_WHITE = (255, 255, 255)
C_YELLOW = (255, 240, 50)
C_DARK = (15, 18, 28)
C_GRAY = (75, 82, 98)
C_LIGHT_GRAY = (180, 185, 195)
C_GREEN = (38, 165, 78)
C_SHADOW = (10, 12, 20, 70)
C_ORANGE = (255, 120, 25)  
C_BIRD = (20, 22, 30)
C_PURPLE = (150, 50, 220)
C_CYAN = (40, 210, 230)

# Environment & Atmosphere Colors
C_RIVER_DEEP = (10, 50, 125)
C_RIVER_MID = (20, 95, 175)
C_RIVER_LIGHT = (55, 155, 205)
C_WATER_FOAM = (215, 245, 255)
C_SKY_BLUE = (135, 205, 240)
C_CLOUD = (255, 255, 255, 170)

# Multi-Tone Mountain Palette
C_MNT_FAR = (40, 48, 66)         
C_MNT_DARK = (55, 68, 85)        
C_MNT_LIGHT = (90, 102, 122)     
C_MNT_SNOW = (245, 248, 252)     

# Structural & Floral Elements
C_BAZAM_WOOD = (85, 45, 20)      
C_BAZAM_GOLD = (230, 170, 40)     
C_BAZAM_STONE = (95, 95, 100)   
C_GHO_MAROON = (125, 15, 25)  
C_LAGAY_WHITE = (245, 245, 245) 
C_BIRCH_TRUNK = (242, 242, 238)   
C_BIRCH_LEAVES = (235, 175, 20)   
C_GRASS_DETAIL = (32, 145, 60)

# --- Expanded Level Quiz Database (1-20 Scales) ---
LEVEL_DATA = {
    1: {"subj": "Science", "q": "Which gas do trees release?", "a": "oxygen", "options": ["oxygen", "carbon dioxide", "nitrogen", "hydrogen"]},
    2: {"subj": "Mathematics", "q": "What is 8 * 5?", "a": "40", "options": ["40", "35", "45", "13"]},
    3: {"subj": "History", "q": "Who was the first king of Bhutan?", "a": "ugyen wangchuck", "options": ["ugyen wangchuck", "jigme wangchuck", "jigme singye wangchuck", "jigme khesar namgyel wangchuck"]},
    4: {"subj": "Economics", "q": "If you have 50 gold and spend 20, how much remains?", "a": "30", "options": ["30", "20", "50", "70"]},
    5: {"subj": "Science", "q": "What is the role of decomposers in an ecosystem?", "a": "break down dead organisms", "options": ["break down dead organisms", "produce oxygen", "hunt predators", "create soil"]},
    6: {"subj": "Mathematics", "q": "Solve: (12 + 8) / 4", "a": "5", "options": ["5", "4", "6", "8"]},
    7: {"subj": "History", "q": "In which year was Bhutan's Constitution adopted?", "a": "2008", "options": ["2008", "2005", "2010", "1999"]},
    8: {"subj": "Economics", "q": "What happens when demand increases but supply stays same?", "a": "price increases", "options": ["price increases", "price decreases", "supply increases", "market crashes"]},
    9: {"subj": "Science/Logic", "q": "Why are forests important for biodiversity?", "a": "they provide habitat/support many species", "options": ["they provide habitat/support many species", "they produce wood", "they look beautiful", "they prevent floods"]},
    10: {"subj": "Mixed Challenge", "q": "What is 2008 + 5 * 2?", "a": "2018", "options": ["2018", "2026", "4016", "2010"]},
    # Harder Tier Extension Levels
    11: {"subj": "Quantum Physics", "q": "What subatomic particles compose a proton?", "a": "two ups and one down quark", "options": ["two ups and one down quark", "two downs and one up quark", "three electron neutrinos", "four gluons"]},
    12: {"subj": "Advanced Calculus", "q": "What is the derivative of sin(x^2)?", "a": "2x * cos(x^2)", "options": ["2x * cos(x^2)", "cos(2x)", "-2x * sin(x)", "2 * sin(x)cos(x)"]},
    13: {"subj": "World Geography", "q": "Which landlocked country is entirely surrounded by South Africa?", "a": "lesotho", "options": ["lesotho", "swaziland", "botswana", "namibia"]},
    14: {"subj": "Organic Chemistry", "q": "What type of bonds characterize alkynes?", "a": "triple covalent bonds", "options": ["triple covalent bonds", "double covalent bonds", "single ionic bonds", "hydrogen bonds"]},
    15: {"subj": "Macroeconomics", "q": "What index gauges inflation by sampling a basket of consumer products?", "a": "cpi", "options": ["cpi", "gdp deflator", "ppi", "nasdaq"]},
    16: {"subj": "Computer Science", "q": "What is the average time complexity of quicksort?", "a": "O(n log n)", "options": ["O(n log n)", "O(n^2)", "O(n)", "O(log n)"]},
    17: {"subj": "Astronomy", "q": "What is the approximate age of the universe in billions of years?", "a": "13.8", "options": ["13.8", "4.5", "9.3", "20.1"]},
    18: {"subj": "Microbiology", "q": "Which organelle is responsible for cellular respiration?", "a": "mitochondria", "options": ["mitochondria", "ribosome", "golgi apparatus", "lysosome"]},
    19: {"subj": "Philosophy/Logic", "q": "Who coined the phrase 'Cogito, ergo sum'?", "a": "rene descartes", "options": ["rene descartes", "john locke", "immanuel kant", "socrates"]},
    20: {"subj": "Grand Finale", "q": "Complete the sequence: 1, 1, 2, 3, 5, 8, 13, ...", "a": "21", "options": ["21", "20", "25", "19"]}
}

class UltimateBrainTrekEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Brain Trek: Master Grandmaster Edition")
        self.clock = pygame.time.Clock()
        
        # Typography Systems
        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.btn_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 42, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 16, bold=True)
        
        # Difficult Matrix Configuration
        self.modes = {
            1: {"name": "Casual Mode", "desc": "10 Lives Available", "lives": 10, "card": (22, 60, 36)},
            2: {"name": "Scholar Mode", "desc": "5 Lives Available", "lives": 5, "card": (68, 60, 52)},
            3: {"name": "Survival Mode", "desc": "1 Life Challenge", "lives": 1, "card": (75, 32, 85)}
        }
        
        # Core States
        self.state = "HOME_MENU"
        self.player_name = ""
        self.gold = 0
        self.current_level = 1
        self.lives = 5
        self.selected_mode = 1
        self.feedback = ""
        self.feedback_timer = 0
        
        # Shop Inventory System
        self.player_speed = 3.6
        self.active_skin = "DEFAULT"
        self.unlocked_skins = ["DEFAULT"]
        self.speed_purchases = 0
        
        # Quiz Timer Parameters
        self.quiz_timer_duration = 30.0  # 30 seconds limit per sector
        self.quiz_timer_start = 0
        
        # Animation variables
        self.shake_intensity = 0
        self.shake_decay = 0.88
        self.walk_cycle = 0.0
        self.smooth_bob_y = 0.0
        
        # Geometry Layout Setup
        self.river_center_x = WORLD_SIZE // 2 
        self.river_width = 180
        self.bridge_y = WORLD_SIZE // 2  
        self.bridge_height_span = 70

        # Spawns Matrix
        self.player_x = self.river_center_x - 200
        self.player_y = self.bridge_y
        self.camera_x = float(self.player_x)
        self.camera_y = float(self.player_y)
        self.camera_smoothing = 0.08
        
        # Menu Rectangle Definitions
        self.start_btn = pygame.Rect(380, 500, 240, 60)
        self.load_btn = pygame.Rect(380, 580, 240, 50)
        self.next_btn = pygame.Rect(380, 450, 240, 60)
        
        # Pause UI Buttons
        self.resume_btn = pygame.Rect(380, 240, 240, 50)
        self.shop_btn = pygame.Rect(380, 310, 240, 50)
        self.save_btn = pygame.Rect(380, 380, 240, 50)
        self.quit_btn = pygame.Rect(380, 450, 240, 50)
        
        self.mode_buttons = {}
        self.quiz_option_rects = []
        self.shop_items_rects = []

        # Background Aesthetics
        self.clouds = [{"x": random.randint(0, WIDTH), "y": random.randint(20, 120), "speed": random.uniform(0.15, 0.45), "w": random.randint(110, 190)} for _ in range(5)]
        
        random.seed(8888)
        self.mountain_peaks = [
            {"wx": 0,   "wy": 0,   "h": 410, "r": 370}, 
            {"wx": 280, "wy": 0,   "h": 330, "r": 300}, 
            {"wx": 0,   "wy": 280, "h": 350, "r": 320}, 
            {"wx": 600, "wy": 0,   "h": 270, "r": 230}
        ]

        self.grass_tufts = []
        for _ in range(120):
            gx, gy = random.randint(30, WORLD_SIZE-30), random.randint(30, WORLD_SIZE-30)
            if not abs(gx - self.river_center_x) < (self.river_width // 2) and (gx + gy > 400):
                self.grass_tufts.append((gx, gy, random.randint(4, 7)))

        self.trees = []
        while len(self.trees) < 95:  
            tx, ty = random.randint(50, WORLD_SIZE - 50), random.randint(50, WORLD_SIZE - 50)
            if not self.is_in_river(tx, ty) and not (self.bridge_y - 120 <= ty <= self.bridge_y + 120) and (tx + ty > 450):
                tree_variant = random.choice(["BIRCH", "PINE_TALL", "PINE_WIDE"])
                self.trees.append((tx, ty, tree_variant, random.uniform(0.95, 1.25)))

        self.coins = []
        self.chests = []
        self.respawn_coins()
        self.respawn_chests()

    def trigger_shake(self, intensity):
        self.shake_intensity = intensity

    def world_to_iso(self, wx, wy, wz=0):
        dx = wx - self.camera_x
        dy = wy - self.camera_y
        iso_x = (dx - dy) * 1.1 + (WIDTH // 2)
        iso_y = (dx + dy) * 0.55 + (HEIGHT // 2) - wz
        
        if self.shake_intensity > 0.5:
            iso_x += random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            iso_y += random.randint(-int(self.shake_intensity), int(self.shake_intensity))
        return int(iso_x), int(iso_y)

    def is_on_bridge(self, wx, wy):
        if (self.bridge_y - self.bridge_height_span) <= wy <= (self.bridge_y + self.bridge_height_span):
            return abs(wx - self.river_center_x) < (self.river_width // 2 + 60)
        return False

    def is_in_river(self, wx, wy):
        if self.is_on_bridge(wx, wy):
            return False  
        return abs(wx - self.river_center_x) < (self.river_width // 2 - 10)

    def start_game_mode(self, mode_idx):
        self.selected_mode = mode_idx
        m = self.modes[mode_idx]
        self.lives = m["lives"]
        self.gold = 0
        self.current_level = 1
        self.player_speed = 3.6
        self.speed_purchases = 0
        self.active_skin = "DEFAULT"
        self.unlocked_skins = ["DEFAULT"]
        
        self.player_y = self.bridge_y
        self.player_x = self.river_center_x - 200
        self.camera_x = float(self.player_x)
        self.camera_y = float(self.player_y)
        self.respawn_chests()
        self.respawn_coins()
        self.state = "EXPLORING"

    def respawn_chests(self):
        self.chests = []
        random.seed(pygame.time.get_ticks() + 77)
        while len(self.chests) < 4:
            cx = random.randint(200, WORLD_SIZE - 200)
            cy = random.randint(200, WORLD_SIZE - 200)
            if not self.is_in_river(cx, cy) and not self.is_on_bridge(cx, cy) and (cx + cy > 450):
                if math.hypot(cx - self.player_x, cy - self.player_y) > 150:
                    self.chests.append((cx, cy))

    def respawn_coins(self):
        self.coins = []
        for _ in range(30):
            cx = random.randint(100, WORLD_SIZE - 100)
            cy = random.randint(100, WORLD_SIZE - 100)
            if not self.is_in_river(cx, cy) and (cx + cy > 450):
                self.coins.append((cx, cy))

    # --- Save & Load Implementation Engine ---
    def save_progress(self):
        data = {
            "player_name": self.player_name,
            "gold": self.gold,
            "current_level": self.current_level,
            "lives": self.lives,
            "selected_mode": self.selected_mode,
            "player_speed": self.player_speed,
            "speed_purchases": self.speed_purchases,
            "active_skin": self.active_skin,
            "unlocked_skins": self.unlocked_skins,
            "player_x": self.player_x,
            "player_y": self.player_y
        }
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f)
            self.feedback = "PROGRESS SYSTEM SAVED SUCCESSFULLY!"
            self.feedback_timer = pygame.time.get_ticks()
        except Exception:
            self.feedback = "ERROR EXECUTING SYSTEM WRITE"
            self.feedback_timer = pygame.time.get_ticks()

    def load_progress(self):
        if not os.path.exists(SAVE_FILE):
            self.feedback = "NO ACTIVE SAVE MATRIX FOUND!"
            self.feedback_timer = pygame.time.get_ticks()
            return False
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            self.player_name = data.get("player_name", "Explorer")
            self.gold = data.get("gold", 0)
            self.current_level = data.get("current_level", 1)
            self.lives = data.get("lives", 5)
            self.selected_mode = data.get("selected_mode", 1)
            self.player_speed = data.get("player_speed", 3.6)
            self.speed_purchases = data.get("speed_purchases", 0)
            self.active_skin = data.get("active_skin", "DEFAULT")
            self.unlocked_skins = data.get("unlocked_skins", ["DEFAULT"])
            self.player_x = data.get("player_x", self.river_center_x - 200)
            self.player_y = data.get("player_y", self.bridge_y)
            self.camera_x = float(self.player_x)
            self.camera_y = float(self.player_y)
            
            self.respawn_chests()
            self.respawn_coins()
            self.state = "EXPLORING"
            self.feedback = "RESTORED PROFILE MEMORY BLOCK!"
            self.feedback_timer = pygame.time.get_ticks()
            return True
        except Exception:
            self.feedback = "SAVE DATA CORRUPTED OR READ FAIL"
            self.feedback_timer = pygame.time.get_ticks()
            return False

    def evaluate_quiz_choice(self, chosen_idx):
        q_data = LEVEL_DATA[self.current_level]
        selected_answer = q_data["options"][chosen_idx].lower().strip()
        target_answer = q_data["a"].lower().strip()
        
        if selected_answer == target_answer:
            self.gold += 30
            self.feedback = f"CORRECT! +30 GOLD (SECTOR {self.current_level} CLEAR)"
            self.feedback_timer = pygame.time.get_ticks()
            if self.current_level >= 20:
                self.state = "WIN_SCREEN"
            else:
                self.state = "LEVEL_VICTORY"
        else:
            self.lives -= 1
            self.feedback = "INCORRECT RESPONSE ALERT!"
            self.trigger_shake(15)  
            self.feedback_timer = pygame.time.get_ticks()
            if self.lives <= 0:
                self.state = "GAME_OVER"
            else:
                self.state = "EXPLORING"

    def handle_shop_click(self, item_index):
        # 0: Speed Boost, 1: Royal Skin, 2: Cyber Skin
        if item_index == 0:
            if self.gold >= 75:
                self.gold -= 75
                self.player_speed += 0.6
                self.speed_purchases += 1
                self.feedback = "PURCHASED HYPER SPEED ENGINE BOOST!"
            else:
                self.feedback = "INSUFFICIENT GOLD RESERVES!"
        elif item_index == 1:
            if "ROYAL" in self.unlocked_skins:
                self.active_skin = "ROYAL"
                self.feedback = "EQUIPPED ROYAL ROBE SKIN"
            elif self.gold >= 150:
                self.gold -= 150
                self.unlocked_skins.append("ROYAL")
                self.active_skin = "ROYAL"
                self.feedback = "UNLOCKED & EQUIPPED ROYAL GARB!"
            else:
                self.feedback = "INSUFFICIENT GOLD RESERVES!"
        elif item_index == 2:
            if "CYBER" in self.unlocked_skins:
                self.active_skin = "CYBER"
                self.feedback = "EQUIPPED CYBER NET SUIT SKIN"
            elif self.gold >= 250:
                self.gold -= 250
                self.unlocked_skins.append("CYBER")
                self.active_skin = "CYBER"
                self.feedback = "UNLOCKED & EQUIPPED CYBERNETIC COAT!"
            else:
                self.feedback = "INSUFFICIENT GOLD RESERVES!"
        self.feedback_timer = pygame.time.get_ticks()

    # --- UI Layout Rendering Passes ---
    def draw_home_menu(self):
        self.screen.fill(C_DARK)
        t_s = self.title_font.render("BRAIN TREK: HIGHLAND EXPEDITION", True, C_GOLD)
        self.screen.blit(t_s, (WIDTH // 2 - t_s.get_width() // 2, 140))
        
        i1 = "Explore map grid paths, harvest coins, shop upgrades, and unlock grand master chests."
        i2 = "Features automated progress storage, countdown vectors, and hard tier levels."
        s1 = self.font.render(i1, True, C_WHITE)
        s2 = self.font.render(i2, True, C_WHITE)
        self.screen.blit(s1, (WIDTH // 2 - s1.get_width() // 2, 260))
        self.screen.blit(s2, (WIDTH // 2 - s2.get_width() // 2, 300))
        
        m_pos = pygame.mouse.get_pos()
        
        is_hov_start = self.start_btn.collidepoint(m_pos)
        pygame.draw.rect(self.screen, C_GOLD if is_hov_start else (195, 135, 20), self.start_btn, border_radius=12)
        b_txt = self.btn_font.render("NEW EXPEDITION", True, C_DARK)
        self.screen.blit(b_txt, (self.start_btn.centerx - b_txt.get_width() // 2, self.start_btn.centery - b_txt.get_height() // 2))

        is_hov_load = self.load_btn.collidepoint(m_pos)
        pygame.draw.rect(self.screen, C_CYAN if is_hov_load else (20, 130, 150), self.load_btn, border_radius=10)
        l_txt = self.btn_font.render("RESTORE LAST ARCHIVE", True, C_WHITE)
        self.screen.blit(l_txt, (self.load_btn.centerx - l_txt.get_width() // 2, self.load_btn.centery - l_txt.get_height() // 2))

    def draw_name_input(self):
        self.screen.fill(C_DARK)
        p_s = self.title_font.render("REGISTER PROFILE TAG", True, C_GOLD)
        self.screen.blit(p_s, (WIDTH // 2 - p_s.get_width() // 2, 200))
        
        sub_s = self.font.render("Type character identifier moniker, then press ENTER:", True, C_WHITE)
        self.screen.blit(sub_s, (WIDTH // 2 - sub_s.get_width() // 2, 290))
        
        box = pygame.Rect(250, 360, 500, 60)
        pygame.draw.rect(self.screen, C_GRAY, box, border_radius=10)
        pygame.draw.rect(self.screen, C_GOLD, box, 3, border_radius=10)
        
        n_surf = self.title_font.render(self.player_name + "_", True, C_YELLOW)
        self.screen.blit(n_surf, (270, box.centery - n_surf.get_height() // 2))

    def draw_mode_menu(self):
        self.screen.fill(C_DARK)
        t_s = self.title_font.render("SELECT DIFFICULTY ACCENTS", True, C_GOLD)
        self.screen.blit(t_s, (WIDTH // 2 - t_s.get_width() // 2, 80))
        
        m_pos = pygame.mouse.get_pos()
        card_w, card_h = 250, 360
        start_x = (WIDTH - (3 * card_w + 80)) // 2
        
        for idx, m_data in self.modes.items():
            cx = start_x + (idx - 1) * (card_w + 40)
            card_rect = pygame.Rect(cx, 200, card_w, card_h)
            self.mode_buttons[idx] = card_rect
            
            is_hov = card_rect.collidepoint(m_pos)
            pygame.draw.rect(self.screen, m_data["card"], card_rect, border_radius=15)
            pygame.draw.rect(self.screen, C_GOLD if is_hov else C_GRAY, card_rect, 3, border_radius=15)
            
            n_s = self.font.render(m_data["name"], True, C_WHITE)
            d_s = self.small_font.render(m_data["desc"], True, C_GOLD)
            self.screen.blit(n_s, (cx + 25, 240))
            self.screen.blit(d_s, (cx + 25, 290))
            
            btn = pygame.Rect(cx + 25, 460, card_w - 50, 45)
            pygame.draw.rect(self.screen, C_GOLD if is_hov else (175, 125, 30), btn, border_radius=8)
            lbl = self.btn_font.render("INITIALIZE", True, C_DARK)
            self.screen.blit(lbl, (btn.centerx - lbl.get_width() // 2, btn.centery - lbl.get_height() // 2))

    def draw_pause_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 22, 205))  
        self.screen.blit(overlay, (0, 0))
        
        m_rect = pygame.Rect(320, 140, 360, 400)
        pygame.draw.rect(self.screen, (32, 38, 55), m_rect, border_radius=16)
        pygame.draw.rect(self.screen, C_GOLD, m_rect, 3, border_radius=16)
        
        p_t = self.title_font.render("SYSTEM PAUSED", True, C_GOLD)
        self.screen.blit(p_t, (WIDTH // 2 - p_t.get_width() // 2, 165))
        
        m_pos = pygame.mouse.get_pos()
        
        for btn, label, color, hov_color in [
            (self.resume_btn, "RESUME EXPEDITION", (25, 120, 55), C_GREEN),
            (self.shop_btn, "ENTER SHOP TERMINAL", (140, 95, 20), C_GOLD),
            (self.save_btn, "SAVE ARCHIVE STATE", (20, 110, 130), C_CYAN),
            (self.quit_btn, "ABORT TO MAIN MENU", (160, 40, 40), C_RED)
        ]:
            is_h = btn.collidepoint(m_pos)
            pygame.draw.rect(self.screen, hov_color if is_h else color, btn, border_radius=8)
            lbl_t = self.btn_font.render(label, True, C_WHITE if color != C_GOLD else C_DARK)
            self.screen.blit(lbl_t, (btn.centerx - lbl_t.get_width()//2, btn.centery - lbl_t.get_height()//2))

    def draw_shop_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 15, 25, 235))
        self.screen.blit(overlay, (0, 0))
        
        box_frame = pygame.Rect(100, 80, 800, 540)
        pygame.draw.rect(self.screen, (25, 32, 48), box_frame, border_radius=16)
        pygame.draw.rect(self.screen, C_GOLD, box_frame, 4, border_radius=16)
        
        sh_t = self.title_font.render("HIGHLAND SUPPLY TERMINAL", True, C_GOLD)
        self.screen.blit(sh_t, (WIDTH // 2 - sh_t.get_width() // 2, 105))
        
        # Display Available Balance Vector
        bal_s = self.font.render(f"YOUR BALANCE: 🪙 {self.gold} GOLD", True, C_YELLOW)
        self.screen.blit(bal_s, (WIDTH // 2 - bal_s.get_width() // 2, 160))
        
        m_pos = pygame.mouse.get_pos()
        self.shop_items_rects = []
        
        shop_items = [
            {"name": "Engine Speed Boost", "desc": f"Increases movement. Owned: {self.speed_purchases}", "cost": "75 Gold", "btn_lbl": "PURCHASE (+0.6 Spd)"},
            {"name": "Royal Robes Gown", "desc": "Prestige gold apparel outfit matrix.", "cost": "150 Gold", "btn_lbl": "EQUIP" if "ROYAL" in self.unlocked_skins else "UNLOCK SKIN"},
            {"name": "Cybernetic Suit", "desc": "Neon synthetic glowing operations vest.", "cost": "250 Gold", "btn_lbl": "EQUIP" if "CYBER" in self.unlocked_skins else "UNLOCK SKIN"}
        ]
        
        for i, item in enumerate(shop_items):
            card_y = 210 + i * 115
            item_card = pygame.Rect(140, card_y, 720, 95)
            pygame.draw.rect(self.screen, (38, 46, 68), item_card, border_radius=10)
            pygame.draw.rect(self.screen, C_GRAY, item_card, 2, border_radius=10)
            
            # Text Renderers
            self.screen.blit(self.font.render(item["name"], True, C_WHITE), (170, card_y + 20))
            self.screen.blit(self.small_font.render(item["desc"], True, C_LIGHT_GRAY), (170, card_y + 52))
            self.screen.blit(self.font.render(item["cost"], True, C_GOLD), (490, card_y + 35))
            
            buy_btn = pygame.Rect(620, card_y + 25, 210, 45)
            self.shop_items_rects.append(buy_btn)
            
            is_h = buy_btn.collidepoint(m_pos)
            pygame.draw.rect(self.screen, C_GOLD if is_h else (180, 130, 25), buy_btn, border_radius=6)
            
            btn_txt = item["btn_lbl"]
            # Highlight current active skin indicators
            if i == 1 and self.active_skin == "ROYAL": btn_txt = "ACTIVE robes"
            if i == 2 and self.active_skin == "CYBER": btn_txt = "ACTIVE cyber"
            
            b_surf = self.small_font.render(btn_txt, True, C_DARK)
            self.screen.blit(b_surf, (buy_btn.centerx - b_surf.get_width() // 2, buy_btn.centery - b_surf.get_height() // 2))
            
        esc_lbl = self.small_font.render("Press ESCAPE or P to close Shop and return to pause layout map", True, C_WHITE)
        self.screen.blit(esc_lbl, (WIDTH // 2 - esc_lbl.get_width() // 2, 585))

    def draw_level_victory(self):
        self.screen.fill(C_DARK)
        v_s = self.title_font.render("SECTOR BLOCK VECTOR CLEARED!", True, C_GOLD)
        self.screen.blit(v_s, (WIDTH // 2 - v_s.get_width() // 2, 240))
        
        info_s = self.font.render(f"Prepare matrix systems for Level Sector {self.current_level + 1}", True, C_WHITE)
        self.screen.blit(info_s, (WIDTH // 2 - info_s.get_width() // 2, 310))
        
        is_hov = self.next_btn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, C_GREEN if is_hov else (20, 140, 50), self.next_btn, border_radius=10)
        lbl = self.btn_font.render("CONTINUE MISSION", True, C_DARK)
        self.screen.blit(lbl, (self.next_btn.centerx - lbl.get_width() // 2, self.next_btn.centery - lbl.get_height() // 2))

    # --- Grand Triumph Winning Screen ---
    def draw_win_screen(self):
        self.screen.fill((10, 22, 18))
        
        # Golden pulse aura visual background vector simulation ticks
        pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.004)) * 30)
        pygame.draw.circle(self.screen, (245, 185, 35, 20), (WIDTH//2, 240), 120 + pulse)
        
        w_t = self.title_font.render("🏆 HIGHLAND EXPEDITION TRIUMPH! 🏆", True, C_GOLD)
        self.screen.blit(w_t, (WIDTH // 2 - w_t.get_width() // 2, 220))
        
        m1 = f"Congratulations Operator, {self.player_name}! You completed all 20 advanced challenge zones."
        m2 = f"Final Wealth Inventory Harvested: 🪙 {self.gold} accumulated gold assets."
        
        s1 = self.font.render(m1, True, C_WHITE)
        s2 = self.font.render(m2, True, C_YELLOW)
        self.screen.blit(s1, (WIDTH // 2 - s1.get_width() // 2, 340))
        self.screen.blit(s2, (WIDTH // 2 - s2.get_width() // 2, 390))
        
        r_s = self.small_font.render("Press ENTER terminal key to cycle back safely to Main Menu Terminal core system", True, C_LIGHT_GRAY)
        self.screen.blit(r_s, (WIDTH // 2 - r_s.get_width() // 2, 500))

    def draw_game_over(self):
        self.screen.fill(C_DARK)
        o_s = self.title_font.render("💀 CORE EXPEDITION SIMULATION FAILED 💀", True, C_RED)
        self.screen.blit(o_s, (WIDTH // 2 - o_s.get_width() // 2, 240))
        r_s = self.font.render("Press ENTER to return safely to Main System Base Module Terminal", True, C_WHITE)
        self.screen.blit(r_s, (WIDTH // 2 - r_s.get_width() // 2, 360))

    def draw_minimap(self):
        mm_size = 140
        mm_offset = 20
        mm_x = WIDTH - mm_size - mm_offset
        mm_y = HEIGHT - mm_size - mm_offset - 10
        
        pygame.draw.rect(self.screen, (20, 25, 38), (mm_x, mm_y, mm_size, mm_size), border_radius=8)
        pygame.draw.rect(self.screen, C_GOLD, (mm_x, mm_y, mm_size, mm_size), 2, border_radius=8)
        
        scale = float(mm_size) / WORLD_SIZE
        
        rx = int((self.river_center_x) * scale) + mm_x
        rw = int(self.river_width * scale)
        pygame.draw.rect(self.screen, C_RIVER_MID, (rx - rw//2, mm_y + 2, rw, mm_size - 4))
        
        by = int((self.bridge_y) * scale) + mm_y
        bh = int(self.bridge_height_span * 2 * scale)
        pygame.draw.rect(self.screen, (140, 90, 50), (rx - rw//2 - 2, by - bh//2, rw + 4, bh))

        for cx, cy in self.chests:
            mcx = int(cx * scale) + mm_x
            mcy = int(cy * scale) + mm_y
            if mm_x <= mcx <= mm_x + mm_size and mm_y <= mcy <= mm_y + mm_size:
                pygame.draw.circle(self.screen, C_YELLOW, (mcx, mcy), 3)

        mpx = int(self.player_x * scale) + mm_x
        mpy = int(self.player_y * scale) + mm_y
        if mm_x <= mpx <= mm_x + mm_size and mm_y <= mpy <= mm_y + mm_size:
            pygame.draw.circle(self.screen, C_RED, (mpx, mpy), 4)

        self.screen.blit(self.small_font.render("MINI-MAP", True, C_LIGHT_GRAY), (mm_x + 5, mm_y - 20))

    def draw_clouds_and_birds(self):
        cloud_surf = pygame.Surface((WIDTH, 200), pygame.SRCALPHA)
        for c in self.clouds:
            c["x"] = (c["x"] + c["speed"]) % (WIDTH + c["w"])
            pygame.draw.ellipse(cloud_surf, C_CLOUD, (int(c["x"] - c["w"]), c["y"], c["w"], 45))
        self.screen.blit(cloud_surf, (0, 0))

        num_birds = 4
        ticks = pygame.time.get_ticks() * 0.001
        base_x = (ticks * 45) % (WIDTH + 200) - 100
        for i in range(num_birds):
            ox = i * 26
            oy = i * 12 + math.sin(ticks * 3 + i) * 10
            bx, by = int(base_x + ox), int(90 + oy)
            if 0 <= bx < WIDTH:
                wing = int(abs(math.sin(ticks * 8)) * 6)
                pygame.draw.line(self.screen, C_BIRD, (bx, by), (bx - 8, by - wing), 2)
                pygame.draw.line(self.screen, C_BIRD, (bx, by), (bx + 8, by - wing), 2)

    def draw_realistic_mountain_range(self):
        for peak in self.mountain_peaks:
            hx, hy = peak["wx"] - 40, peak["wy"] - 40
            p_pk = self.world_to_iso(hx, hy, wz=int(peak["h"] * 1.25))
            p_l = self.world_to_iso(hx, hy + int(peak["r"] * 1.35))
            p_r = self.world_to_iso(hx + int(peak["r"] * 1.35), hy)
            pygame.draw.polygon(self.screen, C_MNT_FAR, [p_pk, p_l, p_r])

        for peak in self.mountain_peaks:
            wx, wy, h, r = peak["wx"], peak["wy"], peak["h"], peak["r"]
            
            p_peak = self.world_to_iso(wx, wy, wz=h)
            p_left = self.world_to_iso(wx, wy + r)
            p_right = self.world_to_iso(wx + r, wy)
            p_front = self.world_to_iso(wx + r, wy + r)

            pygame.draw.polygon(self.screen, C_MNT_DARK, [p_peak, p_left, p_front])
            pygame.draw.polygon(self.screen, C_MNT_LIGHT, [p_peak, p_right, p_front])
            
            p_sn_l = self.world_to_iso(wx, wy + int(r * 0.3), wz=int(h * 0.7))
            p_sn_r = self.world_to_iso(wx + int(r * 0.3), wy, wz=int(h * 0.7))
            p_sn_f = self.world_to_iso(wx + int(r * 0.35), wy + int(r * 0.35), wz=int(h * 0.68))
            pygame.draw.polygon(self.screen, C_MNT_SNOW, [p_peak, p_sn_l, p_sn_f, p_sn_r])

    def run(self):
        while True:
            if self.shake_intensity > 0:
                self.shake_intensity *= self.shake_decay

            mx, my = pygame.mouse.get_pos()

            # --- Live Quiz Countdown Vectors Engine Mapping ---
            if self.state == "QUIZ":
                elapsed_quiz_time = (pygame.time.get_ticks() - self.quiz_timer_start) / 1000.0
                remaining_quiz_time = max(0.0, self.quiz_timer_duration - elapsed_quiz_time)
                
                # Dynamic feedback warning alert system
                if remaining_quiz_time < 6.0:
                    self.trigger_shake(2.0)
                
                if remaining_quiz_time <= 0.0:
                    self.lives -= 1
                    self.feedback = "TIME EXPIRED! SECURITY BREACH PENALTY"
                    self.trigger_shake(20)
                    self.feedback_timer = pygame.time.get_ticks()
                    if self.lives <= 0: self.state = "GAME_OVER"
                    else: self.state = "EXPLORING"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        if self.state == "EXPLORING":
                            self.state = "PAUSED"
                        elif self.state in ["PAUSED", "SHOP"]:
                            self.state = "EXPLORING"

                if self.state == "HOME_MENU" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.start_btn.collidepoint(event.pos):
                            self.state = "NAME_INPUT"
                        elif self.load_btn.collidepoint(event.pos):
                            self.load_progress()
                        
                elif self.state == "NAME_INPUT" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(self.player_name.strip()) > 0:
                        self.state = "MODE_MENU"
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    else:
                        if len(self.player_name) < 14 and event.unicode.isalnum():
                            self.player_name += event.unicode
                            
                elif self.state == "MODE_MENU" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for idx, btn in self.mode_buttons.items():
                            if btn.collidepoint(event.pos):
                                self.start_game_mode(idx)

                elif self.state == "PAUSED" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.resume_btn.collidepoint(event.pos):
                            self.state = "EXPLORING"
                        elif self.shop_btn.collidepoint(event.pos):
                            self.state = "SHOP"
                        elif self.save_btn.collidepoint(event.pos):
                            self.save_progress()
                        elif self.quit_btn.collidepoint(event.pos):
                            self.state = "HOME_MENU"
                            self.player_name = ""

                elif self.state == "SHOP" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for idx, buy_rect in enumerate(self.shop_items_rects):
                            if buy_rect.collidepoint(event.pos):
                                self.handle_shop_click(idx)
                                break

                elif self.state == "QUIZ" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for o_idx, opt_rect in enumerate(self.quiz_option_rects):
                            if opt_rect.collidepoint(event.pos):
                                self.evaluate_quiz_choice(o_idx)
                                break
                            
                elif self.state == "LEVEL_VICTORY" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.next_btn.collidepoint(event.pos):
                        self.current_level += 1
                        self.respawn_chests()
                        self.state = "EXPLORING"
                            
                elif self.state in ["GAME_OVER", "WIN_SCREEN"] and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.state = "HOME_MENU"
                        self.player_name = ""
                        self.gold = 0
                        self.current_level = 1
                        self.lives = 5

            if self.state == "EXPLORING":
                keys = pygame.key.get_pressed()
                vx, vy = 0, 0
                
                if keys[pygame.K_UP] or keys[pygame.K_w]:    vx -= self.player_speed; vy -= self.player_speed
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:  vx += self.player_speed; vy += self.player_speed
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:  vx -= self.player_speed; vy += self.player_speed
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: vx += self.player_speed; vy -= self.player_speed
                
                is_moving = (vx != 0 or vy != 0)
                if is_moving:
                    # Fluid movement speed walk dampener scalar calculation 
                    self.walk_cycle += 0.18  
                    # Smooth sinusoidal positional assignment vectors
                    self.smooth_bob_y = math.sin(self.walk_cycle) * 5.5
                    
                    old_x = self.player_x
                    self.player_x += vx
                    hit = self.is_in_river(self.player_x, self.player_y) or (self.player_x + self.player_y < 420)
                    for tx, ty, _, scale in self.trees:
                        if math.hypot(self.player_x - tx, self.player_y - ty) < (18 * scale): hit = True
                    if hit: self.player_x = old_x
                            
                    old_y = self.player_y
                    self.player_y += vy
                    hit = self.is_in_river(self.player_x, self.player_y) or (self.player_x + self.player_y < 420)
                    for tx, ty, _, scale in self.trees:
                        if math.hypot(self.player_x - tx, self.player_y - ty) < (18 * scale): hit = True
                    if hit: self.player_y = old_y
                else:
                    # Seamlessly decay player bob state variables back to baseline resting geometry
                    self.smooth_bob_y *= 0.75

                self.player_x = max(30, min(self.player_x, WORLD_SIZE - 30))
                self.player_y = max(30, min(self.player_y, WORLD_SIZE - 30))
                
                self.camera_x += (self.player_x - self.camera_x) * self.camera_smoothing
                self.camera_y += (self.player_y - self.camera_y) * self.camera_smoothing
                
                for coin in self.coins[:]:
                    if math.hypot(self.player_x - coin[0], self.player_y - coin[1]) < 30:
                        self.gold += 5
                        self.coins.remove(coin)
                
                for c_pos in self.chests[:]:
                    if math.hypot(self.player_x - c_pos[0], self.player_y - c_pos[1]) < 42:
                        self.state = "QUIZ"
                        self.quiz_timer_start = pygame.time.get_ticks()
                        self.chests.remove(c_pos)

            # --- Master Graphic Scene Generation Frame Dispatch Pipelines ---
            if self.state in ["HOME_MENU", "NAME_INPUT", "MODE_MENU", "LEVEL_VICTORY", "GAME_OVER", "WIN_SCREEN"]:
                if self.state == "HOME_MENU": self.draw_home_menu()
                elif self.state == "NAME_INPUT": self.draw_name_input()
                elif self.state == "MODE_MENU": self.draw_mode_menu()
                elif self.state == "LEVEL_VICTORY": self.draw_level_victory()
                elif self.state == "GAME_OVER": self.draw_game_over()
                elif self.state == "WIN_SCREEN": self.draw_win_screen()
            else:
                self.screen.fill(C_SKY_BLUE) 
                self.draw_clouds_and_birds()

                pts = [self.world_to_iso(0, 0), self.world_to_iso(WORLD_SIZE, 0), 
                       self.world_to_iso(WORLD_SIZE, WORLD_SIZE), self.world_to_iso(0, WORLD_SIZE)]
                pygame.draw.polygon(self.screen, (42, 158, 72), pts)
                
                self.draw_realistic_mountain_range()

                for gx, gy, sz in self.grass_tufts:
                    gsx, gsy = self.world_to_iso(gx, gy)
                    if -50 < gsx < WIDTH+50 and -50 < gsy < HEIGHT+50:
                        pygame.draw.line(self.screen, C_GRASS_DETAIL, (gsx, gsy), (gsx - 2, gsy - sz), 2)
                        pygame.draw.line(self.screen, C_GRASS_DETAIL, (gsx, gsy), (gsx + 3, gsy - sz + 1), 2)
                
                r_l = self.river_center_x - (self.river_width // 2)
                r_r = self.river_center_x + (self.river_width // 2)
                pygame.draw.polygon(self.screen, C_RIVER_DEEP, [self.world_to_iso(r_l - 10, 0), self.world_to_iso(r_r + 10, 0), self.world_to_iso(r_r + 10, WORLD_SIZE), self.world_to_iso(r_l - 10, WORLD_SIZE)])
                pygame.draw.polygon(self.screen, C_RIVER_MID, [self.world_to_iso(r_l, 0), self.world_to_iso(r_r, 0), self.world_to_iso(r_r, WORLD_SIZE), self.world_to_iso(r_l, WORLD_SIZE)])
                pygame.draw.polygon(self.screen, C_RIVER_LIGHT, [self.world_to_iso(r_l + 25, 0), self.world_to_iso(r_r - 25, 0), self.world_to_iso(r_r - 25, WORLD_SIZE), self.world_to_iso(r_l + 25, WORLD_SIZE)])

                for step_y in range(0, WORLD_SIZE, 50):
                    foam_time = pygame.time.get_ticks() * 0.005
                    foam_w = int(abs(math.sin(foam_time + step_y)) * 5) + 2
                    pygame.draw.line(self.screen, C_WATER_FOAM, self.world_to_iso(r_l, step_y), self.world_to_iso(r_l + foam_w, step_y), 2)
                    pygame.draw.line(self.screen, C_WATER_FOAM, self.world_to_iso(r_r, step_y), self.world_to_iso(r_r - foam_w, step_y), 2)

                b_w, b_h = self.river_width // 2 + 30, self.bridge_height_span
                p1 = self.world_to_iso(self.river_center_x - b_w, self.bridge_y - b_h)
                p2 = self.world_to_iso(self.river_center_x + b_w, self.bridge_y - b_h)
                p3 = self.world_to_iso(self.river_center_x + b_w, self.bridge_y + b_h)
                p4 = self.world_to_iso(self.river_center_x - b_w, self.bridge_y + b_h)
                
                pygame.draw.polygon(self.screen, (140, 90, 45), [p1, p2, p3, p4])
                pygame.draw.polygon(self.screen, C_BAZAM_WOOD, [p1, p2, p3, p4], 3)
                for offset in range(-b_h + 10, b_h, 15):
                    pl1 = self.world_to_iso(self.river_center_x - b_w, self.bridge_y + offset)
                    pl2 = self.world_to_iso(self.river_center_x + b_w, self.bridge_y + offset)
                    pygame.draw.line(self.screen, C_BAZAM_WOOD, pl1, pl2, 2)

                # Sorting isometric layer elements
                render_queue = []
                for tx, ty, t_variant, scale in self.trees:
                    render_queue.append((tx + ty, "TREE", tx, ty, (t_variant, scale)))
                for cx, cy in self.chests:
                    render_queue.append((cx + cy, "CHEST", cx, cy, None))
                for c_x, c_y in self.coins:
                    render_queue.append((c_x + c_y, "COIN", c_x, c_y, None))
                
                render_queue.append((self.river_center_x - 110 + self.bridge_y, "PIER", self.river_center_x - 110, self.bridge_y, "LEFT"))
                render_queue.append((self.river_center_x + 110 + self.bridge_y, "PIER", self.river_center_x + 110, self.bridge_y, "RIGHT"))
                render_queue.append((self.player_x + self.player_y, "PLAYER", self.player_x, self.player_y, None))
                render_queue.append((self.river_center_x + self.bridge_y + 1, "RAILINGS", self.river_center_x, self.bridge_y, None))

                ticks = pygame.time.get_ticks() * 0.03
                for f_id in range(5):
                    f_y = (f_id * 450 + ticks) % (WORLD_SIZE - 100) + 50
                    f_x = self.river_center_x + int(math.sin(ticks * 0.04 + f_id) * 30)
                    render_queue.append((f_x + f_y - 20, "FISH", f_x, f_y, ticks + f_id))

                render_queue.sort(key=lambda item: item[0])

                shadow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                for item in render_queue:
                    typ, wx, wy = item[1], item[2], item[3]
                    sx, sy = self.world_to_iso(wx, wy)
                    if typ == "PLAYER":
                        wz_offset = 12 if self.is_on_bridge(wx, wy) else 0
                        pygame.draw.ellipse(shadow_surf, C_SHADOW, (sx - 18, sy - 6 + wz_offset, 36, 13))
                    elif typ == "TREE":
                        pygame.draw.ellipse(shadow_surf, C_SHADOW, (sx - 22, sy - 9, 44, 16))
                    elif typ == "CHEST":
                        pygame.draw.ellipse(shadow_surf, C_SHADOW, (sx - 20, sy - 7, 40, 14))
                self.screen.blit(shadow_surf, (0, 0))

                for item in render_queue:
                    typ, wx, wy, data_pkg = item[1], item[2], item[3], item[4]
                    sx, sy = self.world_to_iso(wx, wy)
                    
                    if typ == "PIER":
                        p1_stone = self.world_to_iso(wx - 25, wy - 65)
                        p2_stone = self.world_to_iso(wx + 25, wy - 65)
                        p3_stone = self.world_to_iso(wx + 25, wy + 65)
                        p4_stone = self.world_to_iso(wx - 25, wy + 65)
                        pygame.draw.polygon(self.screen, C_BAZAM_STONE, [p1_stone, p2_stone, p3_stone, p4_stone])
                        pygame.draw.polygon(self.screen, C_DARK, [p1_stone, p2_stone, p3_stone, p4_stone], 2)
                        
                    elif typ == "RAILINGS":
                        pr1 = self.world_to_iso(wx - b_w, wy - b_h, wz=18)
                        pr2 = self.world_to_iso(wx + b_w, wy - b_h, wz=18)
                        pr3 = self.world_to_iso(wx + b_w, wy + b_h, wz=18)
                        pr4 = self.world_to_iso(wx - b_w, wy + b_h, wz=18)
                        pygame.draw.line(self.screen, C_BAZAM_GOLD, p1, pr1, 3)
                        pygame.draw.line(self.screen, C_BAZAM_GOLD, p2, pr2, 3)
                        pygame.draw.line(self.screen, C_BAZAM_GOLD, p3, pr3, 3)
                        pygame.draw.line(self.screen, C_BAZAM_GOLD, p4, pr4, 3)
                        pygame.draw.polygon(self.screen, C_BAZAM_GOLD, [pr1, pr2, pr3, pr4], 2)
                        
                    elif typ == "FISH":
                        wiggle = int(math.sin(data_pkg * 0.4) * 4)
                        pygame.draw.ellipse(self.screen, C_ORANGE, (sx - 9, sy - 4, 18, 9))
                        pygame.draw.polygon(self.screen, C_GOLD, [(sx + 9, sy), (sx + 15, sy - 4 + wiggle), (sx + 15, sy + 4 + wiggle)])
                        
                    elif typ == "COIN":
                        spin_scale = math.sin(pygame.time.get_ticks() * 0.007 + (wx * 0.05))
                        bob_height = int(math.sin(pygame.time.get_ticks() * 0.005 + wy) * 4) - 10
                        c_w = max(2, int(12 * abs(spin_scale)))
                        if -20 < sx < WIDTH+20:
                            pygame.draw.ellipse(self.screen, C_GOLD, (sx - c_w//2, sy + bob_height, c_w, 14))
                            pygame.draw.ellipse(self.screen, C_YELLOW, (sx - c_w//4, sy + bob_height + 2, c_w//2, 10))
                        
                    elif typ == "PLAYER":
                        wz = 12 if self.is_on_bridge(wx, wy) else 0
                        psx, psy = self.world_to_iso(wx, wy, wz=wz)
                        
                        # Apply dynamic aesthetic skin coats directly to core layout
                        base_color = C_GHO_MAROON
                        accent_color = C_GOLD
                        if self.active_skin == "ROYAL":
                            base_color = C_PURPLE
                            accent_color = C_YELLOW
                        elif self.active_skin == "CYBER":
                            base_color = C_DARK
                            accent_color = C_CYAN
                        
                        bob = int(self.smooth_bob_y)
                        pygame.draw.rect(self.screen, base_color, (psx - 16, psy - 52 + bob, 32, 45), border_radius=6)
                        pygame.draw.rect(self.screen, C_LAGAY_WHITE, (psx - 16, psy - 12 + bob, 6, 6))
                        pygame.draw.rect(self.screen, C_LAGAY_WHITE, (psx + 10, psy - 12 + bob, 6, 6))
                        pygame.draw.rect(self.screen, accent_color, (psx - 16, psy - 28 + bob, 32, 5))
                        pygame.draw.circle(self.screen, (255, 212, 182), (psx, psy - 64 + bob), 14)
                        pygame.draw.rect(self.screen, accent_color, (psx - 4,  psy - 42 + bob, 8, 6)) 
                        
                    elif typ == "TREE":
                        t_variant, scale = data_pkg
                        if t_variant == "BIRCH":
                            pygame.draw.rect(self.screen, C_BIRCH_TRUNK, (sx - int(5 * scale), sy - int(35 * scale), int(10 * scale), int(40 * scale)))
                            pygame.draw.circle(self.screen, (210, 145, 18), (sx, sy - int(46 * scale)), int(26 * scale))
                            pygame.draw.circle(self.screen, C_BIRCH_LEAVES, (sx, sy - int(66 * scale)), int(20 * scale))
                        elif t_variant == "PINE_TALL":
                            pygame.draw.rect(self.screen, C_BAZAM_WOOD, (sx - int(6 * scale), sy - int(45 * scale), int(12 * scale), int(50 * scale)))
                            pygame.draw.polygon(self.screen, (18, 95, 38), [(sx, sy - int(95 * scale)), (sx - int(25 * scale), sy - int(45 * scale)), (sx + int(25 * scale), sy - int(45 * scale))])
                            pygame.draw.polygon(self.screen, (22, 115, 48), [(sx, sy - int(115 * scale)), (sx - int(18 * scale), sy - int(75 * scale)), (sx + int(18 * scale), sy - int(75 * scale))])
                        else:  
                            pygame.draw.rect(self.screen, C_BAZAM_WOOD, (sx - int(7 * scale), sy - int(35 * scale), int(14 * scale), int(40 * scale)))
                            pygame.draw.circle(self.screen, (12, 90, 30), (sx, sy - int(45 * scale)), int(34 * scale))
                            pygame.draw.circle(self.screen, (28, 125, 50), (sx, sy - int(65 * scale)), int(24 * scale))
                        
                    elif typ == "CHEST":
                        glow_p = int(abs(math.sin(pygame.time.get_ticks() * 0.006)) * 8) + 4
                        glow_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (255, 230, 130, 35 + glow_p * 4), (50, 50), 18 + glow_p)
                        self.screen.blit(glow_surf, (sx - 50, sy - 65))
                        pygame.draw.rect(self.screen, (195, 125, 15), (sx - 20, sy - 22, 40, 26), border_radius=4)
                        pygame.draw.rect(self.screen, C_GOLD, (sx - 20, sy - 25, 40, 8), border_radius=2)
                        pygame.draw.rect(self.screen, C_DARK, (sx - 4, sy - 20, 8, 8), border_radius=1)

                # --- Multiple Choice Display Core Card ---
                if self.state == "QUIZ":
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((10, 12, 22, 225))
                    self.screen.blit(overlay, (0, 0))
                    
                    card_rect = pygame.Rect(120, 100, 760, 500)
                    pygame.draw.rect(self.screen, (36, 42, 60), card_rect, border_radius=16)
                    pygame.draw.rect(self.screen, C_GOLD, card_rect, 4, border_radius=16)
                    
                    q_data = LEVEL_DATA[self.current_level]
                    self.screen.blit(self.font.render(f"CHALLENGE VECTOR TASK {self.current_level}: {q_data['subj']}", True, C_GOLD), (160, 130))
                    self.screen.blit(self.font.render(q_data["q"], True, C_WHITE), (160, 180))
                    
                    # Live Render Timer Vector Strip Line
                    t_width = int(760 * (remaining_quiz_time / self.quiz_timer_duration))
                    t_color = C_GREEN if remaining_quiz_time > 10 else C_RED
                    pygame.draw.rect(self.screen, t_color, (120, 95, t_width, 6))
                    
                    time_s = self.font.render(f"⏱️ TIME REMAINING: {remaining_quiz_time:.1f}s", True, t_color)
                    self.screen.blit(time_s, (WIDTH - time_s.get_width() - 150, 130))
                    
                    self.quiz_option_rects = []
                    for idx, opt in enumerate(q_data["options"]):
                        r_y = 245 + idx * 62
                        opt_rect = pygame.Rect(160, r_y, 680, 48)
                        self.quiz_option_rects.append(opt_rect)
                        
                        is_hov = opt_rect.collidepoint(mx, my)
                        pygame.draw.rect(self.screen, (50, 58, 82) if is_hov else (25, 30, 45), opt_rect, border_radius=8)
                        pygame.draw.rect(self.screen, C_GOLD if is_hov else C_GRAY, opt_rect, 2, border_radius=8)
                        
                        lbl_opt = self.font.render(f" {idx + 1} »  {opt}", True, C_YELLOW if is_hov else C_WHITE)
                        self.screen.blit(lbl_opt, (185, r_y + 10))

                # --- Menu Overlay Management Routing ---
                if self.state == "PAUSED": self.draw_pause_menu()
                elif self.state == "SHOP": self.draw_shop_menu()
                elif self.state == "EXPLORING": self.draw_minimap()

                # --- Top HUD Bar ---
                pygame.draw.rect(self.screen, (12, 15, 26), (0, 0, WIDTH, 75))
                pygame.draw.line(self.screen, C_GOLD, (0, 75), (WIDTH, 75), 2)
                
                self.screen.blit(self.font.render(f"🪙 GOLD: {self.gold}", True, C_GOLD), (40, 24))
                self.screen.blit(self.font.render(f"❤️ LIVES: {self.lives}", True, C_RED), (230, 24))
                self.screen.blit(self.font.render(f"🎯 VECTOR: {self.current_level}/20", True, C_GREEN), (410, 24))
                self.screen.blit(self.small_font.render(f"🏃 SPD: {self.player_speed:.1f}", True, C_CYAN), (580, 28))
                
                n_txt = self.font.render(f"OP: {self.player_name}", True, C_WHITE)
                self.screen.blit(n_txt, (WIDTH - n_txt.get_width() - 40, 24))
            
            # Draw notifications matching parameters
            now = pygame.time.get_ticks()
            if now - self.feedback_timer < 2500 and self.feedback:
                f_box = pygame.Rect(WIDTH // 2 - 275, 95, 550, 45)
                pygame.draw.rect(self.screen, (22, 28, 42), f_box, border_radius=8)
                pygame.draw.rect(self.screen, C_GOLD, f_box, 2, border_radius=8)
                f_msg = self.font.render(self.feedback, True, C_WHITE if ("CORRECT" in self.feedback or "SUCCESS" in self.feedback or "EQUIP" in self.feedback or "PURCHASE" in self.feedback) else C_RED)
                self.screen.blit(f_msg, (WIDTH // 2 - f_msg.get_width() // 2, 105))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = UltimateBrainTrekEngine()
    game.run()