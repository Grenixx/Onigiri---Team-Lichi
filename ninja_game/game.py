# --- Importations des modules nécessaires ---
import os
import sys
import math
import random

# Importation de la bibliothèque Pygame pour la création du jeu
import pygame

# Importations des scripts personnalisés du projet
from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark
from client_network import ClientNetwork

# Constante qui stocke le chemin absolu du dossier 'ninja_game'.
# C'est crucial pour que le jeu trouve ses ressources (images, sons, cartes) peu importe d'où il est lancé.
BASE_PATH = os.path.dirname(__file__)

class Game:
    def __init__(self):
        # Initialisation de tous les modules Pygame
        pygame.init()

        # Configuration de la fenêtre du jeu
        pygame.display.set_caption('ninja game')
        self.screen = pygame.display.set_mode((640, 480)) # La fenêtre principale, visible par le joueur
        # 'display' est une surface de rendu interne à basse résolution (320x240).
        # On dessine le jeu sur cette surface, puis on l'agrandit pour un effet pixel-art.
        # SRCALPHA permet la transparence, utile pour les effets de particules.
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        # 'display_2' est une autre surface interne, utilisée pour dessiner le fond et les effets de silhouette.
        self.display_2 = pygame.Surface((320, 240))

        # L'horloge de Pygame, essentielle pour contrôler la vitesse du jeu (FPS)
        self.clock = pygame.time.Clock()
        
        # Liste pour suivre les mouvements du joueur (gauche, droite)
        self.movement = [False, False]
        
        # Dictionnaire central pour stocker toutes les ressources graphiques (images, animations)
        # Le jeu charge tout au démarrage pour éviter les ralentissements plus tard.
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'), # Gardé pour référence si nécessaire ailleurs, mais l'animation est clé.
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/attack_front': Animation(load_images('entities/player/attack_front'), img_dur=20, loop=False),
            'player/attack_up': Animation(load_images('entities/player/attack_up'), img_dur=20, loop=False),
            'player/attack_down': Animation(load_images('entities/player/attack_down'), img_dur=20, loop=False),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
            'weapon': load_image('entities/weapon/weapon.xcf'), 
        }
        
        # Dictionnaire pour stocker tous les effets sonores (SFX)
        self.sfx = {
            'jump': pygame.mixer.Sound(os.path.join(BASE_PATH, 'data/sfx/jump.wav')),
            'dash': pygame.mixer.Sound(os.path.join(BASE_PATH, 'data/sfx/dash.wav')),
            'hit': pygame.mixer.Sound(os.path.join(BASE_PATH, 'data/sfx/hit.wav')),
            'shoot': pygame.mixer.Sound(os.path.join(BASE_PATH, 'data/sfx/shoot.wav')),
            'ambience': pygame.mixer.Sound(os.path.join(BASE_PATH, 'data/sfx/ambience.wav')),
        }
        
        # Réglage du volume pour chaque effet sonore pour un meilleur mixage audio
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)
        
        self.clouds = Clouds(self.assets['clouds'], count=16)
        # Création de l'instance du joueur
        self.player = Player(self, (50, 50), (8, 15))
        # Création de l'instance de la carte (Tilemap)
        self.tilemap = Tilemap(self, tile_size=16)
        
        # Gestion du niveau actuel
        self.level = 0
        self.load_level(self.level)
        
        # Variable pour contrôler l'effet de secousse de l'écran
        self.screenshake = 0

        # --- Partie Réseau ---
        # Pour tester sur la même machine, utilisez "127.0.0.1" (localhost).
        # Pour jouer avec des amis sur internet, utilisez votre IP publique "82.65.71.205"
        # et assurez-vous que le port 5005 est ouvert sur votre routeur (port forwarding).
        self.net = ClientNetwork("127.0.0.1", 5005)
        self.net.connect()
        # Dictionnaire pour stocker les informations des autres joueurs reçues du serveur
        self.remote_players = {}
        
    def load_level(self, map_id):
        # Charge les données de la carte depuis un fichier .json
        self.tilemap.load(os.path.join(BASE_PATH, 'data/maps', str(map_id) + '.json'))
        
        # Trouve les tuiles d'arbres pour y faire apparaître des feuilles
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        # Initialise les listes pour les entités et effets du niveau
        self.enemies = []
        # Trouve les tuiles "spawner" sur la carte
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                # Le spawner de type 0 définit la position de départ du joueur
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                # Les autres spawners font apparaître des ennemis
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
            
        # Réinitialise les listes de projectiles, particules et étincelles
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        # Réinitialise la position de la caméra (scroll) et l'état du joueur
        self.scroll = [0, 0]
        self.dead = 0
        # La transition est utilisée pour l'effet de fondu (cercle) entre les niveaux
        self.transition = -30

        
    def run(self):
        # Charge et joue la musique de fond en boucle
        pygame.mixer.music.load(os.path.join(BASE_PATH, 'data/music.wav'))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        
        # Joue le son d'ambiance en boucle
        self.sfx['ambience'].play(-1)
        
        # --- BOUCLE DE JEU PRINCIPALE ---
        while True:
            # --- Logique Réseau ---
            # Envoie la position et la vitesse actuelles de notre joueur au serveur
            self.net.send_state(self.player.pos[0], self.player.pos[1], self.player.velocity[0], self.player.velocity[1])

            # Récupère les positions de tous les autres joueurs depuis le client réseau
            self.remote_players = self.net.players

            # --- Rendu (début) ---
            # Efface la surface de jeu principale (avec transparence pour voir ce qu'il y a derrière)
            self.display.fill((0, 0, 0, 0))
            # Dessine l'image de fond sur la deuxième surface
            self.display_2.blit(self.assets['background'], (0, 0))
            
            # Réduit progressivement l'effet de secousse de l'écran
            self.screenshake = max(0, self.screenshake - 1)
            
            # --- Logique de jeu ---
            # Si tous les ennemis sont vaincus, commence la transition vers le niveau suivant
            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    # Charge le niveau suivant (en s'assurant de ne pas dépasser le nombre de cartes disponibles)
                    self.level = min(self.level + 1, len(os.listdir(os.path.join(BASE_PATH, 'data/maps'))) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1
            
            # Si le joueur est mort
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    # Commence la transition de "mort"
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    # Recharge le niveau actuel
                    self.load_level(self.level)
            
            # --- Caméra ---
            # Fait en sorte que la caméra suive le joueur de manière fluide (effet de lissage)
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            # Crée une version arrondie du scroll pour éviter les problèmes de rendu avec des coordonnées flottantes
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            # --- Particules et Effets ---
            # Fait apparaître des feuilles depuis les arbres de manière aléatoire
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            # Met à jour et dessine les nuages en arrière-plan (avec effet de parallaxe)
            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)
            
            # Dessine la carte (les tuiles)
            self.tilemap.render(self.display, offset=render_scroll)
            
            # Met à jour et dessine chaque ennemi
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            
            # Met à jour et dessine le joueur s'il n'est pas mort
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)
            
            # Met à jour et dessine les projectiles (tirs ennemis)
            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                # Si le projectile touche un mur
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                # Si le projectile a une durée de vie trop longue
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                # Si le projectile touche le joueur (et que le joueur ne dashe pas)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            # Met à jour et dessine les étincelles
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                    
            # --- Effet de silhouette ---
            # Crée un "masque" à partir de tout ce qui a été dessiné sur 'display'
            display_mask = pygame.mask.from_surface(self.display)   
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset) # Dessine la silhouette décalée sur 'display_2' pour un effet de contour
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            # --- Gestion des entrées (clavier, souris, etc.) ---
            for event in pygame.event.get():
                # Si l'utilisateur ferme la fenêtre
                if event.type == pygame.QUIT:
                    self.net.disconnect()
                    pygame.quit()
                    sys.exit()
                # Si une touche est pressée
                if event.type == pygame.KEYDOWN:
                    # Mouvement horizontal
                    if event.key == pygame.K_LEFT or event.key == pygame.K_q:
                        self.movement[0] = True
                        self.player.is_pressed = 'left'
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                        self.player.is_pressed = 'right'
                    if event.key == pygame.K_UP or event.key == pygame.K_z:
                        self.player.is_pressed = 'up'
                    # On vérifie d'abord la touche, PUIS on tente de sauter.
                    if event.key == pygame.K_SPACE:
                        if self.player.request_jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        # On stocke l'information que la touche bas est pressée
                        self.player.is_pressed = 'down'
                    if event.key == pygame.K_x or event.key == pygame.K_LSHIFT:
                        self.player.dash()
                # Si une touche est relâchée
                if event.type == pygame.KEYUP or event.type == pygame.K_SPACE:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_q:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                    # Si on relâche une touche directionnelle, on réinitialise la variable
                    if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_d, pygame.K_a, pygame.K_SPACE, pygame.K_s]:
                        self.player.is_pressed = None
                # Si un bouton de la souris est pressé
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        # Vérifie les touches actuellement maintenues
                        keys = pygame.key.get_pressed()
                        if keys[pygame.K_UP] or keys[pygame.K_z]:
                            direction = 'up'
                        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                            direction = 'down'
                        elif keys[pygame.K_LEFT] or keys[pygame.K_q]:
                            direction = 'left'
                        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                            direction = 'right'
                        else:
                            direction = None  # aucune direction active

                        self.player.attack(direction)

                        
            # --- Rendu (fin) ---qqqd
            # Si une transition est en cours, dessine l'effet de cercle
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
            
            # --- Affichage des autres joueurs (partie réseau) ---
            for pid, (x, y, vx, vy) in self.remote_players.items():
                if pid != self.net.id:  # ne pas afficher soi-même
                    # Crée un simple rectangle vert pour représenter l'autre joueur
                    rect = pygame.Rect(
                        x - render_scroll[0],
                        y - render_scroll[1],
                        8, 15
                    )
                    pygame.draw.rect(self.display, (0, 255, 0), rect)
            # ----------------------------------------------------

            # Copie la surface de jeu (avec les personnages, tuiles, etc.) sur la surface de fond
            self.display_2.blit(self.display, (0, 0))
            
            # Calcule le décalage pour l'effet de secousse de l'écran
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            # Prend la surface finale ('display_2'), l'agrandit à la taille de l'écran, et l'affiche avec le décalage de secousse.
            # C'est ici que l'effet pixel-art est créé.
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)


            
            # Met à jour l'affichage complet de l'écran
            pygame.display.update()
            # Attend le temps nécessaire pour maintenir 60 images par seconde (FPS)
            self.clock.tick(60)

Game().run()
