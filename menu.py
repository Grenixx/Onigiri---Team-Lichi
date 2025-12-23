import sys
import pygame

pygame.init()
WIDTH, HEIGHT = 1920, 1080
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
        self.spacing = spacing
        self.selected = 0
        self.visible = True
        self._build_buttons(items)

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
    while in_game:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                in_game = False
        screen.fill((10, 20, 30))
        label = font.render("Game screen - press ESC to go back", True, (200, 200, 200))
        screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()
        clock.tick(FPS)


def open_options():
    global active_menu
    active_menu = options_menu


def quit_game():
    pygame.quit()
    sys.exit()


def toggle_dummy_setting():
    toggle_dummy_setting.state = not getattr(toggle_dummy_setting, 'state', False)
    text = f"Sound: {'On' if toggle_dummy_setting.state else 'Off'}"
    options_menu.items[0].text = text
    options_menu.items[0]._render_label()

def resize(new_width, new_height):
    global WIDTH,HEIGHT, screen
    WIDTH,HEIGHT = new_width,new_height
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    last_menu.draw(screen)
    

def rebinding(action):
    global wait_key, action_changing
    wait_key = True
    action_changing = action
    
    



main_menu = Menu("Main Menu", [("START GAME", start_game),("OPTIONS", open_options),("QUIT GAME", quit_game),], font)
options_menu = Menu("Options", [("Audio",None),("Keyboards",lambda: set_active_menu(keyboard_menu)),("Graphics",lambda: set_active_menu(graphics_menu)),("Back", lambda: set_active_menu(main_menu)),], font)
keyboard_menu = Menu("Keyboard", [("Jump",None),("Attack",None),("Dodge",None),("left",None),("Right",None),("Back", lambda: set_active_menu(options_menu))],font)
graphics_menu = Menu("Graphics",[("1920-1080",lambda: resize(1920, 1080)),("1680-1050",lambda: resize(1680, 1050)),("1280-720",lambda: resize(1280,720)),("1024-768",lambda: resize(1024,768)),("800-600",lambda: resize(800,600)),("Back", lambda: set_active_menu(options_menu))],font)



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
        screen.fill(BG_COLOR)
        if active_menu:
            active_menu.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)



main() 
