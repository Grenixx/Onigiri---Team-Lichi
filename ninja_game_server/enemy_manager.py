import random
from math import *

from TilemapServer import PHYSICS_TILES

class EnemyManager:
    def __init__(self, tilemap, num_enemies=200, speed=1.5):
        self.tilemap = tilemap
        self.enemies = {}
        self.next_enemy_id = 1
        self.speed = speed
        for _ in range(num_enemies):
            self.create_enemy([random.randint(100,250), random.randint(40,100)], "blob")

    def create_enemy(self, pos: list, enemy_type: str):
        enemy_types = {"blob": Blob}
        self.enemies[self.next_enemy_id] = enemy_types[enemy_type](self.next_enemy_id, pos, self)
        self.next_enemy_id += 1

    def update(self, players):
        """Met à jour tous les ennemis en fonction de la map et des joueurs"""
        if not players:
            return
        
        enemies = list_copy(self.enemies.items()) #dict can change size when running for loop
        for eid, enemy in enemies:
            enemy.physics_process(0.0, self.tilemap)

class Enemy:
    def __init__(self, eid, pos, enemy_manager):
        self.eid = eid
        self.properties = {
            'x': pos[0],
            'y': pos[1],
            'vx': 0.0,
            'vy': 0.0,
            'target_player': None,
        }
        self.enemy_manager = enemy_manager
        print(f"ennemi créé en {pos} !")
    def can_see_player(self, player, tilemap):
        return not raycast_collide([self.properties['x'], self.properties['y']], 
                                    angle(vector_to([self.properties['x'], self.properties['y']], player)),
                                    tilemap,
                                    distane_to([self.properties['x'], self.properties['y']], player) - 10,
                                    4,
                                    PHYSICS_TILES
                                    )
    def create_enemy(self, pos: list, enemy_type: str):
        self.enemy_manager.create_enemy(pos, enemy_type)

class Blob(Enemy):
    def __init__(self, eid, pos, enemy_manager):
        super().__init__(eid, pos, enemy_manager)
    
    def physics_process(self, delta: float, players: list, ):
        pos = [self.properties['x'], self.properties['y']]
        velocity = [self.properties['vx'], self.properties['vy']]

        # --- Gravité ---
        if not self.tilemap.solid_check((pos[0], pos[1] + 4)):
            velocity[1] += 0  # tombe
        else:
            velocity[1] = 0

        # --- Trouver la cible la plus proche ---
        closest_dist = None
        closest_pid = None
        for pid in players.keys():
            dist = distance_squared_to(pos, players[pid])
            if closest_dist == None or closest_dist > dist:
                closest_dist,closest_pid = dist,pid

        if distane_to(pos, players[closest_pid]) < 16*30 and self.can_see_player(self.properties, players[closest_pid]):
            self.properties['target_player'] = closest_pid
            step = [0,0]
            dist = distane_to(pos, players[closest_pid])
            if dist > 1:
                step = normalized(vector_to(pos, players[closest_pid]))
                step = [i * self.speed for i in step]

            # --- Test collisions map ---
            new_x = pos[0] + step[0]
            new_y = pos[1] + step[1] + velocity[1]

            if not self.tilemap.solid_check((new_x, pos[1])):
                velocity[0] = step[0]
            else:
                velocity[0] = 0

            if not self.tilemap.solid_check((pos[0], new_y)):
                velocity[1] += step[1]
            else:
                velocity[1] = 0

            # Limites de la map
            pos[0] = max(0, min(pos[0] + velocity[0], 1000))
            pos[1] = max(0, min(pos[1] + velocity[1], 1000))

            velocity[1] = 0

        else:
            self.properties['target_player'] = None
            velocity = [0,0]
            
            # test
            if random.randint(0, 500) == 0:
                new_blob_pos = raycast_pos(pos, angle(vector_to(pos, players[pid])), self.tilemap, distane_to(pos, players[pid]) - 10, 4, 10, PHYSICS_TILES, True)
                if new_blob_pos != None:
                    EnemyManager.create_enemy(new_blob_pos, "blob")
                else:
                    print("raycast_pos failed")
        self.properties['x'] = pos[0]
        self.properties['y'] = pos[1]
        self.properties['vx'] = velocity[0]
        self.properties['vy'] = velocity[1]

