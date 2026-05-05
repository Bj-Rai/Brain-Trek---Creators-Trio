import pygame
import sys
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import math

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
LIGHT_GREEN = (144, 238, 144)
BLUE = (135, 206, 235)
DARK_BLUE = (25, 25, 112)
YELLOW = (255, 215, 0)
ORANGE = (255, 165, 0)
RED = (220, 20, 60)
PURPLE = (128, 0, 128)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
LIGHT_GRAY = (211, 211, 211)
CREAM = (255, 253, 240)
GOLD = (255, 215, 0)

class GameState(Enum):
    START_SCREEN = 1
    MAP_SCREEN = 2
    LOCATION_INFO = 3
    TASK_SCREEN = 4
    QUIZ_SCREEN = 5
    SUCCESS_SCREEN = 6
    GAME_OVER = 7
    WIN_SCREEN = 8
    INSTRUCTIONS = 9

@dataclass
class Location:
    id: str
    name: str
    x: int
    y: int
    radius: int
    description: str
    history: str
    facts: List[str]
    task_instruction: str
    task_options: List[str]
    correct_task: int
    quiz_questions: List[Dict]
    points_reward: int
    unlocked: bool = False
    completed: bool = False

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = color
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen):
        self.current_color = self.hover_color if self.is_hovered() else self.color
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 3, border_radius=10)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_hovered(self):
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

class ThreadsOfTimeGUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Threads of Time - A Journey Through Bhutan")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = GameState.START_SCREEN
        self.player_name = ""
        self.points = 100
        self.current_location = None
        self.current_quiz_question = 0
        self.name_input = ""
        self.name_input_active = False
        self.message = ""
        self.message_timer = 0
        self.transition_alpha = 0
        self.transitioning = False
        self.transition_target = None
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 48)
        self.normal_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.tiny_font = pygame.font.Font(None, 24)
        
        # Load or create Bhutan map shape
        self.bhutan_outline = self.create_bhutan_outline()
        
        # Initialize locations with positions on the map
        self.locations = self.initialize_locations()
        
        # Buttons
        self.buttons = {}
        self.create_buttons()
    
    def create_bhutan_outline(self):
        """Create a simplified outline of Bhutan's map shape"""
        # Bhutan is roughly rectangular/elongated, wider in the middle
        # Coordinates are approximate relative positions
        points = [
            (300, 250), (400, 220), (550, 210), (700, 220), (850, 240),
            (950, 280), (1000, 330), (1020, 400), (1000, 470),
            (950, 520), (850, 560), (700, 580), (550, 590),
            (400, 580), (300, 540), (220, 480), (180, 400),
            (220, 320), (300, 250)
        ]
        return points
    
    def initialize_locations(self):
        """Initialize Bhutan locations with map positions"""
        locations = {
            "paro": Location(
                id="paro",
                name="Paro Taktsang",
                x=280, y=420,
                radius=25,
                description="A sacred Buddhist site built into a cliff 900 meters above the Paro Valley.",
                history="Built in 1692 around the cave where Guru Rinpoche meditated for 3 months.",
                facts=["The monastery is at 3,120 meters altitude", 
                      "It takes 2-3 hours to hike up",
                      "No photography allowed inside"],
                task_instruction="Climb the 700 steps to reach the monastery. Choose your pace:",
                task_options=["Rush quickly", "Take steady pace", "Rest frequently"],
                correct_task=1,
                quiz_questions=[
                    {"question": "In which year was Tiger's Nest built?",
                     "options": ["1592", "1692", "1792", "1892"], "correct": 1},
                    {"question": "How many meters above the valley is the monastery?",
                     "options": ["500m", "700m", "900m", "1100m"], "correct": 2}
                ],
                points_reward=25,
                unlocked=True
            ),
            "punakha": Location(
                id="punakha",
                name="Punakha Dzong",
                x=520, y=380,
                radius=25,
                description="The second oldest and second largest dzong in Bhutan.",
                history="Built in 1637 by Shabdrung Ngawang Namgyal. It served as the capital until 1955.",
                facts=["Known as the Palace of Great Happiness",
                      "Houses sacred relics of Buddhism",
                      "Survived floods and fires for centuries"],
                task_instruction="Cross the Bazam (bamboo bridge) over the river. How do you proceed?",
                task_options=["Run across quickly", "Walk carefully holding the rails", "Jump from plank to plank"],
                correct_task=1,
                quiz_questions=[
                    {"question": "Who built Punakha Dzong?",
                     "options": ["Guru Rinpoche", "Shabdrung Ngawang Namgyal", "King Jigme", "Buddha Dordenma"], 
                     "correct": 1},
                    {"question": "What does Punakha Dzong mean?",
                     "options": ["Palace of Great Happiness", "Fortress of Peace", "Temple of Wisdom", "Monastery of Light"],
                     "correct": 0}
                ],
                points_reward=25
            ),
            "thimphu": Location(
                id="thimphu",
                name="Buddha Dordenma",
                x=620, y=320,
                radius=25,
                description="A gigantic Shakyamuni Buddha statue overlooking Thimphu valley.",
                history="Completed in 2015, the statue is 51.5 meters tall and made of bronze.",
                facts=["Contains 125,000 smaller Buddha statues inside",
                      "Weighs 500 tons of bronze",
                      "Visible from across the valley"],
                task_instruction="Climb the hill to reach the Buddha statue. What's your strategy?",
                task_options=["Take a taxi all the way", "Hike up the mountain trail", "Take the scenic walking path"],
                correct_task=2,
                quiz_questions=[
                    {"question": "How tall is the Buddha Dordenma statue?",
                     "options": ["25.5m", "41.5m", "51.5m", "61.5m"], "correct": 2},
                    {"question": "How many smaller Buddha statues are inside?",
                     "options": ["12,500", "52,500", "125,000", "250,000"], "correct": 2}
                ],
                points_reward=25
            ),
            "dochula": Location(
                id="dochula",
                name="Dochula Pass",
                x=750, y=350,
                radius=25,
                description="A mountain pass at 3,100m with 108 memorial chortens.",
                history="Built in 2003 to honor fallen soldiers in the fight against insurgents.",
                facts=["108 Druk Wangyal Khang Zhang Chortens",
                      "View of Gangkhar Puensum (highest unclimbed peak)",
                      "Hosts annual Dochula Druk Wangyal Festival"],
                task_instruction="You're at high altitude. How do you handle it?",
                task_options=["Ignore and keep moving", "Acclimatize slowly, drink water", "Rush to finish quickly"],
                correct_task=1,
                quiz_questions=[
                    {"question": "How many chortens are at Dochula Pass?",
                     "options": ["88", "98", "108", "118"], "correct": 2},
                    {"question": "What is the altitude of Dochula Pass?",
                     "options": ["2,100m", "3,100m", "4,100m", "5,100m"], "correct": 1}
                ],
                points_reward=25
            )
        }
        return locations
    
    def create_buttons(self):
        """Create UI buttons"""
        # Start screen buttons
        self.buttons['play'] = Button(450, 400, 300, 60, "PLAY GAME", GREEN, LIGHT_GREEN, WHITE)
        self.buttons['instructions'] = Button(450, 480, 300, 60, "HOW TO PLAY", BLUE, LIGHT_GRAY, WHITE)
        self.buttons['exit'] = Button(450, 560, 300, 60, "EXIT", RED, LIGHT_GRAY, WHITE)
        
        # Map screen buttons
        self.buttons['back_to_menu'] = Button(50, 700, 200, 50, "Main Menu", GRAY, LIGHT_GRAY, WHITE)
        self.buttons['view_progress'] = Button(950, 700, 200, 50, "View Progress", BLUE, LIGHT_GRAY, WHITE)
        
        # Task/Quiz buttons
        self.buttons['option1'] = Button(350, 350, 500, 60, "", BLUE, LIGHT_GRAY, WHITE)
        self.buttons['option2'] = Button(350, 430, 500, 60, "", BLUE, LIGHT_GRAY, WHITE)
        self.buttons['option3'] = Button(350, 510, 500, 60, "", BLUE, LIGHT_GRAY, WHITE)
        self.buttons['continue'] = Button(450, 650, 300, 60, "Continue", GREEN, LIGHT_GREEN, WHITE)
        self.buttons['retry'] = Button(450, 650, 300, 60, "Try Again", ORANGE, YELLOW, WHITE)
        self.buttons['next_question'] = Button(450, 650, 300, 60, "Next Question", GREEN, LIGHT_GREEN, WHITE)
    
    def draw_bhutan_map(self):
        """Draw the outline of Bhutan"""
        # Draw filled shape
        pygame.draw.polygon(self.screen, LIGHT_GREEN, self.bhutan_outline)
        # Draw outline
        pygame.draw.polygon(self.screen, DARK_GREEN, self.bhutan_outline, 4)
        
        # Add some mountain decorations
        mountains = [(350, 300), (550, 280), (750, 310), (900, 350)]
        for mx, my in mountains:
            pygame.draw.polygon(self.screen, WHITE, [
                (mx, my), (mx + 30, my - 40), (mx + 60, my)
            ])
            pygame.draw.polygon(self.screen, GRAY, [
                (mx, my), (mx + 30, my - 40), (mx + 60, my)
            ], 2)
    
    def draw_locations(self):
        """Draw location markers on the map"""
        for loc_id, location in self.locations.items():
            # Draw connection lines between locations
            loc_list = list(self.locations.values())
            idx = loc_list.index(location)
            if idx > 0:
                prev_loc = loc_list[idx - 1]
                if location.unlocked and prev_loc.unlocked:
                    pygame.draw.line(self.screen, DARK_GREEN, 
                                   (prev_loc.x, prev_loc.y), 
                                   (location.x, location.y), 3)
            
            # Draw location circle
            color = GOLD if location.completed else (GREEN if location.unlocked else GRAY)
            pygame.draw.circle(self.screen, color, (location.x, location.y), location.radius + 5)
            pygame.draw.circle(self.screen, BLACK, (location.x, location.y), location.radius + 5, 3)
            pygame.draw.circle(self.screen, WHITE, (location.x, location.y), location.radius)
            
            # Draw marker icon
            font = self.tiny_font
            marker = "✓" if location.completed else ("🔓" if location.unlocked else "🔒")
            text = font.render(marker, True, BLACK)
            text_rect = text.get_rect(center=(location.x, location.y))
            self.screen.blit(text, text_rect)
            
            # Draw location name
            name_font = self.small_font
            name_text = name_font.render(location.name, True, BLACK)
            name_rect = name_text.get_rect(center=(location.x, location.y + 40))
            self.screen.blit(name_text, name_rect)
    
    def draw_start_screen(self):
        """Draw the start screen"""
        self.screen.fill(CREAM)
        
        # Title
        title = self.title_font.render("THREADS OF TIME", True, DARK_GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.subtitle_font.render("A Journey Through Bhutan", True, BROWN)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Decorative elements
        pygame.draw.rect(self.screen, GOLD, (350, 270, 500, 4), border_radius=2)
        
        # Features
        features = [
            "🏔️ Explore Historic Places of Bhutan",
            "📚 Learn History & Geography",
            "🎯 Solve Tasks & Challenges",
            "⭐ Earn Points & Unlock Locations",
            "📝 Answer Quizzes to Progress"
        ]
        
        for i, feature in enumerate(features):
            text = self.normal_font.render(feature, True, DARK_BLUE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 320 + i * 50))
            self.screen.blit(text, text_rect)
        
        # Draw buttons
        self.buttons['play'].draw(self.screen)
        self.buttons['instructions'].draw(self.screen)
        self.buttons['exit'].draw(self.screen)
    
    def draw_map_screen(self):
        """Draw the interactive map screen"""
        self.screen.fill(CREAM)
        
        # Header
        header = self.subtitle_font.render("BHUTAN MAP", True, DARK_GREEN)
        self.screen.blit(header, (50, 30))
        
        # Player info
        info_text = f"Player: {self.player_name} | Points: {self.points} ⭐"
        info = self.normal_font.render(info_text, True, DARK_BLUE)
        self.screen.blit(info, (50, 80))
        
        # Draw Bhutan map
        self.draw_bhutan_map()
        
        # Draw locations
        self.draw_locations()
        
        # Instructions
        instr = self.small_font.render("Click on an unlocked location (green circles) to explore!", True, BROWN)
        self.screen.blit(instr, (350, 650))
        
        # Buttons
        self.buttons['back_to_menu'].draw(self.screen)
        self.buttons['view_progress'].draw(self.screen)
    
    def draw_location_info(self):
        """Draw location information screen"""
        self.screen.fill(CREAM)
        
        if not self.current_location:
            return
        
        loc = self.locations[self.current_location]
        
        # Title
        title = self.subtitle_font.render(loc.name, True, DARK_GREEN)
        self.screen.blit(title, (50, 30))
        
        # Description box
        pygame.draw.rect(self.screen, LIGHT_GREEN, (50, 100, 1100, 150), border_radius=10)
        pygame.draw.rect(self.screen, DARK_GREEN, (50, 100, 1100, 150), 3, border_radius=10)
        
        desc_text = self.normal_font.render("📖 LOCATION INFORMATION", True, DARK_BLUE)
        self.screen.blit(desc_text, (70, 110))
        
        desc_lines = self.wrap_text(loc.description, 100)
        for i, line in enumerate(desc_lines):
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (70, 145 + i * 30))
        
        # History
        hist_y = 270
        pygame.draw.rect(self.screen, LIGHT_GRAY, (50, hist_y, 530, 200), border_radius=10)
        pygame.draw.rect(self.screen, GRAY, (50, hist_y, 530, 200), 3, border_radius=10)
        
        hist_title = self.normal_font.render("📜 HISTORY", True, DARK_BLUE)
        self.screen.blit(hist_title, (70, hist_y + 10))
        
        hist_lines = self.wrap_text(loc.history, 60)
        for i, line in enumerate(hist_lines):
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (70, hist_y + 45 + i * 28))
        
        # Facts
        facts_y = 270
        pygame.draw.rect(self.screen, GOLD, (620, facts_y, 530, 200), border_radius=10)
        pygame.draw.rect(self.screen, ORANGE, (620, facts_y, 530, 200), 3, border_radius=10)
        
        facts_title = self.normal_font.render("💡 INTERESTING FACTS", True, DARK_BLUE)
        self.screen.blit(facts_title, (640, facts_y + 10))
        
        for i, fact in enumerate(loc.facts):
            text = self.small_font.render(f"• {fact}", True, BLACK)
            self.screen.blit(text, (640, facts_y + 45 + i * 35))
        
        # Continue button
        self.buttons['continue'].draw(self.screen)
    
    def draw_task_screen(self):
        """Draw task screen"""
        self.screen.fill(CREAM)
        
        if not self.current_location:
            return
        
        loc = self.locations[self.current_location]
        
        # Title
        title = self.subtitle_font.render("📋 YOUR TASK", True, DARK_GREEN)
        self.screen.blit(title, (50, 30))
        
        # Task instruction
        pygame.draw.rect(self.screen, LIGHT_BLUE if 'LIGHT_BLUE' in dir() else (173, 216, 230), 
                        (50, 120, 1100, 150), border_radius=10)
        pygame.draw.rect(self.screen, BLUE, (50, 120, 1100, 150), 3, border_radius=10)
        
        instr_lines = self.wrap_text(loc.task_instruction, 100)
        for i, line in enumerate(instr_lines):
            text = self.normal_font.render(line, True, DARK_BLUE)
            self.screen.blit(text, (70, 140 + i * 40))
        
        # Options
        for i, option in enumerate(loc.task_options):
            self.buttons[f'option{i+1}'].text = f"{i+1}. {option}"
            self.buttons[f'option{i+1}'].draw(self.screen)
    
    def draw_quiz_screen(self):
        """Draw quiz screen"""
        self.screen.fill(CREAM)
        
        if not self.current_location:
            return
        
        loc = self.locations[self.current_location]
        question = loc.quiz_questions[self.current_quiz_question]
        
        # Title
        title_text = f"📝 QUIZ - Question {self.current_quiz_question + 1}/{len(loc.quiz_questions)}"
        title = self.subtitle_font.render(title_text, True, DARK_GREEN)
        self.screen.blit(title, (50, 30))
        
        # Question
        pygame.draw.rect(self.screen, LIGHT_GRAY, (50, 120, 1100, 120), border_radius=10)
        pygame.draw.rect(self.screen, GRAY, (50, 120, 1100, 120), 3, border_radius=10)
        
        q_lines = self.wrap_text(question['question'], 100)
        for i, line in enumerate(q_lines):
            text = self.normal_font.render(line, True, BLACK)
            self.screen.blit(text, (70, 140 + i * 40))
        
        # Options
        for i, option in enumerate(question['options']):
            self.buttons[f'option{i+1}'].text = f"{i+1}. {option}"
            self.buttons[f'option{i+1}'].draw(self.screen)
    
    def draw_success_screen(self):
        """Draw success/completion screen"""
        self.screen.fill(CREAM)
        
        if not self.current_location:
            return
        
        loc = self.locations[self.current_location]
        
        # Success message
        title = self.title_font.render("🎉 EXCELLENT!", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        msg = self.subtitle_font.render("You've mastered this location!", True, DARK_GREEN)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(msg, msg_rect)
        
        # Points earned
        points_text = f"⭐ You earned {loc.points_reward} points!"
        points = self.subtitle_font.render(points_text, True, ORANGE)
        points_rect = points.get_rect(center=(SCREEN_WIDTH // 2, 360))
        self.screen.blit(points, points_rect)
        
        # Current score
        score_text = f"📊 Current Score: {self.points} points"
        score = self.normal_font.render(score_text, True, DARK_BLUE)
        score_rect = score.get_rect(center=(SCREEN_WIDTH // 2, 420))
        self.screen.blit(score, score_rect)
        
        # Continue button
        self.buttons['continue'].draw(self.screen)
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(CREAM)
        
        title = self.title_font.render("💀 GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(title, title_rect)
        
        msg = self.subtitle_font.render("You've run out of points!", True, DARK_BLUE)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, 330))
        self.screen.blit(msg, msg_rect)
        
        score_text = f"Final Score: {self.points}"
        score = self.normal_font.render(score_text, True, BLACK)
        score_rect = score.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(score, score_rect)
        
        # Buttons
        self.buttons['retry'].text = "Try Again"
        self.buttons['retry'].draw(self.screen)
        self.buttons['play'].text = "Main Menu"
        self.buttons['play'].draw(self.screen)
    
    def draw_win_screen(self):
        """Draw victory screen"""
        self.screen.fill(CREAM)
        
        title = self.title_font.render("🏆 CONGRATULATIONS! 🏆", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        msg = self.subtitle_font.render(f"{self.player_name}, you've completed your journey!", True, DARK_GREEN)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(msg, msg_rect)
        
        # Stats
        stats = [
            f"Total Points: {self.points} ⭐",
            f"Locations Explored: {sum(1 for loc in self.locations.values() if loc.completed)}/{len(self.locations)}",
            f"Completion Rate: {sum(1 for loc in self.locations.values() if loc.completed)/len(self.locations)*100:.0f}%"
        ]
        
        for i, stat in enumerate(stats):
            text = self.normal_font.render(stat, True, DARK_BLUE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 320 + i * 60))
            self.screen.blit(text, text_rect)
        
        # Exit button
        self.buttons['exit'].draw(self.screen)
    
    def draw_instructions(self):
        """Draw instructions screen"""
        self.screen.fill(CREAM)
        
        title = self.subtitle_font.render("HOW TO PLAY", True, DARK_GREEN)
        self.screen.blit(title, (50, 50))
        
        instructions = [
            "1. Select locations from the Bhutan map",
            "2. Complete tasks at each location",
            "3. Answer quiz questions correctly",
            "4. Earn points to unlock new locations",
            "5. Don't let your points drop to zero!",
            "",
            "TIPS:",
            "• Read information carefully before tasks",
            "• Choose options wisely",
            "• Learn from Bhutan's rich history"
        ]
        
        for i, instr in enumerate(instructions):
            text = self.normal_font.render(instr, True, DARK_BLUE)
            self.screen.blit(text, (70, 150 + i * 45))
        
        # Back button
        back_btn = Button(50, 650, 200, 60, "Back", BLUE, LIGHT_GRAY, WHITE)
        back_btn.draw(self.screen)
        return back_btn
    
    def wrap_text(self, text, max_width):
        """Wrap text to fit within max_width pixels"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.small_font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def show_message(self, msg, duration=2000):
        """Show temporary message"""
        self.message = msg
        self.message_timer = pygame.time.get_ticks() + duration
    
    def handle_start_screen(self, event):
        """Handle events on start screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttons['play'].is_clicked(event):
                self.name_input_active = True
            elif self.buttons['instructions'].is_clicked(event):
                self.game_state = GameState.INSTRUCTIONS
            elif self.buttons['exit'].is_clicked(event):
                self.running = False
        
        if event.type == pygame.KEYDOWN and self.name_input_active:
            if event.key == pygame.K_RETURN:
                if self.name_input.strip():
                    self.player_name = self.name_input.strip()
                    self.name_input_active = False
                    self.locations["paro"].unlocked = True
                    self.game_state = GameState.MAP_SCREEN
            elif event.key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            else:
                if len(self.name_input) < 20:
                    self.name_input += event.unicode
    
    def handle_map_screen(self, event):
        """Handle events on map screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check location clicks
            for loc_id, location in self.locations.items():
                if location.unlocked:
                    mouse_pos = pygame.mouse.get_pos()
                    dist = math.sqrt((mouse_pos[0] - location.x)**2 + 
                                   (mouse_pos[1] - location.y)**2)
                    if dist <= location.radius:
                        self.current_location = loc_id
                        self.game_state = GameState.LOCATION_INFO
                        return
            
            # Check buttons
            if self.buttons['back_to_menu'].is_clicked(event):
                self.game_state = GameState.START_SCREEN
            elif self.buttons['view_progress'].is_clicked(event):
                self.show_progress_popup()
    
    def handle_location_info(self, event):
        """Handle events on location info screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttons['continue'].is_clicked(event):
                self.game_state = GameState.TASK_SCREEN
    
    def handle_task_screen(self, event):
        """Handle events on task screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.current_location:
                return
            
            loc = self.locations[self.current_location]
            
            for i in range(3):
                if self.buttons[f'option{i+1}'].is_clicked(event):
                    if i == loc.correct_task:
                        self.game_state = GameState.QUIZ_SCREEN
                        self.current_quiz_question = 0
                        self.show_message("Correct! Now answer the quiz!", 2000)
                    else:
                        self.deduct_points(10)
                        self.show_message("Wrong choice! Try again.", 2000)
                        if self.points <= 0:
                            self.game_state = GameState.GAME_OVER
    
    def handle_quiz_screen(self, event):
        """Handle events on quiz screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.current_location:
                return
            
            loc = self.locations[self.current_location]
            question = loc.quiz_questions[self.current_quiz_question]
            
            for i in range(3):
                if self.buttons[f'option{i+1}'].is_clicked(event):
                    if i == question['correct']:
                        self.current_quiz_question += 1
                        if self.current_quiz_question >= len(loc.quiz_questions):
                            # All questions answered
                            loc.completed = True
                            self.points += loc.points_reward
                            self.unlock_next_location()
                            self.game_state = GameState.SUCCESS_SCREEN
                        else:
                            self.show_message("Correct! Next question...", 1500)
                    else:
                        self.show_message("Wrong! Try again.", 2000)
    
    def handle_success_screen(self, event):
        """Handle events on success screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttons['continue'].is_clicked(event):
                self.current_location = None
                self.game_state = GameState.MAP_SCREEN
    
    def handle_game_over(self, event):
        """Handle events on game over screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttons['retry'].is_clicked(event):
                # Reset game
                self.points = 100
                for loc in self.locations.values():
                    loc.unlocked = False
                    loc.completed = False
                self.locations["paro"].unlocked = True
                self.current_location = None
                self.game_state = GameState.MAP_SCREEN
            elif self.buttons['play'].is_clicked(event):
                self.game_state = GameState.START_SCREEN
    
    def handle_win_screen(self, event):
        """Handle events on win screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttons['exit'].is_clicked(event):
                self.running = False
    
    def unlock_next_location(self):
        """Unlock the next location in sequence"""
        loc_ids = list(self.locations.keys())
        current_idx = loc_ids.index(self.current_location)
        
        if current_idx + 1 < len(loc_ids):
            next_loc = loc_ids[current_idx + 1]
            self.locations[next_loc].unlocked = True
            self.show_message(f"🔓 New location unlocked: {self.locations[next_loc].name}!", 3000)
    
    def deduct_points(self, amount):
        """Deduct points from player"""
        self.points -= amount
        self.show_message(f"⚠️ Lost {amount} points! Current: {self.points}", 2000)
    
    def show_progress_popup(self):
        """Show progress information"""
        completed = sum(1 for loc in self.locations.values() if loc.completed)
        unlocked = sum(1 for loc in self.locations.values() if loc.unlocked)
        
        self.show_message(f"Progress: {completed}/{len(self.locations)} completed, "
                         f"{unlocked}/{len(self.locations)} unlocked", 3000)
    
    def draw_message(self):
        """Draw temporary message"""
        if self.message and pygame.time.get_ticks() < self.message_timer:
            pygame.draw.rect(self.screen, YELLOW, (300, 50, 600, 50), border_radius=10)
            pygame.draw.rect(self.screen, ORANGE, (300, 50, 600, 50), 3, border_radius=10)
            
            msg_text = self.small_font.render(self.message, True, BLACK)
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, 75))
            self.screen.blit(msg_text, msg_rect)
        else:
            self.message = ""
    
    def draw_name_input(self):
        """Draw name input dialog"""
        if self.name_input_active:
            # Overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            # Input box
            pygame.draw.rect(self.screen, WHITE, (350, 350, 500, 100), border_radius=10)
            pygame.draw.rect(self.screen, GOLD, (350, 350, 500, 100), 4, border_radius=10)
            
            # Prompt
            prompt = self.normal_font.render("Enter your name:", True, BLACK)
            self.screen.blit(prompt, (370, 370))
            
            # Input field
            input_text = self.normal_font.render(self.name_input + "_", True, DARK_BLUE)
            self.screen.blit(input_text, (370, 410))
            
            # Hint
            hint = self.tiny_font.render("Press ENTER to continue", True, GRAY)
            self.screen.blit(hint, (370, 460))
    
    def run(self):
        """Main game loop"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if self.game_state == GameState.START_SCREEN:
                    self.handle_start_screen(event)
                elif self.game_state == GameState.MAP_SCREEN:
                    self.handle_map_screen(event)
                elif self.game_state == GameState.LOCATION_INFO:
                    self.handle_location_info(event)
                elif self.game_state == GameState.TASK_SCREEN:
                    self.handle_task_screen(event)
                elif self.game_state == GameState.QUIZ_SCREEN:
                    self.handle_quiz_screen(event)
                elif self.game_state == GameState.SUCCESS_SCREEN:
                    self.handle_success_screen(event)
                elif self.game_state == GameState.GAME_OVER:
                    self.handle_game_over(event)
                elif self.game_state == GameState.WIN_SCREEN:
                    self.handle_win_screen(event)
                elif self.game_state == GameState.INSTRUCTIONS:
                    back_btn = self.draw_instructions()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if back_btn.is_clicked(event):
                            self.game_state = GameState.START_SCREEN
            
            # Draw current screen
            if self.game_state == GameState.START_SCREEN:
                self.draw_start_screen()
                self.draw_name_input()
            elif self.game_state == GameState.MAP_SCREEN:
                self.draw_map_screen()
            elif self.game_state == GameState.LOCATION_INFO:
                self.draw_location_info()
            elif self.game_state == GameState.TASK_SCREEN:
                self.draw_task_screen()
            elif self.game_state == GameState.QUIZ_SCREEN:
                self.draw_quiz_screen()
            elif self.game_state == GameState.SUCCESS_SCREEN:
                self.draw_success_screen()
            elif self.game_state == GameState.GAME_OVER:
                self.draw_game_over()
            elif self.game_state == GameState.WIN_SCREEN:
                self.draw_win_screen()
            
            # Draw message if any
            self.draw_message()
            
            # Check win condition
            if self.game_state == GameState.MAP_SCREEN:
                if all(loc.completed for loc in self.locations.values()):
                    self.game_state = GameState.WIN_SCREEN
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ThreadsOfTimeGUI()
    game.run()