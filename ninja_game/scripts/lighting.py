import pygame
import math

class LightingSystem:
    def __init__(self, size):
        # Surface sur laquelle sera dessinée la lumière
        self.surface = pygame.Surface(size).convert_alpha()
        self.surface.fill((0, 0, 0, 255))

        # Masque de halo pré-généré
        self.light_mask_base = pygame.Surface((256, 256), pygame.SRCALPHA)
        pygame.draw.circle(self.light_mask_base, (255, 255, 255, 255), (128, 128), 128)
        self.light_mask_base = pygame.transform.smoothscale(self.light_mask_base, (256, 256))

        # On peut pré-créer plusieurs tailles si on veut un cache
        self.light_masks = [pygame.transform.smoothscale(self.light_mask_base, (r, r)) for r in range(32, 512, 16)]

    def clear(self, darkness_color=(5, 15, 35)):
        """Remplit la surface d’une couleur sombre (obscurité ambiante)."""
        self.surface.fill(darkness_color)

    def draw_light(self, pos, radius=200, intensity=1.0, color=(255, 255, 255)):
        """Ajoute une lumière douce à la position donnée."""
        # Sélectionne le masque de taille la plus proche
        radius = max(32, min(radius, 512))
        idx = min(len(self.light_masks) - 1, radius // 16 - 2)
        glow_img = self.light_masks[idx].copy()

        # Teinte la lumière
        r, g, b = color
        glow_img.fill((r, g, b, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Ajuste l’intensité (luminosité)
        if intensity != 1.0:
            glow_img.set_alpha(int(255 * intensity))

        rect = glow_img.get_rect(center=pos)
        self.surface.blit(glow_img, rect, special_flags=pygame.BLEND_RGBA_ADD)

    def apply(self, target_surface):
        """Applique l’effet de lumière sur une surface de jeu."""
        target_surface.blit(self.surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
