import pygame
import math
import random
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.weapon import Weapon
from scripts.grass import GrassManager

# Constantes pour une logique indépendante du framerate
GRAVITY = 600.0           # pixels/s² (0.1 * 60²)
MAX_FALL_SPEED = 300.0    # pixels/s (5.0 * 60)
FRICTION = 360.0          # pixels/s² (0.1 * 60)
RUN_SPEED = 120.0         # pixels/s (2.0 * 60)
JUMP_FORCE = -180.0       # pixels/s (-3.0 * 60)
WALL_JUMP_X = 210.0       # pixels/s (3.5 * 60)
WALL_JUMP_Y = -150.0      # pixels/s (-2.5 * 60)

# Timers en secondes (inchangés)
COYOTE_TIME = 0.15        # 9 frames à 60 FPS
JUMP_BUFFER_TIME = 0.20   # 12 frames à 60 FPS
DASH_TIME = 1.0           # 60 frames à 60 FPS
DASH_SPEED = 480.0        # pixels/s (8.0 * 60)
WALL_SLIDE_SPEED = 30.0   # pixels/s (0.5 * 60)


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0.0, 0.0]
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
    
    def update(self, tilemap, movement=(0, 0), dt=0):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        # Calcul du mouvement pour ce frame
        frame_movement_x = (movement[0] * RUN_SPEED + self.velocity[0]) * dt
        frame_movement_y = (movement[1] + self.velocity[1]) * dt
        
        # Déplacement horizontal
        self.pos[0] += frame_movement_x
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement_x > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement_x < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        # Déplacement vertical
        self.pos[1] += frame_movement_y
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement_y > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement_y < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
        
        # Orientation
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        # Gravité
        self.velocity[1] += GRAVITY * dt
        self.velocity[1] = min(self.velocity[1], MAX_FALL_SPEED)
        
        # Reset de la vélocité verticale si collision
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
        
        # Mise à jour de l'animation
        self.animation.update()
    
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0],
                   self.pos[1] - offset[1] + self.anim_offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0.0
        self.jumps = True
        self.wall_slide = False
        self.dashing = 0.0
        self.is_pressed = None
        self.jump_buffer_timer = 0.0
        self.weapon = Weapon(self)
    
    def update(self, tilemap, movement=(0, 0), dt=0):
        # Mise à jour de la physique de base
        super().update(tilemap, movement=movement, dt=dt)
        
        # Mise à jour des timers
        self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        
        # Gestion du temps dans les airs
        if self.collisions['down']:
            self.air_time = 0.0
            self.jumps = True
            # Jump buffer check
            if self.jump_buffer_timer > 0:
                self.jump()
        else:
            self.air_time += dt
        
        # Mort après chute
        if self.air_time > 2.0:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        # Wall slide
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 0.07 and not self.collisions['down']:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], WALL_SLIDE_SPEED)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        # Gestion du dash
        if abs(self.dashing) > 0:
            # Particules de dash
            if abs(self.dashing) in {DASH_TIME, DASH_TIME - 0.17}:  # ~60 et 50 frames à 60 FPS
                for _ in range(20):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 30.0 + 30.0  # pixels/s
                    pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                    self.game.particles.append(Particle(self.game, 'particle',
                                                        self.rect().center,
                                                        velocity=pvelocity,
                                                        frame=random.randint(0, 7)))
            
            # Réduction du timer de dash
            if self.dashing > 0:
                self.dashing = max(0, self.dashing - dt)
            else:
                self.dashing = min(0, self.dashing + dt)
            
            # Appliquer la vitesse de dash
            if abs(self.dashing) > DASH_TIME * 0.833:  # > 50/60 de la durée
                dash_direction = 1 if self.dashing > 0 else -1
                self.velocity[0] = dash_direction * DASH_SPEED
                
                # Particules pendant le dash
                pvelocity = [dash_direction * random.random() * 180.0, 0]  # pixels/s
                self.game.particles.append(Particle(self.game, 'particle',
                                                    self.rect().center,
                                                    velocity=pvelocity,
                                                    frame=random.randint(0, 7)))
        
        # Friction horizontale (uniquement sur le sol)
        if movement[0] == 0 and self.collisions['down']:
            if self.velocity[0] > 0:
                self.velocity[0] = max(0, self.velocity[0] - FRICTION * dt)
            elif self.velocity[0] < 0:
                self.velocity[0] = min(0, self.velocity[0] + FRICTION * dt)
            
            # Arrondir à zéro si très proche
            if abs(self.velocity[0]) < 1.0:
                self.velocity[0] = 0
        
        # Animations
        if not self.wall_slide and not self.action.startswith('attack'):
            if self.air_time > 0.07:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        # Fin d'attaque
        if self.action.startswith('attack') and self.animation.done:
            self.set_action('idle')
        
        # Mise à jour de l'arme
        self.weapon.weapon_equiped.update()
        
        # Force sur l'herbe
        player_height = self.size[1]
        force_pos = (self.pos[0] + self.size[0] / 2, self.pos[1] + player_height)
        self.game.tilemap.grass_manager.apply_force(force_pos, 4, 8)
    
    def render(self, surf, offset=(0, 0)):
        # Ne pas render pendant la majeure partie du dash
        if abs(self.dashing) <= DASH_TIME * 0.833:  # <= 50/60 de la durée
            super().render(surf, offset=offset)
            self.weapon.weapon_equiped.render(surf, offset)
    
    def jump(self):
        # Wall jump
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = WALL_JUMP_X
                self.velocity[1] = WALL_JUMP_Y
                self.air_time = 0.08  # ~5 frames à 60 FPS
                self.jumps = False
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -WALL_JUMP_X
                self.velocity[1] = WALL_JUMP_Y
                self.air_time = 0.08
                self.jumps = False
                return True
        
        # Saut normal avec coyote time
        elif self.jumps and self.air_time < COYOTE_TIME:
            self.velocity[1] = JUMP_FORCE
            self.jumps = False
            self.air_time = COYOTE_TIME + 0.01  # Désactiver coyote time
            self.jump_buffer_timer = 0
            return True
        
        return False
    
    def dash(self):
        if self.dashing == 0:
            self.game.sfx['dash'].play()
            self.dashing = DASH_TIME if not self.flip else -DASH_TIME
    
    def request_jump(self):
        if not self.jump():
            self.jump_buffer_timer = JUMP_BUFFER_TIME
            return False
        return True
    
    def attack(self, direction):
        if (not self.action.startswith('attack') or self.animation.done) and not self.wall_slide:
            attack_direction = 'front'
            
            if direction in ['up', 'down']:
                attack_direction = direction
            
            # Mise à jour de l'orientation
            if direction == 'left':
                self.flip = True
            elif direction == 'right':
                self.flip = False
            
            self.set_action('attack_' + attack_direction)
            self.weapon.weapon_equiped.swing(direction)


