import pygame
import sys
import random

# --- Window Configurations ---
WIDTH = 1000
HEIGHT = 700
WORLD_SIZE = 3000 
FPS = 60

# --- Color Constants ---
C_GOLD = (255, 215, 0)
C_RED = (255, 50, 50)
C_WHITE = (255, 255, 255)
C_YELLOW = (255, 255, 0)
C_DARK = (20, 20, 30)
C_BLUE = (0, 50, 150)
C_GRAY = (70, 70, 90)
C_GREEN = (0, 255, 100)

# --- Level 1-10 Chart Database ---
LEVEL_DATA = {
    1: {
        "subj": "Science",
        "q": "Which gas do trees release?",
        "a": "oxygen",
        "r": 10
    },
    2: {
        "subj": "Mathematics",
        "q": "What is 8 * 5?",
        "a": "40",
        "r": 10
    },
    3: {
        "subj": "History",
        "q": "Who was the first king of Bhutan?",
        "a": "ugyen wangchuck",
        "r": 10
    },
    4: {
        "subj": "Economics",
        "q": "If you have 50 gold and spend 20, how much remains?",
        "a": "30",
        "r": 15
    },
    5: {
        "subj": "Science",
        "q": "What is the role of decomposers in an ecosystem?",
        "a": "break down dead organisms",
        "r": 20
    },
    6: {
        "subj": "Mathematics",
        "q": "Solve: (12 + 8) / 4",
        "a": "5",
        "r": 20
    },
    7: {
        "subj": "History",
        "q": "In which year was Bhutan's Constitution adopted?",
        "a": "2008",
        "r": 20
    },
    8: {
        "subj": "Economics",
        "q": "What happens when demand increases but supply stays same?",
        "a": "price increases",
        "r": 25
    },
    9: {
        "subj": "Science/Logic",
        "q": "Why are forests important for biodiversity?",
        "a": "they provide habitat/support many species",
        "r": 30
    },
    10: {
        "subj": "Mixed Challenge",
        "q": "What is 2008 + 5 * 2?",
        "a": "2018",
        "r": 30
    }
}

class BrainTrekGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Brain Trek")
        self.clock = pygame.time.Clock()
        
        # Typography Assets
        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.btn_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 40, bold=True)
        
        # Mode Mechanics Settings
        self.modes = {
            1: {
                "name": "Casual Mode",
                "desc": "10 Lives Available",
                "lives": 10,
                "bg": (34, 110, 34),
                "tree": (15, 60, 15),
                "card": (24, 76, 24)
            },
            2: {
                "name": "Scholar Mode",
                "desc": "5 Lives Available",
                "lives": 5,
                "bg": (120, 110, 95),
                "tree": (80, 75, 65),
                "card": (89, 81, 69)
            },
            3: {
                "name": "Survival Mode",
                "desc": "1 Life Challenge",
                "lives": 1,
                "bg": (145, 130, 155),
                "tree": (75, 60, 85),
                "card": (95, 75, 105)
            }
        }
        
        # Application Status Vectors
        self.state = "HOME_MENU"
        self.player_name = ""
        self.gold = 0
        self.current_level = 1
        self.lives = 5
        self.feedback = ""
        self.feedback_timer = 0
        self.user_input = ""
        
        # UI Button Boundaries
        self.start_btn = pygame.Rect(380, 500, 240, 60)
        self.next_btn = pygame.Rect(380, 460, 240, 60)
        self.mode_buttons = {}

    def draw_home_menu(self):
        self.screen.fill(C_DARK)
        
        t_s = self.title_font.render("BRAIN TREK", True, C_GOLD)
        self.screen.blit(t_s, (WIDTH // 2 - t_s.get_width() // 2, 80))
        
        i1 = "Roam the maps, collect the chests, and crack quizzes."
        i2 = "Progress sequentially from Level 1 up through Level 10!"
        s1 = self.font.render(i1, True, C_WHITE)
        s2 = self.font.render(i2, True, C_WHITE)
        self.screen.blit(s1, (WIDTH // 2 - s1.get_width() // 2, 210))
        self.screen.blit(s2, (WIDTH // 2 - s2.get_width() // 2, 245))
        
        d1 = "DEVELOPERS:"
        d2 = "Reegyel, Bikash, Krishna"
        d1_s = self.font.render(d1, True, C_GOLD)
        d2_s = self.font.render(d2, True, C_YELLOW)
        self.screen.blit(d1_s, (WIDTH // 2 - d1_s.get_width() // 2, 340))
        self.screen.blit(d2_s, (WIDTH // 2 - d2_s.get_width() // 2, 375))
        
        m_pos = pygame.mouse.get_pos()
        is_hov = self.start_btn.collidepoint(m_pos)
        b_col = C_GOLD if is_hov else (210, 165, 45)
        pygame.draw.rect(self.screen, b_col, self.start_btn, border_radius=15)
        
        btn_s = self.btn_font.render("START GAME", True, C_DARK)
        self.screen.blit(btn_s, (self.start_btn.centerx - btn_s.get_width() // 2, self.start_btn.centery - btn_s.get_height() // 2))

    def draw_name_input(self):
        self.screen.fill(C_DARK)
        p_s = self.title_font.render("REGISTER EXPLORER NAME", True, C_GOLD)
        self.screen.blit(p_s, (WIDTH // 2 - p_s.get_width() // 2, 160))
        
        sub = "Type your username profile label, then press ENTER to lock in"
        sub_s = self.font.render(sub, True, C_WHITE)
        self.screen.blit(sub_s, (WIDTH // 2 - sub_s.get_width() // 2, 240))
        
        box_rect = pygame.Rect(250, 320, 500, 65)
        pygame.draw.rect(self.screen, C_GRAY, box_rect, border_radius=12)
        pygame.draw.rect(self.screen, C_GOLD, box_rect, 3, border_radius=12)
        
        disp_name = self.player_name + "_"
        name_s = self.title_font.render(disp_name, True, C_YELLOW)
        self.screen.blit(name_s, (280, box_rect.centery - name_s.get_height() // 2))

    def draw_mode_menu(self):
        self.screen.fill(C_DARK)
        t_s = self.title_font.render("SELECT GAMEPLAY DIFFICULTY", True, C_GOLD)
        self.screen.blit(t_s, (WIDTH // 2 - t_s.get_width() // 2, 60))
        
        m_pos = pygame.mouse.get_pos()
        card_w, card_h = 240, 380
        start_y = 180
        gap = 45
        total_w = (3 * card_w) + (2 * gap)
        start_x = (WIDTH - total_w) // 2
        
        for i, m_data in self.modes.items():
            cx = start_x + (i - 1) * (card_w + gap)
            card_rect = pygame.Rect(cx, start_y, card_w, card_h)
            self.mode_buttons[i] = card_rect
            
            is_hov = card_rect.collidepoint(m_pos)
            b_color = (255, 235, 100) if is_hov else (160, 140, 100)
            
            pygame.draw.rect(self.screen, m_data["card"], card_rect, border_radius=18)
            pygame.draw.rect(self.screen, b_color, card_rect, 3, border_radius=18)
            
            w_rect = pygame.Rect(cx + 15, start_y + 15, card_w - 30, 130)
            pygame.draw.rect(self.screen, m_data["bg"], w_rect, border_radius=10)
            
            n_s = self.font.render(m_data["name"], True, C_WHITE)
            d_s = self.font.render(m_data["desc"], True, C_YELLOW)
            
            self.screen.blit(n_s, (cx + 25, start_y + 170))
            self.screen.blit(d_s, (cx + 25, start_y + 210))
            
            btn = pygame.Rect(cx + 25, start_y + 300, card_w - 50, 45)
            btn_col = C_GOLD if is_hov else (210, 165, 45)
            pygame.draw.rect(self.screen, btn_col, btn, border_radius=12)
            
            sel_s = self.btn_font.render("LAUNCH", True, C_DARK)
            self.screen.blit(sel_s, (btn.centerx - sel_s.get_width() // 2, btn.centery - sel_s.get_height() // 2))

    def start_game_mode(self, mode_idx):
        m = self.modes[mode_idx]
        self.current_mode_name = m["name"]
        self.lives = m["lives"]
        self.bg_color = m["bg"]
        self.tree_color = m["tree"]
        self.gold = 0
        self.current_level = 1
        
        self.player_rect = pygame.Rect(WORLD_SIZE // 2, WORLD_SIZE // 2, 50, 70)
        self.camera_offset = pygame.Vector2(0, 0)
        
        self.trees = [
            pygame.Rect(random.randint(0, WORLD_SIZE), random.randint(0, WORLD_SIZE), 40, 40) 
            for _ in range(90)
        ]
        self.respawn_chests()
        self.state = "EXPLORING"

    def respawn_chests(self):
        self.chests = [
            pygame.Rect(random.randint(200, WORLD_SIZE - 200), random.randint(200, WORLD_SIZE - 200), 60, 45) 
            for _ in range(5)
        ]

    def check_answer(self):
        ans = self.user_input.lower().strip()
        q_info = LEVEL_DATA[self.current_level]
        correct_target = q_info["a"]
        
        is_correct = False
        if self.current_level == 5:
            if "break" in ans or "dead" in ans or "organism" in ans:
                is_correct = True
        elif self.current_level == 9:
            if "habitat" in ans or "species" in ans or "provide" in ans:
                is_correct = True
        else:
            if ans == correct_target:
                is_correct = True
                
        if is_correct:
            reward = q_info["r"]
            self.gold += reward
            self.feedback = f"CORRECT! +{reward} GOLD"
            self.feedback_timer = pygame.time.get_ticks()
            self.state = "LEVEL_VICTORY"
        else:
            self.lives -= 1
            self.feedback = "WRONG ANSWER! LIFE LOST."
            self.feedback_timer = pygame.time.get_ticks()
            if self.lives <= 0:
                self.state = "GAME_OVER"
            else:
                self.state = "EXPLORING"
        self.user_input = ""

    def draw_level_victory(self):
        self.screen.fill(C_DARK)
        
        v_s = self.title_font.render("✨ VICTORY! ✨", True, C_GOLD)
        self.screen.blit(v_s, (WIDTH // 2 - v_s.get_width() // 2, 160))
        
        txt = f"Level {self.current_level} Answered Correctly!"
        txt_s = self.font.render(txt, True, C_WHITE)
        self.screen.blit(txt_s, (WIDTH // 2 - txt_s.get_width() // 2, 250))
        
        g_txt = f"Current Wealth: {self.gold} Gold"
        g_s = self.font.render(g_txt, True, C_YELLOW)
        self.screen.blit(g_s, (WIDTH // 2 - g_s.get_width() // 2, 310))
        
        m_pos = pygame.mouse.get_pos()
        is_hov = self.next_btn.collidepoint(m_pos)
        b_col = C_GREEN if is_hov else (0, 180, 80)
        pygame.draw.rect(self.screen, b_col, self.next_btn, border_radius=12)
        
        btn_txt = "NEXT LEVEL" if self.current_level < 10 else "FINAL RESULTS"
        b_s = self.btn_font.render(btn_txt, True, C_DARK)
        self.screen.blit(b_s, (self.next_btn.centerx - b_s.get_width() // 2, self.next_btn.centery - b_s.get_height() // 2))

    def draw_final_victory(self):
        self.screen.fill(C_DARK)
        v_s = self.title_font.render("🏆 GRAND VICTORY 🏆", True, C_GOLD)
        self.screen.blit(v_s, (WIDTH // 2 - v_s.get_width() // 2, 200))
        
        msg = f"Explorer {self.player_name} conquered all 10 Levels!"
        m_s = self.font.render(msg, True, C_WHITE)
        self.screen.blit(m_s, (WIDTH // 2 - m_s.get_width() // 2, 290))
        
        g_s = self.title_font.render(f"TOTAL SCORE: {self.gold} GOLD", True, C_YELLOW)
        self.screen.blit(g_s, (WIDTH // 2 - g_s.get_width() // 2, 360))
        
        r_s = self.font.render("Press ENTER to return to Home Page", True, C_GRAY)
        self.screen.blit(r_s, (WIDTH // 2 - r_s.get_width() // 2, 510))

    def draw_game_over(self):
        self.screen.fill(C_DARK)
        o_s = self.title_font.render("💀 GAME OVER 💀", True, C_RED)
        self.screen.blit(o_s, (WIDTH // 2 - o_s.get_width() // 2, 220))
        
        r_s = self.font.render("Press ENTER to return to Home Page", True, C_WHITE)
        self.screen.blit(r_s, (WIDTH // 2 - r_s.get_width() // 2, 340))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    pygame.quit()
                    sys.exit()
                
                if self.state == "HOME_MENU" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.start_btn.collidepoint(event.pos):
                        self.state = "NAME_INPUT"
                        
                elif self.state == "NAME_INPUT" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if len(self.player_name.strip()) > 0:
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
                
                elif self.state == "QUIZ" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.check_answer()
                    elif event.key == pygame.K_BACKSPACE:
                        self.user_input = self.user_input[:-1]
                    else:
                        if len(self.user_input) < 40:
                            self.user_input += event.unicode
                            
                elif self.state == "LEVEL_VICTORY" and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.next_btn.collidepoint(event.pos):
                        if self.current_level >= 10:
                            self.state = "FINAL_VICTORY"
                        else:
                            self.current_level += 1
                            self.respawn_chests()
                            self.state = "EXPLORING"
                            
                elif self.state in ["FINAL_VICTORY", "GAME_OVER"] and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.player_name = ""
                        self.state = "HOME_MENU"

            if self.state == "EXPLORING":
                keys = pygame.key.get_pressed()
                spd = 8
                if keys[pygame.K_LEFT]: self.player_rect.x -= spd
                if keys[pygame.K_RIGHT]: self.player_rect.x += spd
                if keys[pygame.K_UP]: self.player_rect.y -= spd
                if keys[pygame.K_DOWN]: self.player_rect.y += spd
                
                # Keep within bounds
                self.player_rect.x = max(0, min(self.player_rect.x, WORLD_SIZE - 50))
                self.player_rect.y = max(0, min(self.player_rect.y, WORLD_SIZE - 70))
                
                self.camera_offset.x = -(self.player_rect.centerx - WIDTH // 2)
                self.camera_offset.y = -(self.player_rect.centery - HEIGHT // 2)

                for chest in self.chests[:]:
                    if self.player_rect.colliderect(chest):
                        self.state = "QUIZ"
                        self.chests.remove(chest)

            # --- Graphics Pipeline Routing ---
            if self.state == "HOME_MENU":
                self.draw_home_menu()
            elif self.state == "NAME_INPUT":
                self.draw_name_input()
            elif self.state == "MODE_MENU":
                self.draw_mode_menu()
            elif self.state == "LEVEL_VICTORY":
                self.draw_level_victory()
            elif self.state == "FINAL_VICTORY":
                self.draw_final_victory()
            elif self.state == "GAME_OVER":
                self.draw_game_over()
            else:
                self.screen.fill(self.bg_color)
                for t in self.trees:
                    cx = t.x + int(self.camera_offset.x)
                    cy = t.y + int(self.camera_offset.y)
                    pygame.draw.circle(self.screen, self.tree_color, (cx, cy), 40)
                    
                for c in self.chests:
                    cx = c.left + int(self.camera_offset.x)
                    cy = c.top + int(self.camera_offset.y)
                    pygame.draw.rect(self.screen, (255, 200, 0), ((cx, cy), (50, 35)))

                p_pos = self.player_rect.topleft + self.camera_offset
                pygame.draw.rect(self.screen, C_BLUE, (p_pos.x, p_pos.y, 50, 60), border_radius=8)
                pygame.draw.circle(self.screen, (255, 220, 180), (int(p_pos.x + 25), int(p_pos.y - 12)), 22)

                if self.state == "QUIZ":
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 210))
                    self.screen.blit(overlay, (0, 0))
                    
                    pygame.draw.rect(self.screen, (50, 50, 75), (100, 180, 800, 340), border_radius=15)
                    pygame.draw.rect(self.screen, C_GOLD, (100, 180, 800, 340), 3, border_radius=15)
                    
                    q_data = LEVEL_DATA[self.current_level]
                    header_str = f"LEVEL {self.current_level} - {q_data['subj']}"
                    self.screen.blit(self.font.render(header_str, True, C_GOLD), (140, 210))
                    self.screen.blit(self.font.render(q_data["q"], True, C_WHITE), (140, 260))
                    
                    in_str = f"Your Answer: {self.user_input}"
                    self.screen.blit(self.font.render(in_str, True, C_YELLOW), (140, 340))
                    
                    h_str = "(Type response line and hit ENTER to submit answer)"
                    self.screen.blit(self.font.render(h_str, True, C_GRAY), (140, 440))

                # Display HUD Panel
                g_txt = self.font.render(f"GOLD: {self.gold}", True, C_GOLD)
                l_txt = self.font.render(f"LIVES: {self.lives}", True, C_RED)
                lvl_txt = self.font.render(f"LEVEL: {self.current_level}/10", True, C_GREEN)
                n_txt = self.font.render(f"EXPLORER: {self.player_name}", True, C_WHITE)
                
                self.screen.blit(g_txt, (20, 20))
                self.screen.blit(l_txt, (20, 55))
                self.screen.blit(lvl_txt, (180, 20))
                self.screen.blit(n_txt, (WIDTH - n_txt.get_width() - 20, 20))
            
            # Draw overlay banner alerts
            now = pygame.time.get_ticks()
            if now - self.feedback_timer < 2500 and self.feedback:
                f_msg = self.font.render(self.feedback, True, C_WHITE)
                self.screen.blit(f_msg, (WIDTH // 2 - f_msg.get_width() // 2, 130))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = BrainTrekGame()
    game.run()