import pygame
import math
import random
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.weapon import Weapon
from scripts.grass import GrassManager


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')
        
        self.last_movement = [0, 0]
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
                
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0],
                   self.pos[1] - offset[1] + self.anim_offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        # 'jumps' : nombre de sauts restants (pour le double saut)
        self.jumps = True
        self.wall_slide = False
        # 'dashing' : timer pour la durée et le cooldown du dash
        self.dashing = 0
        # 'is_pressed' : stocke la dernière touche de direction pressée (utile pour les attaques directionnelles)
        self.is_pressed = None
        # Timer pour le "jump buffer". Si > 0, le joueur a demandé un saut récemment.
        self.jump_buffer_timer = 0
        # On crée une instance de l'arme et on la lie au joueur
        self.weapon = Weapon(self)
    
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement) 
        self.air_time += 1
        
        self.weapon.weapon_equiped.update()
        self.jump_buffer_timer = max(0, self.jump_buffer_timer - 1)

        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        if self.collisions['down']:
            self.air_time = 0
            # On redonne 2 sauts au joueur quand il touche le sol.
            self.jumps = True
            # --- JUMP BUFFER CHECK ---
            # Si le buffer de saut est actif au moment où on atterrit, on saute.
            if self.jump_buffer_timer > 0:
                self.jump()
            
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4 and not self.collisions['down']:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        if not self.wall_slide and not self.action.startswith('attack'):
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        if self.action.startswith('attack') and self.animation.done:
            self.set_action('idle')
        
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle',
                                                    self.rect().center,
                                                    velocity=pvelocity,
                                                    frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle',
                                                self.rect().center,
                                                velocity=pvelocity,
                                                frame=random.randint(0, 7)))
                
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
        
        if hasattr(self.game.tilemap, 'grass_manager'):
            ts = self.game.tilemap.tile_size

            # on calcule la "vitesse" effective (input + velocity)
            input_speed = math.hypot(self.last_movement[0], self.last_movement[1])
            vel_speed = math.hypot(self.velocity[0], self.velocity[1])
            speed = input_speed + vel_speed

            # Si on bouge (ou si on dash), applique une impulsion — sinon ne rien faire
            # Ajuste threshold selon ton besoin (0.1 = très sensible)
            if speed > 0.1 or abs(self.dashing) > 0:
                # utilise la center en pixels
                force_pos = self.rect().center

                # rayon et dropoff en pixels (ex: 2.5 tiles et 1.2 tiles)
                radius_px = int(ts * 2.5)
                dropoff_px = int(ts * 1.2)

                # applique la force UNE FOIS pour cette frame (si tu veux un "sweep" prolongé
                # tu peux appliquer un petit nombre de frames, mais pas chaque frame)
                self.game.tilemap.grass_manager.apply_force(force_pos, radius_px, dropoff_px)

    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            # Puis on dessine l'arme par-dessus pour qu'elle soit devant
            self.weapon.weapon_equiped.render(surf, offset)
            
    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = False
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = False
                return True
                
        # Saut normal ou "Coyote Time" : si on a un saut et qu'on est en l'air depuis peu de temps
        elif self.jumps and self.air_time < 9: # 9 frames = ~0.15s
            self.velocity[1] = -3
            self.jumps = False
            self.air_time = 5
            self.jump_buffer_timer = 0 # On a sauté, on annule le buffer
            return True
    
        # Si aucune des conditions de saut n'est remplie
        return False

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
    def request_jump(self):
        # Si on ne peut pas sauter immédiatement (car en l'air), on active le buffer.
        # 12 frames = 0.2s. C'est la fenêtre pendant laquelle le jeu se souviendra de l'appui.
        if not self.jump():
            self.jump_buffer_timer = 12
            return False
        return True

    def attack(self, direction):
        print("Attack initiated")
        # On ne peut pas attaquer si on est déjà en train d'attaquer ou de dasher
        if (not self.action.startswith('attack') or self.animation.done) and not self.dashing and not self.wall_slide:
            
            attack_direction = 'front' # Direction par défaut

            # Priorité 1 : Attaque vers le haut si la touche 'haut' est pressée.
            if direction in ['up', 'down']:
                attack_direction = direction
            
            # --- CORRECTION ---
            # On met à jour l'orientation du joueur si l'attaque est latérale
            # Cela garantit que self.flip est correct même si le joueur est immobile.
            if direction == 'left': self.flip = True
            if direction == 'right': self.flip = False

            # Par défaut (aucune touche directionnelle prioritaire), on fait une attaque frontale.
            self.set_action('attack_' + attack_direction)
            # On déclenche l'animation de l'arme
            self.weapon.weapon_equiped.swing(direction)

            print(f"Action set to {self.action}, weapon swinging {attack_direction}") 
            # On pourrait jouer un son ici : self.game.sfx['hit'].play()

