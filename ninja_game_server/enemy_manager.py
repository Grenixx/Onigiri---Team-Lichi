import random
from math import *

class EnemyManager:
    def __init__(self, tilemap, num_enemies=1, speed=0.5):
        self.tilemap = tilemap
        self.enemies = {}
        self.next_enemy_id = 1
        self.speed = speed
        self.create_blob(num_enemies)

    def create_blob(self, num):
        for _ in range(num):
            eid = self.next_enemy_id
            self.next_enemy_id += 1
            self.enemies[eid] = {
                'x': 250,
                'y': 0,
                'vx': 0.0,
                'vy': 0.0,
                'target_player': None,
            }
        print(f"{num} ennemis créés !")

    def update(self, players):
        """Met à jour tous les ennemis en fonction de la map et des joueurs"""
        if not players:
            return

        for eid, enemy in self.enemies.items():
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

            enemy['target_player'] = closest_pid
            #print("angle",angle(vector_to(pos, players[closest_pid])))
            #print("distance",distane_to(pos, players[closest_pid]))
            print(raycast_collide(pos, angle(vector_to(pos, players[closest_pid])), self.tilemap, distane_to(pos, players[closest_pid]) - 1, 4))

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
            #print(enemy['vy'])

            # Limites de la map
            enemy['x'] = max(0, min(enemy['x'] + enemy['vx'], 1000))
            enemy['y'] = max(0, min(enemy['y'] + enemy['vy'], 1000))

            enemy['vy'] = 0

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

def raycast_collide(pos: list, angle: float, tilemap, dist_max: float = 1000, dist_check: float = 4, mask: list = []):
    """
    
    """
    vec = vec_from_angle(dist_check, angle)
    print(vec)
    dist = 0
    pos_check = pos
    while dist <= dist_max:
        check_type = tilemap.check_type((pos_check))
        if (mask == [] and check_type != None) or (check_type in mask):
            return True
        pos_check = add_vecs(pos_check, vec)
        dist += dist_check
    return False

def raycast_pos(pos: list, angle: float, tilemap, dist_max: float = 1000, dist_check: float = 4, precision : int = 4, mask: list = []):
    """
    
    """
    vec = vec_from_angle(dist_check, angle)
    pos_check = pos
    hit = False
    while not hit:
        if distane_to(pos,pos_check) <= dist_max:
            return None
        check_type = tilemap.check_type((pos_check[0], pos_check[1]))
        if (mask == [] and check_type != None) or (check_type in mask):
            hit = True
        else:
            pos_check += vec
    
    for _ in range(precision):
        vec = [i / 2 for i in vec]
        if (mask == [] and check_type != None) or (check_type in mask):
            pos_check = sub_vecs(pos_check, vec)
        else:
            pos_check = add_vecs(pos_check, vec)
        check_type = tilemap.check_type((pos_check[0], pos_check[1]))
    return pos_check