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

        self.gravity = 600  # pixels/seconde²
        self.max_fall_speed = 300  # pixels/seconde
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0), dt=0):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        horizontal_speed = movement[0] * 120  # 120 pixels/seconde (run_speed)
        
        frame_movement = (
            (horizontal_speed + self.velocity[0]) * dt,
            (movement[1] + self.velocity[1]) * dt
        )
        
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
        
        #self.velocity[1] = min(5, self.velocity[1] + 0.1)
        self.velocity[1] = min(self.max_fall_speed, self.velocity[1] + self.gravity * dt)

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        self.animation.update(dt)
        #self.pos[0] = round(self.pos[0])
        #self.pos[1] = round(self.pos[1])
        
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

        self.jump_force = -250  # pixels/seconde (négatif = vers le haut)
        self.wall_jump_force_x = 210  # pixels/seconde
        self.wall_jump_force_y = -230  # pixels/seconde
        
        # Constantes pour la détection (en secondes, pas en frames)
        self.coyote_time = 0.15  # secondes au lieu de 9 frames
        self.jump_buffer_time = 0.2  # secondes au lieu de 12 frames
        self.wall_slide_speed = 30  # pixels/seconde maximum en glissade

        self.air_resistance = 600  # pixels/seconde²
        self.dash_duration = 0.1   # secondes (correspond à 30 frames à 60 FPS)
        self.dash_speed = 200
        self.dash_cooldown = 0.5   # secondes (correspond à 30 frames à 60 FPS)
        self.dash_invisible_duration = 0.1  # secondes (correspond à 12 frames à 60 FPS)

    def update(self, tilemap, movement=(0, 0), dt=0):
        super().update(tilemap, movement=movement, dt=dt) 

        if self.collisions['down']:
            self.air_time = 0
        else:
            self.air_time += dt  # dt est en secondes

        
        self.weapon.weapon_equiped.update(dt)
        self.jump_buffer_timer = max(0, self.jump_buffer_timer - dt)

        if self.air_time > 2 :
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        if self.wall_slide:
            self.air_time = 0.08
        if self.collisions['down'] :
            self.air_time = 0
            # On redonne 2 sauts au joueur quand il touche le sol.
            self.jumps = True
            # --- JUMP BUFFER CHECK ---
            # Si le buffer de saut est actif au moment où on atterrit, on saute.
            if self.jump_buffer_timer > 0:
                self.jump()
             
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 0.067 and not self.collisions['down']:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], self.wall_slide_speed)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        if not self.wall_slide and not self.action.startswith('attack'):
            if self.air_time > 0.067:
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
            self.dashing = max(0, self.dashing - dt)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + dt)

            
        dash_progress = abs(self.dashing) / self.dash_duration
        # Particules de début et de fin de dash
        #if dash_progress > 0.9 or (dash_progress < 0.1 and self.dashing != 0):
        #    for i in range(20):
        #        angle = random.random() * math.pi * 2
        #        speed = random.random() * 0.5 + 0.5
        #        pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
        #        self.game.particles.append(Particle(self.game, 'particle',
        #                                           self.rect().center,
        #                                           velocity=pvelocity,
        #                                           frame=random.randint(0, 7)))

        if self.dashing != 0:
            self.velocity[0] = self.dash_speed if self.dashing > 0 else -self.dash_speed
            if dash_progress > 0.9:
                self.velocity[0] *= 0.1
                
                # Résistance de l'air (décélération horizontale)
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - self.air_resistance * dt, 0)
        elif self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + self.air_resistance * dt, 0)
        
        
        #force_pos = self.rect().center  # (x_pixels, y_pixels)
        #self.game.tilemap.grass_manager.update_render(self.game.display,1/60, offset=self.game.scroll)
        # On veut la force au centre des pieds, pas en haut à gauche
        player_height = self.game.player.size[1]  # même taille que le joueur local
        force_pos = (self.pos[0] + self.game.player.size[0] / 2, self.pos[1] + player_height)
        self.game.tilemap.grass_manager.apply_force(force_pos, 4, 8)


    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= self.dash_duration - self.dash_invisible_duration:
            super().render(surf, offset=offset)
            # Puis on dessine l'arme par-dessus pour qu'elle soit devant
            self.weapon.weapon_equiped.render(surf, offset)
            
    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = self.wall_jump_force_x
                self.velocity[1] = self.wall_jump_force_y
                self.air_time = 0.08
                self.jumps = False
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = self.wall_jump_force_x * -1
                self.velocity[1] = self.wall_jump_force_y
                self.air_time = 0.08
                self.jumps = False
                return True
                
        # Saut normal ou "Coyote Time" : si on a un saut et qu'on est en l'air depuis peu de temps
        elif self.jumps and self.air_time < self.coyote_time: # 9 frames = ~0.15s
            self.velocity[1] = self.jump_force
            self.jumps = False
            self.air_time = 0.08
            self.jump_buffer_timer = 0 # On a sauté, on annule le buffer
            return True
    
        # Si aucune des conditions de saut n'est remplie
        return False

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -self.dash_duration
            else:
                self.dashing = self.dash_duration
    def request_jump(self):
        # Si on ne peut pas sauter immédiatement (car en l'air), on active le buffer.
        # 12 frames = 0.2s. C'est la fenêtre pendant laquelle le jeu se souviendra de l'appui.
        if not self.jump():
            self.jump_buffer_timer = self.jump_buffer_time
            return False
        return True

    def attack(self, direction):
        # On ne peut pas attaquer si on est déjà en train d'attaquer ou de dasher
        if (not self.action.startswith('attack') or self.animation.done)and not self.wall_slide:
            
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



