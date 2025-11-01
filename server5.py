import socket
import struct
import time
import random
import miniupnpc

# ==============================
# --- Player Manager ---
# ==============================
class PlayerManager:
    def __init__(self):
        self.clients = {}   # addr -> id
        self.players = {}   # id -> (x, y, vx, vy)
        self.next_id = 1

    def add_player(self, addr):
        pid = self.next_id
        self.next_id += 1
        self.clients[addr] = pid
        self.players[pid] = (0, 0, 0, 0)
        return pid

    def remove_player(self, addr):
        if addr not in self.clients:
            return
        pid = self.clients[addr]
        del self.clients[addr]
        if pid in self.players:
            del self.players[pid]
        return pid

    def update_player(self, addr, data):
        if addr not in self.clients:
            return
        pid = self.clients[addr]
        x, y, vx, vy = struct.unpack("ffff", data)
        self.players[pid] = (x, y, vx, vy)

# ==============================
# --- Enemy Manager ---
# ==============================
class EnemyManager:
    def __init__(self, num_enemies=20, speed=0.5):
        self.enemies = {}
        self.next_enemy_id = 1
        self.speed = speed
        self.create_enemies(num_enemies)

    def create_enemies(self, num):
        for _ in range(num):
            eid = self.next_enemy_id
            self.next_enemy_id += 1
            self.enemies[eid] = {
                'x': random.uniform(-100, 100),
                'y': random.uniform(-100, 100),
                'target_player': None
            }
        print(f"{num} ennemis créés !")

    def update(self, players):
        for eid, enemy in self.enemies.items():
            if not players:
                continue

            # Trouver la cible la plus proche
            ex, ey = enemy['x'], enemy['y']
            closest_pid = min(
                players,
                key=lambda pid: (players[pid][0] - ex)**2 + (players[pid][1] - ey)**2
            )
            enemy['target_player'] = closest_pid

            # Se déplacer vers la cible
            px, py, _, _ = players[closest_pid]
            dx, dy = px - ex, py - ey
            dist = (dx**2 + dy**2)**0.5
            if dist > 5:
                enemy['x'] += (dx / dist) * self.speed
                enemy['y'] += (dy / dist) * self.speed

# ==============================
# --- Game Server ---
# ==============================
class GameServer:
    def __init__(self, ip="0.0.0.0", port=5005, rate=1/30):
        self.ip = ip
        self.port = port
        self.rate = rate
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))

        self.players = PlayerManager()
        self.enemies = EnemyManager()
        self.last_update = time.time()

        print(f"Serveur en ligne sur {ip}:{port}")
        self.init_upnp()

    def init_upnp(self):
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 200
        upnp.discover()
        upnp.selectigd()
        try:
            upnp.addportmapping(self.port, 'UDP', upnp.lanaddr, self.port, 'Python Game Server', '')
            print(f"UPnP : port {self.port} ouvert ! IP publique : {upnp.externalipaddress()}")
        except Exception as e:
            print("UPnP non disponible :", e)

    def run(self):
        print("Serveur en cours d’exécution...")
        try:
            while True:
                data, addr = self.sock.recvfrom(1024)
                self.handle_message(data, addr)
                now = time.time()
                if now - self.last_update >= self.rate:
                    self.last_update = now
                    self.update_world()
        except KeyboardInterrupt:
            print("Arrêt du serveur...")
            self.sock.close()

    def handle_message(self, data, addr):
        msg_type = data[0]

        # Connexion
        if addr not in self.players.clients and msg_type == 0:
            pid = self.players.add_player(addr)
            self.sock.sendto(struct.pack("I", pid), addr)
            print(f"Nouveau joueur {pid} ({addr})")
            return

        # Déconnexion
        if msg_type == 1:
            pid = self.players.remove_player(addr)
            print(f"Déconnexion du joueur {pid}")
            # Enlever les cibles
            for e in self.enemies.enemies.values():
                if e['target_player'] == pid:
                    e['target_player'] = None
            return

        # Update position joueur
        if msg_type == 0 and addr in self.players.clients and len(data) >= 17:
            self.players.update_player(addr, data[1:17])

    def update_world(self):
        self.enemies.update(self.players.players)
        self.broadcast_state()

    def broadcast_state(self):
        payload = struct.pack("B", len(self.players.players))
        for pid, (x, y, vx, vy) in self.players.players.items():
            payload += struct.pack("Iffff", pid, x, y, vx, vy)

        payload += struct.pack("B", len(self.enemies.enemies))
        for eid, e in self.enemies.enemies.items():
            payload += struct.pack("Iff", eid, e['x'], e['y'])

        for addr in self.players.clients:
            self.sock.sendto(payload, addr)

# ==============================
# --- Lancement ---
# ==============================
if __name__ == "__main__":
    server = GameServer()
    server.run()
