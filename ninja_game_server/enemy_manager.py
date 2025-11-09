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
            self.create_blob([random.randint(100,250), random.randint(40,100)])

    def create_blob(self, pos: list):
        eid = self.next_enemy_id
        self.next_enemy_id += 1
        self.enemies[eid] = {
            'x': pos[0],
            'y': pos[1],
            'vx': 0.0,
            'vy': 0.0,
            'target_player': None,
        }
        print(f"ennemi créés en {pos} !")

    def update(self, players):
        """Met à jour tous les ennemis en fonction de la map et des joueurs"""
        if not players:
            return

        def can_see_player(enemy, pid):
            return not raycast_collide([enemy['x'], enemy['y']], angle(vector_to([enemy['x'], enemy['y']], players[pid])), self.tilemap, distane_to([enemy['x'], enemy['y']], players[pid]) - 10, 4, PHYSICS_TILES)
        
        enemies = list_copy(self.enemies.items()) #dict can change size when running for loop
        for eid, enemy in enemies:
            pos = [enemy['x'], enemy['y']]
            
            # --- Gravité ---
            if not self.tilemap.solid_check((pos[0], pos[1] + 4)):
                enemy['vy'] += 0  # tombe
            else:
                enemy['vy'] = 0

            # --- Trouver la cible la plus proche ---
            closest_dist = None
            closest_pid = None
            for pid in players.keys():
                dist = distance_squared_to(pos, players[pid])
                if closest_dist == None or closest_dist > dist:
                    closest_dist,closest_pid = dist,pid

            if can_see_player(enemy, closest_pid):
                enemy['target_player'] = closest_pid
                step = [0,0]
                dist = distane_to(pos, players[closest_pid])
                if dist > 1:
                    step = normalized(vector_to(pos, players[closest_pid]))
                    step = [i * self.speed for i in step]

                # --- Test collisions map ---
                new_x = pos[0] + step[0]
                new_y = pos[1] + step[1] + enemy['vy']

                if not self.tilemap.solid_check((new_x, pos[1])):
                    enemy['vx'] = step[0]
                else:
                    enemy['vx'] = 0

                if not self.tilemap.solid_check((pos[0], new_y)):
                    enemy['vy'] += step[1]
                else:
                    enemy['vy'] = 0

                # Limites de la map
                enemy['x'] = max(0, min(enemy['x'] + enemy['vx'], 1000))
                enemy['y'] = max(0, min(enemy['y'] + enemy['vy'], 1000))

                enemy['vy'] = 0

            else:
                enemy['target_player'] = None
                enemy['vx'], enemy['vy'] = 0,0
                
                # test
                if random.randint(0, 500) == 0:
                    new_blob_pos = raycast_pos(pos, angle(vector_to(pos, players[pid])), self.tilemap, distane_to(pos, players[pid]) - 10, 4, 10, PHYSICS_TILES, True)
                    if new_blob_pos != None:
                        self.create_blob(new_blob_pos)
                    else:
                        print("raycast_pos failed")

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