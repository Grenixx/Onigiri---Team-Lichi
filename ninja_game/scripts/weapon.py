import pygame
import math
import random


# ============================================================
# ===============   GESTIONNAIRE D'ARME    ====================
# ============================================================
class Weapon:
    def __init__(self, owner, weapon_type='mace'):
        self.owner = owner
        self.weapon_type = weapon_type
        self.set_weapon(weapon_type)

    def set_weapon(self, weapon_type):

        if weapon_type == 'mace':
            self.weapon_equiped = Mace(self.owner)
        #elif weapon_type == 'sword':
        #    self.weapon_equiped = Sword(self.owner)

        self.weapon_type = weapon_type
        print(f"[DEBUG] Arme équipée : {self.weapon_type}")

    def update(self):
        self.weapon_equiped.update()

    def render(self, surf, offset=(0, 0)):
        self.weapon_equiped.render(surf, offset)

    def swing(self, direction):
        self.weapon_equiped.swing(direction)
# ============================================================
# ===============   CLASSE DE BASE ARMES   ====================
# ============================================================
class WeaponBase:
    debug = True  # Debug global

    def __init__(self, owner, image=None):
        self.owner = owner
        self.image = image

        self.attack_timer = 0
        self.attack_duration = 15

        self.attack_direction = "front"
        self.angle = 0

    def toggle_debug(self):
        WeaponBase.debug = not WeaponBase.debug
        print(f"[DEBUG] Debug weapon: {'ON' if WeaponBase.debug else 'OFF'}")


    # ------------------------
    # Update générique
    # ------------------------
    def update(self):
        if self.attack_timer > 0:
            self.attack_timer -= 1

    # ------------------------
    # Swing générique
    # ------------------------
    def swing(self, direction):
        self.attack_direction = direction
        self.attack_timer = self.attack_duration

    # ------------------------
    # Permet aux armes animées
    # de remplacer l'image
    # ------------------------
    def get_image(self):
        return self.image

    # ------------------------
    # Calcul générique de position
    # ------------------------
    def get_render_pos(self, offset=(0, 0)):
        img = pygame.transform.rotate(self.get_image(), self.angle)
        center_x = self.owner.rect().centerx - offset[0]
        center_y = self.owner.rect().centery - offset[1]
        pos_x = center_x - img.get_width() // 2
        pos_y = center_y - img.get_height() // 2
        return (pos_x, pos_y)

    # ------------------------
    # Hitbox automatique
    # ------------------------
    def rect(self):
        img = pygame.transform.rotate(self.get_image(), self.angle)
        return img.get_rect(topleft=self.get_render_pos((0, 0)))

    # ------------------------
    # Render générique
    # ------------------------
    def render(self, surf, offset=(0, 0)):
        if self.attack_timer > 0:
            rotated = pygame.transform.rotate(self.get_image(), self.angle)
            surf.blit(rotated, self.get_render_pos(offset))
            self.render_debug_hitbox(surf, self.rect(), offset)

    # ------------------------
    # Debug hitbox
    # ------------------------
    def render_debug_hitbox(self, surf, rect, offset):
        if WeaponBase.debug:
            pygame.draw.rect(
                surf, (255, 0, 0),
                pygame.Rect(rect.x - offset[0], rect.y - offset[1], rect.width, rect.height),
                2
            )

# ============================================================
# ======================   MASSE   ============================
# ============================================================
class Mace(WeaponBase):
    def __init__(self, owner):
        super().__init__(owner)
        original_animation = owner.game.assets['mace'].copy()
        scaled_images = [
            pygame.transform.scale(img, (img.get_width() // 8, img.get_height() // 8))
            for img in original_animation.images
        ]
        self.animation = original_animation.__class__(
            scaled_images,
            original_animation.img_duration,
            original_animation.loop
        )

        self.offset_amount = 14  # distance fixe du joueur

    # --- IMAGE + ROTATION + FLIP ---
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

        # flip horizontal si attaque vers la gauche
        if self.attack_direction == "left":
            img = pygame.transform.flip(img, True, False)
        elif self.attack_direction == "front":
            if self.owner.flip:
                img = pygame.transform.flip(img, True, False)

        return img

    # --- UPDATE ---
    def update(self):
        super().update()
        if self.attack_timer > 0:
            self.animation.update()

    # --- SWING ---
    def swing(self, direction):
        # si aucune direction, prendre flip
        if direction is None or direction == "front":
            direction = "left" if self.owner.flip else "right"

        self.attack_direction = direction
        super().swing(direction)

        # reset animation
        self.animation.frame = 0
        self.attack_timer = len(self.animation.images) * self.animation.img_duration

    # --- POSITION ---
    def get_render_pos(self, offset=(0, 0)):
        base_x, base_y = super().get_render_pos(offset)

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


    
        