class PurpleCircle:
    """Classe gérant les ennemis ronds violets + collisions avec le joueur."""
    def __init__(self, game):
        self.game = game
        self.radius = 8  # rayon du cercle pour les collisions

    def update(self):
        """
        Vérifie les collisions entre le joueur et les ennemis.
        Si le joueur est en dash et touche un ennemi, on le supprime.
        """
        player = self.game.player
        player_center = player.rect().center
        is_dashing = abs(self.game.player.dashing) > 50
        is_attacking = player.weapon.weapon_equiped.attack_timer > 0
        
        # Si aucune action offensive n'est en cours, on ne fait rien.
        if not is_dashing and not is_attacking:
            return
            
        to_remove = []
        weapon_rect = player.weapon.weapon_equiped.rect()
        
        for eid, (ex, ey) in list(self.game.net.enemies.items()):
            enemy_rect = pygame.Rect(ex - self.radius, ey - self.radius, self.radius * 2, self.radius * 2)
            
            # Condition 1: Le joueur en dash touche l'ennemi
            hit_by_dash = False
            if is_dashing:
                dx, dy = ex - player_center[0], ey - player_center[1]
                if (dx*dx + dy*dy) < (self.radius + 10)**2: # Plus rapide que sqrt
                    hit_by_dash = True
            
            # Condition 2: L'arme en mouvement touche l'ennemi
            hit_by_weapon = is_attacking and weapon_rect.colliderect(enemy_rect)

            if hit_by_dash or hit_by_weapon:
                to_remove.append(eid)

        for eid in to_remove:
            # Supprime localement pour effet instantané
            if eid in self.game.net.enemies:
                del self.game.net.enemies[eid]
            # Envoie la suppression au serveur
            self.game.net.remove_enemy(eid)
            print(f"Ennemi {eid} détruit !")

    def render(self, surf, offset=(0, 0)):
        """Affiche les ennemis ronds violets à l’écran."""
        for eid, (x, y) in self.game.net.enemies.items():
            screen_x = x - offset[0]
            screen_y = y - offset[1]
            pygame.draw.circle(surf, (128, 0, 128), (int(screen_x), int(screen_y)), self.radius)
            
class RemotePlayerRenderer:
    """Affiche et anime les autres joueurs avec leur sprite."""

    class RemotePlayer:
        def __init__(self, game, pid, pos=(0,0), action='idle', flip=False):
            self.game = game
            self.pid = pid
            self.pos = list(pos)
            self.flip = flip
            self.set_action(action)

        def set_action(self, action):
            if hasattr(self, 'action') and self.action == action:
                return
            self.action = action
            base_anim = self.game.assets.get(f'player/{action}', self.game.assets['player/idle'])
            self.animation = base_anim.copy()

        def update(self, pos, action, flip):
            self.pos = list(pos)
            self.flip = flip
            self.set_action(action)
            self.animation.update()

        def render(self, surf, offset=(0,0)):
            img = pygame.transform.flip(self.animation.img(), self.flip, False)
            surf.blit(img, (self.pos[0] - offset[0] - 3, self.pos[1] - offset[1] - 3))

    def __init__(self, game):
        self.game = game
        self.players = {}  # pid -> RemotePlayer

    def render(self, surf, offset=(0,0)):
        for pid, data in self.game.remote_players.items():
            if pid == self.game.net.id:
                continue

            x, y, action, flip = data

            if pid not in self.players:
                self.players[pid] = self.RemotePlayer(self.game, pid, (x,y), action, flip)

            self.players[pid].update((x,y), action, flip)
            self.players[pid].render(surf, offset)
