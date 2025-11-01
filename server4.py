import socket
import struct
import time
import random
import miniupnpc

# --- Configuration du serveur ---
SERVER_IP = "0.0.0.0"
SERVER_PORT = 5005
UPDATE_RATE = 1 / 30

# --- UPnP : ouvrir le port sur le routeur ---
upnp = miniupnpc.UPnP()
upnp.discoverdelay = 200
print("Recherche du routeur UPnP...")
upnp.discover()
upnp.selectigd()

try:
    upnp.addportmapping(SERVER_PORT, 'UDP', upnp.lanaddr, SERVER_PORT, 'Python Game Server', '')
    print(f"Port {SERVER_PORT} ouvert via UPnP !")
    print(f"IP publique : {upnp.externalipaddress()}")
except Exception as e:
    print("Impossible d'ouvrir le port via UPnP :", e)

# --- Serveur UDP ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))
print(f"Server running on {SERVER_IP}:{SERVER_PORT}")

clients = {}   # addr -> id
players = {}   # id -> (x, y, vx, vy)
enemies = {}   # enemy_id -> {'x': float, 'y': float, 'target_player': int or None}
next_id = 1
next_enemy_id = 1
last_update = time.time()

ENEMY_SPEED = 0.5
NUM_ENEMIES = 20   # nombre d’ennemis globaux

# --- ✅ Créer les ennemis dès le début ---
for i in range(NUM_ENEMIES):
    enemy_id = next_enemy_id
    next_enemy_id += 1
    enemies[enemy_id] = {
        'x': random.uniform(-500, 500),
        'y': random.uniform(-500, 500),
        'target_player': None
    }
print(f"{NUM_ENEMIES} ennemis créés au démarrage du serveur !")

try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if not data:
                continue
 
            msg_type = data[0]

            # --- Nouveau joueur ---
            if addr not in clients and msg_type == 0:
                clients[addr] = next_id
                players[next_id] = (0, 0, 0, 0)
                print(f"New player {next_id} connected {addr}")
                
                sock.sendto(struct.pack("I", next_id), addr)
                next_id += 1
                continue

            # --- Déconnexion ---
            elif msg_type == 1:
                if addr in clients:
                    pid = clients[addr]
                    print(f"Player {pid} disconnected {addr}")
                    del players[pid]
                    del clients[addr]
                    # Supprimer la cible des ennemis de ce joueur
                    for enemy in enemies.values():
                        if enemy['target_player'] == pid:
                            enemy['target_player'] = None
                continue

            # --- Update position joueur ---
            if msg_type == 0 and addr in clients:
                pid = clients[addr]
                if len(data) >= 17:
                    x, y, vx, vy = struct.unpack("ffff", data[1:17])
                    players[pid] = (x, y, vx, vy)
            
            # --- Envoi des mises à jour ---
            now = time.time()
            if now - last_update >= UPDATE_RATE:
                last_update = now
                
                # --- Déplacement des ennemis ---
                for eid, enemy in enemies.items():
                    # Trouver une cible si besoin
                    #if enemy['target_player'] not in players and players:
                    ex, ey = enemy['x'], enemy['y']
                    closest_player = None
                    closest_dist = float('inf')
                    for pid, (px, py, _, _) in players.items():
                        dist = ((px - ex)**2 + (py - ey)**2)**0.5
                        if dist < closest_dist:
                            closest_dist = dist
                            closest_player = pid
                    enemy['target_player'] = closest_player

                    # Se déplacer vers la cible
                    target = enemy['target_player']
                    if target and target in players:
                        px, py, _, _ = players[target]
                        ex, ey = enemy['x'], enemy['y']
                        dx = px - ex
                        dy = py - ey
                        dist = (dx**2 + dy**2)**0.5
                        if dist > 5:
                            enemy['x'] += (dx / dist) * ENEMY_SPEED
                            enemy['y'] += (dy / dist) * ENEMY_SPEED

                # --- Construire et envoyer les données ---
                payload = struct.pack("B", len(players))
                for pid, (px, py, pvx, pvy) in players.items():
                    payload += struct.pack("Iffff", pid, px, py, pvx, pvy)
                
                payload += struct.pack("B", len(enemies))
                for eid, enemy in enemies.items():
                    payload += struct.pack("Iff", eid, enemy['x'], enemy['y'])
                
                for c in clients:
                    sock.sendto(payload, c)

        except Exception as e:
            # print("Error:", e)
            pass

except KeyboardInterrupt:
    print("Fermeture du serveur...")
    try:
        upnp.deleteportmapping(SERVER_PORT, 'UDP')
        print("Redirection UPnP supprimée.")
    except:
        pass
    sock.close()
