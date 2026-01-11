import os
import sys
import math
import random

import pygame
from screeninfo import get_monitors

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, PurpleCircle, RemotePlayerRenderer
from scripts.weapon import Weapon
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

from scripts.shader_bg import ShaderBackground
from scripts.client_network import ClientNetwork
from scripts.controller import Controller  
from scripts.lighting import LightingSystem

###
# TIPS POUR MOI MEME pour les bugg lier au mouvement peut etre pour etduidier le gresillement je peux retirer l offset de la camera pour voir si c est la cam 
# le prob ou ma gestion du mouve en elle meme
###

def resource_path(relative_path):
    """Permet de trouver les fichiers quand le script est compilé en exe"""
    import sys
    import os
    try:
        # PyInstaller stocke les fichiers dans _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Game:
    def __init__(self, max_fps=60):  
        self.max_fps = max_fps
        pygame.init()

        pygame.display.set_caption('ninja game')
        monitors = get_monitors()
        for m in monitors:
            if m.is_primary:
                monitor = m
        print(f"Initialising game with width: {monitor.width} and height: {monitor.height}")
        self.screen = pygame.display.set_mode((monitor.width, monitor.height))
        
        self.base_resolution = (320, 180)
        self.zoom = 1.0
        SCALE = self.base_resolution
        
        self.display = pygame.Surface(SCALE, pygame.SRCALPHA)
        self.display_2 = pygame.Surface(SCALE)

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]
        
        self.assets = {
            'decor': load_images(resource_path('data/images/tiles/decor')),
            'grass': load_images(resource_path('data/images/tiles/grass')),
            'grassSpawner': load_images(resource_path('data/images/grass')),
            'large_decor': load_images(resource_path('data/images/tiles/large_decor')),
            'stone': load_images(resource_path('data/images/tiles/stone')),
            'player': load_image(resource_path('data/images/entities/player.png')),
            'background': load_image(resource_path('data/images/background.png')),
            'clouds': load_images(resource_path('data/images/clouds')),
            'enemy/idle': Animation(load_images(resource_path('data/images/entities/enemy/idle')), img_dur=6),
            'enemy/run': Animation(load_images(resource_path('data/images/entities/enemy/run')), img_dur=4),
            'player/idle': Animation(load_images(resource_path('data/images/entities/player/idle')), img_dur=6),
            'player/run': Animation(load_images(resource_path('data/images/entities/player/run')), img_dur=4),
            'player/attack_front': Animation(load_images(resource_path('data/images/entities/player/attack_front')), img_dur=20, loop=False),
            'player/attack_up': Animation(load_images(resource_path('data/images/entities/player/attack_up')), img_dur=20, loop=False),
            'player/attack_down': Animation(load_images(resource_path('data/images/entities/player/attack_down')), img_dur=20, loop=False),
            'player/jump': Animation(load_images(resource_path('data/images/entities/player/jump'))),
            'player/slide': Animation(load_images(resource_path('data/images/entities/player/slide'))),
            'player/wall_slide': Animation(load_images(resource_path('data/images/entities/player/wall_slide'))),
            'particle/leaf': Animation(load_images(resource_path('data/images/particles/leaf')), img_dur=20, loop=False),
            'particle/particle': Animation(load_images(resource_path('data/images/particles/particle')), img_dur=6, loop=False),
            'gun': load_image(resource_path('data/images/gun.png')),
            'projectile': load_image(resource_path('data/images/projectile.png')),
            'mace': Animation(load_images(resource_path('data/images/entities/weapon/mace'), True), img_dur=5, loop=False),
            'mace1': Animation(load_images(resource_path('data/images/entities/weapon/mace1'), True), img_dur=5, loop=False),
            'slashTriangle': Animation(load_images(resource_path('data/images/entities/weapon/slashTriangle'), True), img_dur=1.5, loop=False),
            'yokai2': Animation(load_images(resource_path('data/images/entities/enemy/yokai2'), True), img_dur=50, loop=True),
        }

        self.sfx = {
            'jump': pygame.mixer.Sound(resource_path('data/sfx/jump.wav')),
            'dash': pygame.mixer.Sound(resource_path('data/sfx/dash.wav')),
            'hit': pygame.mixer.Sound(resource_path('data/sfx/hit.wav')),
            'shoot': pygame.mixer.Sound(resource_path('data/sfx/shoot.wav')),
            'ambience': pygame.mixer.Sound(resource_path('data/sfx/ambience.wav')),
        }

        self.MUSIC_Volume = 0  ############# Volume global #############
        self.SFX_Volume = 0  ########### Volume des SFX #############
        self.music_on = False  # État de la musique (activée par défaut)

        # Ajuster les volumes
        self.sfx['ambience'].set_volume(self.SFX_Volume)
        self.sfx['shoot'].set_volume(self.SFX_Volume)
        self.sfx['hit'].set_volume(self.SFX_Volume)
        self.sfx['dash'].set_volume(self.SFX_Volume)
        self.sfx['jump'].set_volume(self.SFX_Volume)

        
        self.clouds = Clouds(self.assets['clouds'], count=5)
        
        self.player = Player(self, (50, 50), (8, 15))

        self.enemies_renderer = PurpleCircle(self)
        self.remote_players_renderer = RemotePlayerRenderer(self)
        
        self.tilemap = Tilemap(self, tile_size=16)
        
        self.level = 0
        self.load_level(self.level)
        
        self.screenshake = 0

        self.net = ClientNetwork("127.0.0.1", 5006)
        self.net.connect()
        self.remote_players = {}
        
        self.shader_bg = ShaderBackground(SCALE[0], SCALE[1], "data/shaders/3.4.frag")

        self.controller = Controller()

        self.lighting = LightingSystem(self.display.get_size())

        self.weapon_type = 'mace' # On commence avec la lance
        self.weaponDictionary = {1: 'slashTriangle', 2: 'mace1', 3: 'mace'}
        self.currentWeaponIndex = 1

        self.font = pygame.font.SysFont("consolas", 16)
        self.debug = True

    def set_zoom(self, zoom_value):
        self.zoom = max(0.5, min(zoom_value, 2.0))
        
        new_width = int(self.base_resolution[0] / self.zoom)
        new_height = int(self.base_resolution[1] / self.zoom)
        SCALE = (new_width, new_height)
        
        self.display = pygame.Surface(SCALE, pygame.SRCALPHA)
        self.display_2 = pygame.Surface(SCALE)
        
        self.shader_bg.resize(SCALE[0], SCALE[1])

        self.lighting.size = SCALE

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        # Plus besoin de charger les ennemis localement - ils sont gérés par le serveur
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

        
    def run(self):
        pygame.mixer.music.load(resource_path('data/music/musicDynamiqueLoop.mp3'))
        pygame.mixer.music.set_volume(self.MUSIC_Volume)
        pygame.mixer.music.play(-1)
        
        #self.sfx['ambience'].play(-1)
        
        while True:
            dt = self.clock.tick(self.max_fps) / 1000  # dt en secondes
            
            # --- Check Server Level Change ---
            if self.net.map_change_id is not None:
                new_map_id = self.net.map_change_id
                self.net.map_change_id = None
                self.level = new_map_id
                self.load_level(self.level)
            
            # --- PLAYER UPDATE ---
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0),dt=dt)

            action_mapping = {
                "idle": 0, "run": 1, "jump": 2, "wall_slide": 3, "slide": 4,
                # Ajout des actions d'attaque
                "attack_front": 5,
                "attack_up": 6,
                "attack_down": 7,
            }

            action_id = action_mapping[self.player.action]
            flip_byte = 1 if self.player.flip else 0
            self.net.send_state(self.player.pos[0], self.player.pos[1], action_id, flip_byte)

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0])  #/5 # smooth cam
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) #/5 # smooth cam
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.remote_players = self.net.remote_players

            self.display.fill((0, 0, 0, 0))
            # --- BACKGROUND ---
            shader_surface = self.shader_bg.render(camera=(render_scroll[0] * 0.2, render_scroll[1] * -0.2))
            self.display_2.blit(shader_surface, (0, 0))
            self.clouds.render(self.display_2, offset=render_scroll)


            self.screenshake = max(0, self.screenshake - 1)

            if self.transition < 0:
                self.transition += 1
            
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)
            
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            # --- TILEMAP / GRASS ---
            self.tilemap.render(self.display, offset=render_scroll)
            self.tilemap.grass_manager.update_render(self.display, 1/10, offset=render_scroll,
                rot_function=lambda x, y: int(math.sin(x / 100 + pygame.time.get_ticks() / 300) * 30) / 10)

            # --- ENEMIES ---
            self.enemies_renderer.update()
            self.enemies_renderer.render(self.display, offset=render_scroll)

            # --- PLAYER RENDER ---
            if not self.dead:
                self.player.render(self.display, offset=render_scroll)

            # [[x, y], direction, timer]
            #for projectile in self.projectiles.copy():
            #    projectile[0][0] += projectile[1]
            #    projectile[2] += 1
            #    img = self.assets['projectile']
            #    self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
            #    if self.tilemap.solid_check(projectile[0]):
            #        self.projectiles.remove(projectile)
            #    for i in range(4):
            #            self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
            #    elif projectile[2] > 360:
            #        self.projectiles.remove(projectile)
            #    elif abs(self.player.dashing) < 50:
            #        if self.player.rect().collidepoint(projectile[0]):
            #            self.projectiles.remove(projectile)
            #            self.dead += 1
            #            self.sfx['hit'].play()
            #            self.screenshake = max(16, self.screenshake)
            #            for i in range(30):
            #                angle = random.random() * math.pi * 2
            #                speed = random.random() * 5
            #                self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
            #                self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(pygame.time.get_ticks() * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            # --- REMOTE PLAYERS ---
            self.remote_players_renderer.render(self.display, offset=render_scroll)

            self.display_2.blit(self.display, (0, 0))

            for event in pygame.event.get():
                # Si l'utilisateur ferme la fenêtre
                if event.type == pygame.QUIT:
                    self.net.disconnect()
                    pygame.quit()
                    sys.exit()
                # Si une touche est pressée
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        event.type = pygame.QUIT
                    if event.key == pygame.K_F1:
                        self.player.weapon.weapon_equiped.toggle_debug()
                        self.debug = not self.debug
                    if event.key == pygame.K_F2:
                        self.music_on = not self.music_on # Inverse l'état (True devient False et inversement)
                        
                        if self.music_on:
                            self.MUSIC_Volume = 0.5  
                            self.SFX_Volume = 0.5
                            pygame.mixer.music.set_volume(self.MUSIC_Volume)
                            self.sfx['ambience'].set_volume(self.SFX_Volume)
                            self.sfx['shoot'].set_volume(self.SFX_Volume)
                            self.sfx['hit'].set_volume(self.SFX_Volume)
                            self.sfx['dash'].set_volume(self.SFX_Volume)
                            self.sfx['jump'].set_volume(self.SFX_Volume)
                            print("Musique activée")
                        else:
                            self.MUSIC_Volume = 0  
                            self.SFX_Volume = 0
                            pygame.mixer.music.set_volume(self.MUSIC_Volume)
                            self.sfx['ambience'].set_volume(self.SFX_Volume)
                            self.sfx['shoot'].set_volume(self.SFX_Volume)
                            self.sfx['hit'].set_volume(self.SFX_Volume)
                            self.sfx['dash'].set_volume(self.SFX_Volume)
                            self.sfx['jump'].set_volume(self.SFX_Volume)
                            print("Musique coupée")
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
                    if event.key == pygame.K_c:
                        self.currentWeaponIndex = (self.currentWeaponIndex % len(self.weaponDictionary)) + 1
                        self.weapon_type = self.weaponDictionary[self.currentWeaponIndex]
                        self.player.weapon.set_weapon(self.weapon_type)
                    if event.key == pygame.K_n:
                        self.net.send_map_change_request()

                    # Zoom dezoom :D
                    if event.key == pygame.K_KP_PLUS or event.key == pygame.K_PLUS:
                         self.set_zoom(self.zoom + 0.1)
                    if event.key == pygame.K_KP_MINUS or event.key == pygame.K_MINUS:
                         self.set_zoom(self.zoom - 0.1)
                            
                if event.type == pygame.MOUSEWHEEL:
                    self.set_zoom(self.zoom + event.y * 0.1)

                # Si une touche est relâchée
                if event.type == pygame.KEYUP or event.type == pygame.K_SPACE:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_q:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                    # Si on relâche une touche directionnelle on reinit la variable
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
                            direction = None  

                        self.player.attack(direction)

            self.controller.update() #Pour la mannette
            if self.controller.joystick:  # Si une manette est connectée
                if self.controller.button_a:
                    if self.player.jump():
                        self.sfx['jump'].play()
                if self.controller.button_b:
                    self.player.dash()

                move_x = 0
                if self.controller.left_stick_x < -0.5 or self.controller.dpad_left:
                    move_x = -1
                elif self.controller.left_stick_x > 0.5 or self.controller.dpad_right:
                    move_x = 1
                self.movement = [move_x < 0, move_x > 0]

                if self.controller.left_trigger > 0.2:
                    self.player.dash()
                if self.controller.right_trigger > 0.2:
                    self.player.dash()

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display_2.blit(transition_surf, (0, 0))

            
            #self.tilemap.grass_manager.update_render(self.display,1/60, offset=self.scroll)
            #gd.grass_manager.update_render(display, 1 / 60, offset=gd.scroll.copy(), rot_function=lambda x, y: int(math.sin(x / 100 + global_time / 40) * 30) / 10)
            self.tilemap.grass_manager.update_render(self.display, 1/10, offset=render_scroll, rot_function=lambda x, y: int(math.sin(x / 100 + pygame.time.get_ticks() / 300) * 30) / 10)

            """
            # --- APPLICATION DE L’ÉCLAIRAGE APRÈS TOUT ---
            light_sources = [
                (self.player.rect().centerx - render_scroll[0],
                self.player.rect().centery - render_scroll[1],
                300, (220, 240, 255))
            ]
            self.lighting.render(self.display_2, light_sources, pygame.time.get_ticks())
            """
            # --- AFFICHAGE FINAL ---
            screenshake_offset = (
                random.random() * self.screenshake - self.screenshake / 2,
                random.random() * self.screenshake - self.screenshake / 2
            )
            self.screen.blit(
                pygame.transform.scale(self.display_2, self.screen.get_size()),
                screenshake_offset
            )

            # --- AFFICHAGE DES FPS ---
            if self.debug:
                fps = int(self.clock.get_fps())
                fps_color = (0, 255, 0) if fps >= 55 else (255, 255, 0) if fps >= 30 else (255, 0, 0)
                fps_text = self.font.render(f"FPS: {fps}", True, fps_color)
                self.screen.blit(fps_text, (10, 10))

                ping = int(self.net.ping)
                ping_color = (0, 255, 0) if ping < 80 else (255, 255, 0) if ping < 150 else (255, 0, 0)
                ping_text = self.font.render(f"Ping: {ping} ms", True, ping_color)
                self.screen.blit(ping_text, (10, 30))


            pygame.display.update()

if __name__ == "__main__":
    Game().run()