class PurpleCircle:
    """Classe gérant les ennemis ronds violets + collisions avec le joueur."""
    def __init__(self, game):
        self.game = game
        self.radius = 8  # rayon du cercle pour les collisions

        base_anim = self.game.assets.get(f'yokai2', self.game.assets['player/idle'])
        self.animation = base_anim.copy()

    def update(self):
        """
        Vérifie les collisions entre le joueur et les ennemis.
        Si le joueur est en dash et touche un ennemi, on le supprime.
        """
        player = self.game.player
        is_attacking = player.weapon.weapon_equiped.attack_timer > 0

        for eid, (ex, ey, flip) in list(self.game.net.enemies.items()):
            player = self.game.player
            player_col = player.rect()


            enemy_rect = pygame.Rect(ex - self.radius, ey - self.radius, self.radius * 2, self.radius * 2)
            
            if player_col.colliderect(enemy_rect) == True:
                if not self.game.dead:
                    self.game.screenshake = max(16, self.game.screenshake)
                    self.game.sfx['hit'].play()
                self.game.dead += 1


        # Si aucune action offensive n'est en cours, on ne fait rien.
        if not is_attacking:
            return
            
        to_remove = []
        weapon_rect = player.weapon.weapon_equiped.rect()

        
        for eid, (ex, ey, flip) in list(self.game.net.enemies.items()):
            enemy_rect = pygame.Rect(ex - self.radius, ey - self.radius, self.radius * 2, self.radius * 2)
            # JE RETIRE LE DASH QUI TUE
            #hit_by_dash = False
            #if is_dashing:
            #    dx, dy = ex - player_center[0], ey - player_center[1]
            #    if (dx*dx + dy*dy) < (self.radius + 10)**2: # Plus rapide que sqrt
            #        hit_by_dash = True
            
            # L'arme en mouvement touche l'ennemi
            hit_by_weapon = is_attacking and weapon_rect.colliderect(enemy_rect)

            if hit_by_weapon:
                to_remove.append(eid)

        for eid in to_remove:
            # Supprime localement pour effet instantané
            if eid in self.game.net.enemies:
                del self.game.net.enemies[eid]
            # Envoie la suppression au serveur
            self.game.net.remove_enemy(eid)
        

    def render(self, surf, offset=(0, 0), dt=1):
        """Affiche les ennemis ronds violets à l’écran."""

        #surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
        #          (self.pos[0] - offset[0] + self.anim_offset[0],
        #           self.pos[1] - offset[1] + self.anim_offset[1]))
        for eid, (x, y, flip) in self.game.net.enemies.items():
            screen_x = x - offset[0]
            screen_y = y - offset[1]

            #pygame.draw.circle(surf, (128, 0, 128), (int(screen_x), int(screen_y)), self.radius)
            
            self.animation.update(dt)
            imgAnim = self.animation.img()
            surf.blit(pygame.transform.flip(imgAnim, flip, False), (screen_x - imgAnim.get_width()//2, screen_y - imgAnim.get_height()//2))
            self.game.tilemap.grass_manager.apply_force((x, y), 6, 12)
            
            
            
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

        def update(self, pos, action, flip, dt=1):
            self.pos = list(pos)
            self.flip = flip
            self.set_action(action)
            self.animation.update(dt)

        def render(self, surf, offset=(0,0)):
            img = pygame.transform.flip(self.animation.img(), self.flip, False)
            surf.blit(img, (self.pos[0] - offset[0] - 3, self.pos[1] - offset[1] - 3))
            

    def __init__(self, game):
        self.game = game
        self.players = {}  # pid -> RemotePlayer

    def render(self, surf, offset=(0,0), dt=1):
        for pid, data in self.game.remote_players.items():
            if pid == self.game.net.id:
                continue

            x, y, action, flip = data

            #self.game.tilemap.grass_manager.apply_force((x, y), 4, 8)
            # On veut la force au centre des pieds, pas en haut à gauche
            player_height = self.game.player.size[1]  # même taille que le joueur local
            force_pos = (x + self.game.player.size[0] / 2, y + player_height)
            self.game.tilemap.grass_manager.apply_force(force_pos, 4, 8)

            if pid not in self.players:
                self.players[pid] = self.RemotePlayer(self.game, pid, (x,y), action, flip)

            self.players[pid].update((x,y), action, flip, dt)
            self.players[pid].render(surf, offset)



            
