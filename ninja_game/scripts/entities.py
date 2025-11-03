import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark

# Classe de base pour toutes les entités soumises à la physique (gravité, collisions)
class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        # Références au jeu principal et au type d'entité ('player', 'enemy', etc.)
        self.game = game
        self.type = e_type
        # La position est une liste pour pouvoir la modifier facilement (les tuples sont immuables)
        self.pos = list(pos)
        self.size = size
        # La vélocité est la vitesse de l'entité, affectée par la gravité et les mouvements
        self.velocity = [0, 0]
        # Dictionnaire pour suivre les collisions dans chaque direction
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        # Gestion des animations
        self.action = ''
        self.anim_offset = (-3, -3) # Décalage pour que l'animation soit bien centrée sur la hitbox
        self.flip = False
        # Définit l'action initiale, ce qui charge aussi la première animation
        self.set_action('idle')
        
        # Garde en mémoire le dernier mouvement pour des logiques comme le saut mural
        self.last_movement = [0, 0]
    
    def rect(self):
        # Retourne un objet pygame.Rect représentant la hitbox de l'entité
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        # Change l'animation uniquement si la nouvelle action est différente de l'actuelle
        if action != self.action:
            self.action = action
            # Charge la nouvelle animation depuis le dictionnaire d'assets du jeu
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        # Réinitialise les collisions à chaque frame
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        # Calcule le mouvement total pour cette frame (mouvement intentionnel + vélocité actuelle)
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        # --- Gestion des collisions horizontales ---
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        # Vérifie les collisions avec les tuiles solides autour de l'entité
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                # Si on bouge vers la droite et qu'on touche un mur
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                # Si on bouge vers la gauche et qu'on touche un mur
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                # Met à jour la position pour qu'elle corresponde à la position après collision
                self.pos[0] = entity_rect.x
        
        # --- Gestion des collisions verticales ---
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                # Si on tombe et qu'on touche le sol
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                # Si on saute et qu'on touche un plafond
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
                
        # Oriente le sprite dans la direction du mouvement
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        # Sauvegarde le dernier mouvement
        self.last_movement = movement
        
        # Applique la gravité (augmente la vélocité vers le bas, avec une vitesse de chute maximale)
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        # Si on touche le sol ou un plafond, la vélocité verticale est annulée
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        # Met à jour l'animation (passe à l'image suivante)
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        # Dessine le sprite de l'entité sur la surface de jeu
        # pygame.transform.flip retourne l'image si self.flip est True
        # L'offset est utilisé pour la caméra (scroll)
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        
# Classe pour les ennemis, hérite de PhysicsEntity
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        
        # 'walking' est un timer. Quand il est > 0, l'ennemi marche.
        self.walking = 0
        
    def update(self, tilemap, movement=(0, 0)):
        # Si l'ennemi est en train de marcher
        if self.walking:
            # Vérifie s'il y a du sol devant lui pour ne pas tomber
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                # S'il touche un mur, il fait demi-tour
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    # Sinon, il continue d'avancer
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                # S'il n'y a pas de sol, il fait demi-tour
                self.flip = not self.flip
            # Décrémente le timer de marche
            self.walking = max(0, self.walking - 1)
            # Si le timer de marche vient de se terminer
            if not self.walking:
                # Logique de tir : vérifie si le joueur est à portée et dans la bonne direction
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 16):
                    if (self.flip and dis[0] < 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if (not self.flip and dis[0] > 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        # Si l'ennemi est inactif, il y a une petite chance qu'il décide de marcher pour un temps aléatoire
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        
        # Appelle la méthode update de la classe parente (PhysicsEntity) pour gérer la physique
        super().update(tilemap, movement=movement)
        
        # Décide de l'animation à jouer (run ou idle)
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        # --- Vérification des collisions avec le joueur ---
        # Condition 1: Le joueur est-il en train de dasher ?
        is_hit_by_dash = abs(self.game.player.dashing) >= 50
        # Condition 2: L'arme du joueur est-elle active ET touche-t-elle l'ennemi ?
        is_hit_by_weapon = self.game.player.weapon.attack_timer > 0 and self.rect().colliderect(self.game.player.weapon.rect())
        if is_hit_by_dash or is_hit_by_weapon:
            if self.rect().colliderect(self.game.player.rect()) or is_hit_by_weapon:
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True

            
    def render(self, surf, offset=(0, 0)):
        # Dessine l'ennemi
        super().render(surf, offset=offset)
        
        # Dessine son arme par-dessus, orientée dans la bonne direction
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

# Classe pour le joueur, hérite de PhysicsEntity
class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        # 'air_time' : compteur de frames passées en l'air
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
        # Appelle la méthode update de la classe parente pour la physique de base
        super().update(tilemap, movement=movement)
        
        self.air_time += 1
        # On met à jour l'arme à chaque frame
        self.weapon.update()
        self.jump_buffer_timer = max(0, self.jump_buffer_timer - 1)
        
        # Si le joueur tombe trop longtemps, il meurt
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        # Si le joueur touche le sol, réinitialise son temps en l'air et ses sauts
        if self.collisions['down']:
            self.air_time = 0
            # On redonne 2 sauts au joueur quand il touche le sol.
            self.jumps = True
            # --- JUMP BUFFER CHECK ---
            # Si le buffer de saut est actif au moment où on atterrit, on saute.
            if self.jump_buffer_timer > 0:
                self.jump()

            
        # Logique du "Wall Slide" (glissade sur les murs)
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4 and not self.collisions['down']:
            self.wall_slide = True
            # Ralentit la chute
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        # Sélection de l'animation en fonction de l'état (sauf si en wall_slide)
        if not self.wall_slide and not self.action.startswith('attack'):
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        if self.action.startswith('attack') and self.animation.done:
            self.set_action('idle')
        
        # Logique du Dash
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            # Décrémente le timer du dash
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            # Applique une forte vélocité horizontale pendant le dash
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
                
        if self.velocity[0] > 0:
            # Applique une friction pour ralentir le joueur naturellement
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            # On dessine le joueur
            super().render(surf, offset=offset)
            # Puis on dessine l'arme par-dessus pour qu'elle soit devant
            self.weapon.render(surf, offset)

    def jump(self):
        # Si en train de glisser sur un mur (Wall Jump)
        if self.wall_slide:
            # Le saut propulse le joueur loin du mur
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5 # Un peu de temps en l'air pour éviter un autre wall jump immédiat
                self.jumps = False # On utilise le saut
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
                
    
    def dash(self):
        # Ne peut dasher que si le cooldown est terminé
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

            # Par défaut (aucune touche directionnelle prioritaire), on fait une attaque frontale.
            self.set_action('attack_' + attack_direction)
            # On déclenche l'animation de l'arme
            self.weapon.swing(attack_direction)

            print(f"Action set to {self.action}, weapon swinging {attack_direction}")
            # On pourrait jouer un son ici : self.game.sfx['hit'].play()

class Weapon:
    def __init__(self, owner): #owner sera generalement le joueur
        self.owner = owner
        self.image = owner.game.assets['weapon']
        self.angle = 0
        self.attack_timer = 0
    def update(self):
        if self.attack_timer > 0:
            self.attack_timer = max(0, self.attack_timer - 1)

    def rect(self):
        # Crée un rectangle de collision pour l'arme.
        # C'est une simplification, car il ne tourne pas avec l'image.
        # Mais c'est un excellent point de départ !
        if self.owner.flip:
            # Position de la hitbox quand le joueur regarde à gauche
            return pygame.Rect(self.owner.rect().centerx - self.image.get_width(), self.owner.rect().centery - self.image.get_height() // 2, self.image.get_width(), self.image.get_height())
        else:
            # Position de la hitbox quand le joueur regarde à droite
            return pygame.Rect(self.owner.rect().centerx, self.owner.rect().centery - self.image.get_height() // 2, self.image.get_width(), self.image.get_height())

    def render(self, surf, offset=(0, 0)):
        # On ne dessine l'arme que si elle est en train d'attaquer
        if self.attack_timer > 0:
            center_x = self.owner.rect().centerx - offset[0]
            center_y = self.owner.rect().centery - offset[1]
            rotated_image = pygame.transform.rotate(self.image, self.angle)
            if self.owner.flip:
                pos_x = center_x - rotated_image.get_width() + 10
            else:
                pos_x = center_x - 10
            surf.blit(rotated_image, (pos_x, center_y - rotated_image.get_height() // 2))
    def swing(self, direction):
        self.attack_timer = 15
        if direction == 'up':
            self.angle = -90 if self.owner.flip else 90
        elif direction == 'down':
            self.angle = 90 if self.owner.flip else -90
        else:
            self.angle = 0