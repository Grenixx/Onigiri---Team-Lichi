import pygame
import math
import random

# --- Classe de base pour toutes les armes ---
class WeaponBase:
    """Classe de base pour toutes les armes : gère le rendu, le timer, le mode debug."""
    debug = True  # Mode debug global

    def __init__(self, owner):
        self.owner = owner
        self.attack_timer = 0
        self.attack_duration = 15
        self.attack_direction = 'front'
        self.angle = 0

    def toggle_debug(self):
        """Active/désactive le mode debug."""
        WeaponBase.debug = not WeaponBase.debug
        print(f"[DEBUG] Mode debug arme {'activé' if WeaponBase.debug else 'désactivé'}")

    def update(self):
        """Met à jour le timer d'attaque."""
        if self.attack_timer > 0:
            self.attack_timer = max(0, self.attack_timer - 1)

    def swing(self, direction):
        """Déclenche une attaque dans une direction donnée."""
        self.attack_timer = self.attack_duration
        self.attack_direction = direction
        print(f"[DEBUG] Swing: {direction}")

    def render_debug_hitbox(self, surf, rect, offset):
        """Affiche le rectangle de collision (si le debug est actif)."""
        if WeaponBase.debug:
            pygame.draw.rect(
                surf, (255, 0, 0),
                pygame.Rect(rect.x - offset[0], rect.y - offset[1], rect.width, rect.height),
                2
            )


# --- Classe Weapon gérant l’arme équipée ---
class Weapon:
    """Gestionnaire d’arme : choisit l’arme active (lance, masse, etc.)"""
    def __init__(self, owner, weapon_type='lance'):
        self.owner = owner
        self.weapon_type = weapon_type
        self.set_weapon(weapon_type)

    def set_weapon(self, weapon_type):
        """Change le type d’arme actuellement équipée."""
        if weapon_type == 'lance':
            self.weapon_equiped = Lance(self.owner)
        elif weapon_type == 'mace':
            self.weapon_equiped = Mace(self.owner)
        elif weapon_type == 'sword':
            self.weapon_equiped = Sword(self.owner)
        self.weapon_type = weapon_type
        print(f"[DEBUG] Arme équipée : {self.weapon_type}")

    def update(self):
        self.weapon_equiped.update()

    def render(self, surf, offset=(0, 0)):
        self.weapon_equiped.render(surf, offset)

    def swing(self, direction):
        self.weapon_equiped.swing(direction)


# --- Classe Lance héritant de WeaponBase ---
class Lance(WeaponBase):
    def __init__(self, owner):
        super().__init__(owner)
        self.image = owner.game.assets['lance']
        self.attack_duration = 15
        self.max_thrust = 16
        self.retract_distance = 4

    def get_render_pos(self, offset):
        """Calcule la position d’affichage en fonction de l’état de l’attaque."""
        center_x = self.owner.rect().centerx - offset[0]
        center_y = self.owner.rect().centery - offset[1]

        progress = (self.attack_duration - self.attack_timer) / self.attack_duration
        progress = max(0.0, min(1.0, progress))

        if progress < 0.3:
            thrust_progress = progress / 0.3
        elif progress < 0.6:
            thrust_progress = 1.0
        else:
            thrust_progress = 1.0 - ((progress - 0.6) / 0.4)

        thrust = thrust_progress * self.max_thrust - self.retract_distance
        rotated_image = pygame.transform.rotate(self.image, self.angle)

        if self.attack_direction == 'up':
            pos_x = center_x - rotated_image.get_width() // 2
            pos_y = center_y - rotated_image.get_height() - thrust
        elif self.attack_direction == 'down':
            pos_x = center_x - rotated_image.get_width() // 2
            pos_y = center_y + thrust
        else:
            pos_y = center_y - rotated_image.get_height() // 2
            if self.owner.flip:
                pos_x = center_x - rotated_image.get_width() - thrust + 15
            else:
                pos_x = center_x + thrust - 15

        return (pos_x, pos_y)

    def rect(self):
        """Retourne le rectangle de collision pour les tests et le debug."""
        pos = self.get_render_pos((0, 0))
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        return rotated_image.get_rect(topleft=pos)

    def render(self, surf, offset=(0, 0)):
        if self.attack_timer > 0:
            pos = self.get_render_pos(offset)
            rotated_image = pygame.transform.rotate(self.image, self.angle)
            surf.blit(rotated_image, pos)

            # mode debug : afficher la hitbox
            self.render_debug_hitbox(surf, self.rect(), offset)

    def swing(self, direction):
        super().swing(direction)
        if direction == 'up':
            self.angle = 90
        elif direction == 'down':
            self.angle = -90
        else:
            self.angle = 180 if self.owner.flip else 0
        print(f"[DEBUG] Lance swing {direction}, angle={self.angle}, flip={self.owner.flip}")


