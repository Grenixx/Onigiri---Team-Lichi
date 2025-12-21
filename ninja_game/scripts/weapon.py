import pygame
import math
import random

# ============================================================
# ===============   GESTIONNAIRE D'ARME    =================
# ============================================================
class Weapon:
    def __init__(self, owner, weapon_type='mace'):
        self.owner = owner
        self.weapon_type = weapon_type
        self.weapon_equiped = None  # Toujours initialisé
        self.set_weapon(weapon_type)

    def set_weapon(self, weapon_type):
        # Ici toutes les armes type “masse” utilisent WeaponBase
        if weapon_type in ['mace', 'mace1', 'club']:
            self.weapon_equiped = WeaponBase(self.owner, weapon_type)
        else:
            # fallback si arme inconnue
            self.weapon_equiped = WeaponBase(self.owner, 'mace')

        self.weapon_type = weapon_type
        print(f"[DEBUG] Arme équipée : {self.weapon_type}")

    def update(self):
        self.weapon_equiped.update()

    def render(self, surf, offset=(0, 0)):
        self.weapon_equiped.render(surf, offset)

    def swing(self, direction=None):
        self.weapon_equiped.swing(direction)


# ============================================================
# ===============   CLASSE DE BASE ARMES   =================
# ============================================================
class WeaponBase:
    debug = True  # Debug global

    def __init__(self, owner, weapon_type='mace'):
        self.owner = owner
        self.weapon_type = weapon_type
        self.attack_timer = 0
        self.attack_duration = 15
        self.attack_direction = "front"
        self.angle = 0

        # animation placeholder, charge les sprites selon le type
        self.animation = self.load_animation(weapon_type)

        # distance fixe de l'arme par rapport au joueur
        self.offset_amount = 14  

    # ------------------------
    # Charge l'animation depuis assets
    # ------------------------
    def load_animation(self, weapon_type):
        anim_asset = self.owner.game.assets.get(weapon_type)
        if anim_asset is None:
            raise ValueError(f"Aucun asset trouvé pour {weapon_type}")
        # Scale pour s'adapter au jeu
        scaled_images = [
            pygame.transform.scale(img, (img.get_width() // 6, img.get_height() // 6))
            for img in anim_asset.images
        ]
        return anim_asset.__class__(scaled_images, anim_asset.img_duration, anim_asset.loop)

    # ------------------------
    # Toggle debug
    # ------------------------
    def toggle_debug(self):
        WeaponBase.debug = not WeaponBase.debug
        print(f"[DEBUG] Debug weapon: {'ON' if WeaponBase.debug else 'OFF'}")

    # ------------------------
    # Update
    # ------------------------
    def update(self):
        if self.attack_timer > 0:
            self.attack_timer -= 1
            self.animation.update()

    # ------------------------
    # Swing / attaque
    # ------------------------
    def swing(self, direction=None):
        # par défaut utiliser le flip du joueur
        if direction is None or direction == "front":
            direction = "left" if self.owner.flip else "right"

        self.attack_direction = direction
        self.attack_timer = len(self.animation.images) * self.animation.img_duration
        self.animation.frame = 0

    # ------------------------
    # Obtenir image (avec rotation et flip)
    # ------------------------
    def get_image(self):
        img = self.animation.img()

        # angle selon direction
        if self.attack_direction == "up":
            angle = 90
        elif self.attack_direction == "down":
            angle = -90
        else:  # gauche/droite ou front
            angle = 0

        img = pygame.transform.rotate(img, angle)

        # flip horizontal si attaque vers la gauche ou joueur regarde à gauche
        if self.attack_direction == "left":
            img = pygame.transform.flip(img, True, False)
        elif self.attack_direction == "front" and self.owner.flip:
            img = pygame.transform.flip(img, True, False)
        elif self.attack_direction == "up" and self.owner.flip:
            img = pygame.transform.flip(img, True, False)

        elif self.attack_direction == "down" and not self.owner.flip:
            img = pygame.transform.flip(img, True, False)

        return img

    # ------------------------
    # Calcul de position de rendu
    # ------------------------
    def get_render_pos(self, offset=(0, 0)):
        center_x = self.owner.rect().centerx - offset[0]
        center_y = self.owner.rect().centery - offset[1]

        base_x = center_x - self.get_image().get_width() // 2
        base_y = center_y - self.get_image().get_height() // 2

        # offset selon direction
        if self.attack_direction in ["right", "front"]:
            base_x += self.offset_amount
        elif self.attack_direction == "left":
            base_x -= self.offset_amount
        elif self.attack_direction == "up":
            base_y -= self.offset_amount
        elif self.attack_direction == "down":
            base_y += self.offset_amount

        return (base_x, base_y)

    # ------------------------
    # Hitbox
    # ------------------------
    def rect(self):
        img = self.get_image()
        return img.get_rect(topleft=self.get_render_pos((0, 0)))

    # ------------------------
    # Render
    # ------------------------
    def render(self, surf, offset=(0, 0)):
        if self.attack_timer > 0:
            img = self.get_image()
            surf.blit(img, self.get_render_pos(offset))
            self.render_debug_hitbox(surf, self.rect(), offset)

    # ------------------------
    # Debug hitbox
    # ------------------------
    def render_debug_hitbox(self, surf, rect, offset):
        if WeaponBase.debug:
            pygame.draw.rect(
                surf,
                (255, 0, 0),
                pygame.Rect(rect.x - offset[0], rect.y - offset[1], rect.width, rect.height),
                2
            )