class PurpleCircle:
    """Classe gérant les ennemis ronds violets + collisions avec le joueur."""
    def __init__(self, game):
        self.game = game
        self.radius = 8
    
    def update(self, dt=0):
        player = self.game.player
        player_center = player.rect().center
        is_dashing = abs(player.dashing) > DASH_TIME * 0.833  # > 50/60 de la durée
        is_attacking = player.weapon.weapon_equiped.attack_timer > 0
        
        if not is_dashing and not is_attacking:
            return
        
        to_remove = []
        weapon_rect = player.weapon.weapon_equiped.rect()
        
        for eid, (ex, ey) in list(self.game.net.enemies.items()):
            enemy_rect = pygame.Rect(ex - self.radius, ey - self.radius, 
                                    self.radius * 2, self.radius * 2)
            
            hit_by_dash = False
            if is_dashing:
                dx, dy = ex - player_center[0], ey - player_center[1]
                if (dx*dx + dy*dy) < (self.radius + 10)**2:
                    hit_by_dash = True
            
            hit_by_weapon = is_attacking and weapon_rect.colliderect(enemy_rect)
            
            if hit_by_dash or hit_by_weapon:
                to_remove.append(eid)
        
        for eid in to_remove:
            if eid in self.game.net.enemies:
                del self.game.net.enemies[eid]
            self.game.net.remove_enemy(eid)
    
    def render(self, surf, offset=(0, 0)):
        for eid, (x, y) in self.game.net.enemies.items():
            screen_x = x - offset[0]
            screen_y = y - offset[1]
            pygame.draw.circle(surf, (128, 0, 128), (int(screen_x), int(screen_y)), self.radius)
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
        
        def update(self, pos, action, flip, dt=0):
            self.pos = list(pos)
            self.flip = flip
            self.set_action(action)
            self.animation.update()
        
        def render(self, surf, offset=(0,0)):
            img = pygame.transform.flip(self.animation.img(), self.flip, False)
            surf.blit(img, (self.pos[0] - offset[0] - 3, self.pos[1] - offset[1] - 3))
    
    def __init__(self, game):
        self.game = game
        self.players = {}
    
    def render(self, surf, offset=(0,0)):
        for pid, data in self.game.remote_players.items():
            if pid == self.game.net.id:
                continue
            
            x, y, action, flip = data
            
            player_height = self.game.player.size[1]
            force_pos = (x + self.game.player.size[0] / 2, y + player_height)
            self.game.tilemap.grass_manager.apply_force(force_pos, 4, 8)
            
            if pid not in self.players:
                self.players[pid] = self.RemotePlayer(self.game, pid, (x,y), action, flip)
            
            self.players[pid].update((x,y), action, flip)
            self.players[pid].render(surf, offset)