def list_copy(lst):
    """
    Empêche les effets de bord dans les listes
    """
    return [i for i in lst]

def add_vecs(vec1: list, vec2: list):
    return [vec1[i] + vec2[i] for i in range(2)]

def sub_vecs(vec1: list, vec2: list):
    return [vec1[i] - vec2[i] for i in range(2)]

def vector_to(pos1: list,pos2: list):
    """
    Renvoie un vecteur de la position 1 vers 2
    """
    return [pos2[0] - pos1[0], pos2[1] - pos1[1]]

def distance_squared_to(pos1: list,pos2: list):
    """
    Renvoie la distance au carré entre la position 1 et 2
    """
    vec = vector_to(pos1,pos2)
    return vec[0] ** 2 + vec[1] ** 2

def distane_to(pos1: list,pos2: list):
    """
    Renvoie la distance entre la position 1 et 2
    """
    return sqrt(distance_squared_to(pos1,pos2))

def norm(vec: list):
    return distane_to([0,0],vec)

def normalized(vec: list):
    """
    Renvoie le vecteur passé en entrée normalisé
    """
    norm = distane_to([0,0],vec)
    vec = [i/norm for i in vec]
    return vec

def is_normalized(vec: list):
    """
    Vérifie si le vecteur est normalisé
    """
    return norm(vec) == 1

def vec_from_angle(norm: float, angle: float):
    return [cos(angle) * norm, sin(angle) * norm]

def angle(vec: list):
    n = norm(vec)
    if n == 0:
        return 0
    ax = acos(vec[0] / n)
    ay = asin(vec[1] / n)
    if ax == ay:
        return ax
    if ay < 0:
        if ax < pi / 2:
            return ay
        return -ax
    return ax

def is_within(pos, pos1, pos2):
    pos_r1 = [pos1[i] <= pos[i] and pos2[i] >= pos[i] for i in range(2)]
    pos_r2 = [pos1[i] >= pos[i] and pos2[i] <= pos[i] for i in range(2)]
    return (pos_r1[0] and pos_r1[1]) or (pos_r2[0] and pos_r2[1])

def raycast_collide(pos: list, angle: float, tilemap, dist_max: float = 1000, dist_check: float = 4, mask: list = [], return_pos: bool = False):
    """
    
    """
    vec = vec_from_angle(dist_check, angle)
    dist = 0
    pos_check = pos
    while dist <= dist_max:
        check_type = tilemap.check_type((pos_check))
        if (mask == [] and check_type != None) or (check_type in mask):
            if return_pos:
                return pos_check
            return True
        pos_check = add_vecs(pos_check, vec)
        dist += dist_check
    return False

def is_round(num):
    return round(num) == num

def is_almost_round(num, margin):
    return floor(num) != floor(num + margin) or floor(num) != floor(num - margin)

def round_pos_if_possible(pos, margin):
    return [round(i) if is_almost_round(i, margin) else i for i in pos]

def raycast_pos(pos: list, angle: float, tilemap, dist_max: float = 1000, dist_check: float = 4, precision : int = 4, mask: list = [], fix_collisions: bool = False):
    """
    
    """
    vec = vec_from_angle(dist_check, angle)
    dist = 0
    pos_check = raycast_collide(pos, angle, tilemap, dist_max, dist_check, mask, True)
    if not pos_check:
        return None
    
    for _ in range(precision):
        vec = [i / 2 for i in vec]
        check_type = tilemap.check_type((pos_check))
        if (mask == [] and check_type != None) or (check_type in mask):
            pos_check = sub_vecs(pos_check, vec)
        else:
            pos_check = add_vecs(pos_check, vec)
    
    # Ajustements
    if precision >= 10:
        pos_check = round_pos_if_possible(pos_check, dist_check * 2**-(precision - 1))
        if fix_collisions:
            if is_round(pos_check[0]) and angle >= -pi/2 and angle <= pi/2: # collide left side of tile
                pos_check[0] -= 0.0000000000001
            if is_round(pos_check[1]) and angle >= 0 and angle <= pi: # collide up side of tile
                pos_check[1] -= 0.0000000000001

    return pos_check

""" todo:
create class for raycast and vectors
add documentation
add side of block raycast hit in class
"""