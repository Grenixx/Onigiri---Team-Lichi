import os
os.environ['SDL_VIDEO_CENTERED'] = '1'
import sys
import pygame
from game import Game

pygame.init()

from screeninfo import get_monitors

monitors = get_monitors()
for m in monitors:
    if m.is_primary:
        monitor = m
        break

WIDTH, HEIGHT = monitor.width, monitor.height

FPS = 60
BG_COLOR = (30, 30, 40)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
TEXT_COLOR = (255, 255, 255)
FONT_NAME = None  
FONT_SIZE = 36
CONTROLS={"LEFT":pygame.K_q,"RIGHT":pygame.K_s,"JUMP":pygame.K_SPACE,"DASH":pygame.K_LSHIFT,"CHANGE ARM":pygame.K_TAB}
wait_key=False
action_changing=None



screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Menu")
clock = pygame.time.Clock()
font = pygame.font.Font(FONT_NAME, FONT_SIZE)
BACKGROUND = pygame.image.load("data\images\menuImage\Background\\backgroundtemp.png").convert()
BACKGROUND_DIM = pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT))

def render_text(text, font, color):
    return font.render(text, True, color)


class Button:
    def __init__(self, rect, text, callback, font,
                 color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
                 text_color=TEXT_COLOR):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self._render_label()

    def _render_label(self):
        self.label = render_text(self.text, self.font, self.text_color)
        self.label_rect = self.label.get_rect(center=self.rect.center)

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        surface.blit(self.label, self.label_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if callable(self.callback):
                    self.callback()



class Menu:
    def __init__(self, title, items, font, spacing=16):
        self.title = title
        self.font = font
        self.items = []
        self.items_data = items
        self.spacing = spacing
        self.selected = 0
        self.visible = True
        self._build_buttons(items)

    def rebuild(self):
        self.items.clear()
        self._build_buttons(self.items_data)

    def _build_buttons(self, items):
        button_w = 300
        button_h = 60
        total_h = len(items) * button_h + (len(items) - 1) * self.spacing
        start_y = (HEIGHT - total_h) // 2
        x = (WIDTH - button_w) // 2
        for i, (text, callback) in enumerate(items):
            y = start_y + i * (button_h + self.spacing)
            btn = Button((x, y, button_w, button_h), text, callback, self.font)
            self.items.append(btn)

    def draw(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))
        title_font = pygame.font.Font(FONT_NAME, FONT_SIZE + 10)
        title_surf = title_font.render(self.title, True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT * 0.2))
        surface.blit(title_surf, title_rect)
        for i, btn in enumerate(self.items):
            btn.hovered = (i == self.selected)
            btn.draw(surface)

    def handle_event(self, event):
        for btn in self.items:
            btn.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                selected_btn = self.items[self.selected]
                if callable(selected_btn.callback):
                    selected_btn.callback()




def start_game():
    in_game = True
    game = Game(FPS, [WIDTH,HEIGHT])
    game.run()
    while in_game:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                in_game = False
    


def open_options():
    global active_menu
    active_menu = options_menu


def quit_game():
    pygame.quit()
    sys.exit()
  

def resize(new_width, new_height):
    global WIDTH,HEIGHT, screen, BACKGROUND_DIM
    WIDTH,HEIGHT = new_width,new_height
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    BACKGROUND_DIM = pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT))
    for menu in lst_menu:
        menu.rebuild()
    

def rebinding(action):
    global wait_key, action_changing
    wait_key = True
    action_changing = action
    print(CONTROLS)
    
def refps(fps_value):
    global FPS
    FPS=fps_value


main_menu = Menu("Main Menu", [("START GAME", start_game),("OPTIONS", open_options),("QUIT GAME", quit_game),], font)
options_menu = Menu("Options", [("Audio",None),("Keyboards",lambda: set_active_menu(keyboard_menu)),("Graphics",lambda: set_active_menu(graphics_menu)),("FPS",lambda: set_active_menu(fps_menu)),("Back", lambda: set_active_menu(main_menu)),], font)
keyboard_menu = Menu("Keyboard", [(f"Jump : {CONTROLS['JUMP']}",lambda: rebinding("JUMP")),(f"Change Arm : {CONTROLS['CHANGE ARM']}",lambda: rebinding("ATTACK")),(f"Dash : {CONTROLS['DASH']}",lambda: rebinding("DODGE")),(f"left : {CONTROLS['LEFT']}",lambda: rebinding("LEFT")),(f"Right : {CONTROLS['RIGHT']}",lambda: rebinding("RIGHT")),("Back", lambda: set_active_menu(options_menu))],font)
graphics_menu = Menu("Graphics",[("3840-2160",lambda: resize(3840, 2160)),("2560-1440",lambda: resize(2560, 1440)),("1920-1080",lambda: resize(1920, 1080)),("1680-1050",lambda: resize(1680, 1050)),("1280-720",lambda: resize(1280,720)),("1024-768",lambda: resize(1024,768)),("800-600",lambda: resize(800,600)),("Back", lambda: set_active_menu(options_menu))],font)
fps_menu = Menu("FPS",[("30 FPS",lambda: refps(30)),("45 FPS",lambda: refps(45)),("60 FPS",lambda: refps(60)),("120 FPS",lambda: refps(120)),("144 FPS",lambda: refps(144)),("165 FPS",lambda: refps(165)),("180 FPS",lambda: refps(180)),("240 FPS",lambda: refps(240)),("UNCAPPED FPS",lambda: refps(100000000)),("Back", lambda: set_active_menu(options_menu))],font)
lst_menu = [main_menu,options_menu,keyboard_menu,graphics_menu]


def set_active_menu(menu):
    global active_menu, last_menu
    last_menu = active_menu 
    active_menu = menu
    
    

active_menu = main_menu
last_menu = main_menu


def main():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                set_active_menu(last_menu)
            global wait_key, action_changing
            if wait_key and event.type == pygame.KEYDOWN:
                CONTROLS[action_changing] = event.key
                wait_key = False
                action_changing = None
                continue
            if active_menu:
                active_menu.handle_event(event)
        screen.blit(BACKGROUND_DIM, (0, 0))
        if active_menu:
            active_menu.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)



main() 