# --- Classe Mace héritant de WeaponBase ---
class Mace(WeaponBase):
    def __init__(self, owner):
        super().__init__(owner)
        original_animation = owner.game.assets['mace'].copy()
        scaled_images = [
            pygame.transform.scale(img, (img.get_width() , img.get_height() ))
            for img in original_animation.images
        ]
        self.animation = original_animation.__class__(
            scaled_images, original_animation.img_duration, original_animation.loop
        )

    def update(self):
        super().update()
        if self.attack_timer > 0:
            self.animation.update()

    def get_render_pos(self, offset):
        center_x = self.owner.rect().centerx - offset[0]
        center_y = self.owner.rect().centery - offset[1]
        image = self.animation.img()
        pos_y = center_y - image.get_height() // 2 - 10
        pos_x = center_x - image.get_width() if self.owner.flip else center_x
        return (pos_x, pos_y)

    def rect(self):
        pos = self.get_render_pos((0, 0))
        image = self.animation.img()
        return pygame.Rect(pos[0], pos[1], image.get_width(), image.get_height())

    def render(self, surf, offset=(0, 0)):
        if self.attack_timer > 0:
            image = self.animation.img()
            image = pygame.transform.flip(image, self.owner.flip, False)
            pos = self.get_render_pos(offset)
            surf.blit(image, pos)
            self.render_debug_hitbox(surf, self.rect(), offset)

    def swing(self, direction):
        super().swing(direction)
        self.attack_timer = self.animation.img_duration * len(self.animation.images)
        self.animation.frame = 0


# --- Classe Sword avec slash rotatif et flip uniquement horizontal ---
class Sword(WeaponBase):
    def __init__(self, owner):
        super().__init__(owner)
        self.image = owner.game.assets['sword']  # image temporaire
        self.attack_duration = 15
        self.start_angle = 0
        self.end_angle = 0
        self.current_angle = 0
        self.max_thrust = 16
        self.retract_distance = 4

    def update(self):
        super().update()
        if self.attack_timer > 0:
            progress = (self.attack_duration - self.attack_timer) / self.attack_duration
            self.current_angle = self.start_angle + (self.end_angle - self.start_angle) * progress

    def get_render_pos(self, offset):
        center_x = self.owner.rect().centerx - offset[0]
        center_y = self.owner.rect().centery - offset[1]

        thrust = self.max_thrust
        rotated_image = pygame.transform.rotate(self.image, self.current_angle)

        if self.attack_direction == 'up':
            pos_x = center_x - rotated_image.get_width() // 2
            pos_y = center_y - rotated_image.get_height() - thrust
        elif self.attack_direction == 'down':
            pos_x = center_x - rotated_image.get_width() // 2
            pos_y = center_y + thrust
        else:  # horizontal
            pos_y = center_y - rotated_image.get_height() // 2
            if self.owner.flip:  # gauche
                pos_x = center_x - rotated_image.get_width() - thrust + 15
            else:  # droite
                pos_x = center_x + thrust - 15

        return (pos_x, pos_y)

    def rect(self):
        pos = self.get_render_pos((0, 0))
        rotated_image = pygame.transform.rotate(self.image, self.current_angle)
        return rotated_image.get_rect(topleft=pos)

    def render(self, surf, offset=(0, 0)):
        if self.attack_timer > 0:
            pos = self.get_render_pos(offset)
            rotated_image = pygame.transform.rotate(self.image, self.current_angle)
            surf.blit(rotated_image, pos)
            self.render_debug_hitbox(surf, self.rect(), offset)

    def swing(self, direction):
        """Slash rotatif, flip seulement pour horizontal."""
        super().swing(direction)
        self.attack_direction = direction

        # Flip uniquement si horizontal
        if direction == 'left':
            self.owner.flip = True
        elif direction == 'right':
            self.owner.flip = False
        # Pour 'up' et 'down', on ne touche pas à flip

        # Définir l’arc de rotation selon la direction
        if direction == 'up':
            self.start_angle = -90
            self.end_angle = 0
        elif direction == 'down':
            self.start_angle = 90
            self.end_angle = 0
        elif direction == 'left':
            self.start_angle = 180
            self.end_angle = 120
        else:  # right
            self.start_angle = 0
            self.end_angle = -60

        self.current_angle = self.start_angle
        print(f"[DEBUG] Sword swing {direction}, start_angle={self.start_angle}, end_angle={self.end_angle}, flip={self.owner.flip}")
