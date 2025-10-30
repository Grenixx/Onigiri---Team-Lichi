# ps4_controller_square.py
import sys
import math
import pygame

# ---------- Configuration ----------
SCREEN_SIZE = (800, 600)
BG_COLOR = (30, 30, 30)
SQUARE_SIZE = 50
SPEED = 300  # pixels / seconde (max speed)
DEADZONE = 0.15  # zone morte pour axes

# ---------- Init Pygame ----------
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Pygame + PS4 Controller : carré")
clock = pygame.time.Clock()

# ---------- Init Joystick ----------
pygame.joystick.init()
joystick = None

if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Manette détectée : {joystick.get_name()}")
    print(f"Axes : {joystick.get_numaxes()}, Boutons : {joystick.get_numbuttons()}, Hats : {joystick.get_numhats()}")
else:
    print("Aucune manette détectée. Utilisez le clavier (flèches / WASD) ou branchez une manette.")

# ---------- Helper functions ----------
def apply_deadzone(value, deadzone=DEADZONE):
    """Applique une zone morte et renvoie une valeur normalisée."""
    if abs(value) < deadzone:
        return 0.0
    # Optionnel : re-normaliser la plage pour une transition douce
    sign = 1 if value > 0 else -1
    adjusted = (abs(value) - deadzone) / (1 - deadzone)
    return sign * adjusted

# ---------- Game state ----------
x = SCREEN_SIZE[0] // 2 - SQUARE_SIZE // 2
y = SCREEN_SIZE[1] // 2 - SQUARE_SIZE // 2
color = (200, 60, 60)

# pour afficher l'état des axes/boutons (utile pour debug)
show_debug = True

# ---------- Main loop ----------
running = True
while running:
    dt = clock.tick(60) / 1000.0  # delta time en secondes

    # événements
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # détection de connexion/déconnexion de manette (Pygame 2)
        if event.type == pygame.JOYDEVICEADDED:
            if joystick is None:
                joystick = pygame.joystick.Joystick(event.device_index)
                joystick.init()
                print("Manette branchée :", joystick.get_name())
        if event.type == pygame.JOYDEVICEREMOVED:
            if joystick and joystick.get_instance_id() == event.instance_id:
                print("Manette débranchée :", joystick.get_name())
                joystick = None

        # Exemple : bouton X (souvent bouton 0 sur beaucoup de mappings) change la couleur
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"Joystick button {event.button} down")
            # Ajustez le numéro du bouton si nécessaire (imprimez-les pour vérifier)
            if event.button == 0:  # souvent X / Croix
                color = (60, 200, 60)  # vert
            if event.button == 1:  # souvent cercle
                color = (200, 60, 60)  # rouge
            if event.button == 2:  # triangle
                color = (60, 60, 200)  # bleu

    # ---------- Lecture entrée (manette ou clavier) ----------
    move_x = 0.0
    move_y = 0.0

    if joystick:
        # axes communs : axe 0 = stick gauche X, axe 1 = stick gauche Y
        # mais cela peut varier — on imprime plus bas pour debug
        try:
            raw_x = joystick.get_axis(0)
            raw_y = joystick.get_axis(1)
        except Exception:
            raw_x, raw_y = 0.0, 0.0

        ax = apply_deadzone(raw_x)
        ay = apply_deadzone(raw_y)
        # stick Y remonte négatif, donc on inverse pour déplacement intuitif
        move_x = ax * SPEED
        move_y = ay * SPEED

    # fallback clavier (ajoute à la manette si utilisé en plus)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        move_x -= SPEED
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        move_x += SPEED
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        move_y -= SPEED
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        move_y += SPEED

    # déplacement avec dt
    x += move_x * dt
    y += move_y * dt

    # clamp pour rester à l'écran
    x = max(0, min(x, SCREEN_SIZE[0] - SQUARE_SIZE))
    y = max(0, min(y, SCREEN_SIZE[1] - SQUARE_SIZE))

    # ---------- rendu ----------
    screen.fill(BG_COLOR)
    pygame.draw.rect(screen, color, pygame.Rect(int(x), int(y), SQUARE_SIZE, SQUARE_SIZE))

    # affichage debug (axes, boutons)
    if show_debug:
        font = pygame.font.Font(None, 20)
        lines = []
        if joystick:
            # collecter axes
            axes_count = joystick.get_numaxes()
            axes_vals = [f"{i}:{joystick.get_axis(i):+.3f}" for i in range(axes_count)]
            lines.append("Axes: " + "  ".join(axes_vals))
            # boutons
            btn_count = joystick.get_numbuttons()
            btn_vals = [f"{i}:{joystick.get_button(i)}" for i in range(btn_count)]
            lines.append("Buttons: " + "  ".join(btn_vals))
            # hats (D-pad)
            hats = [str(joystick.get_hat(i)) for i in range(joystick.get_numhats())]
            lines.append("Hats: " + " ".join(hats))
            lines.append(f"Stick (post-deadzone) : x={apply_deadzone(joystick.get_axis(0)):+.2f}, y={apply_deadzone(joystick.get_axis(1)):+.2f}")
        else:
            lines.append("Aucune manette connectée. Utilisez le clavier (flèches/WASD).")

        for i, line in enumerate(lines):
            txt = font.render(line, True, (220, 220, 220))
            screen.blit(txt, (10, 10 + i * 18))

    pygame.display.flip()

# ---------- Quit ----------
pygame.quit()
sys.exit()
