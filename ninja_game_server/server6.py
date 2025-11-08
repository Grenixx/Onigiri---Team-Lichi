import socket
import struct
import time
import miniupnpc

from TilemapServer import TilemapServer
from enemy_manager import EnemyManager

# Message types:
#  10 : Connexion
#   1 : Déconnexion
#   0 : Mise à jour du joueur (position/action)
#   3 : Suppression d’un ennemi



# ==============================
# --- Player Manager ---
# ==============================
class PlayerManager:
    def __init__(self):
        self.clients = {}   # addr -> id
        self.players = {}   # id -> (x, y, action:str, flip:bool)
        self.next_id = 1

    def add_player(self, addr):
        pid = self.next_id
        self.next_id += 1
        self.clients[addr] = pid
        self.players[pid] = (0, 0, 'idle', False)
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

        if len(data) < 10:
            return  # paquet trop court

        x, y = struct.unpack("ff", data[:8])
        action_id, flip_byte = struct.unpack("BB", data[8:10])
        action_map = {0: 'idle', 1: 'run', 2: 'jump', 3: 'wall_slide', 4: 'slide'}
        action = action_map.get(action_id, 'idle')
        flip = bool(flip_byte)
        self.players[pid] = (x, y, action, flip)


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

        # --- Charger la map ---
        self.map = TilemapServer()
        self.map.load("data/maps/1.json")
        print("carte chargée sur le serveur.")

        # --- Managers ---
        self.players = PlayerManager()
        self.enemies = EnemyManager(self.map)
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

    # ---------------------------
    # --- Boucle principale ---
    # ---------------------------
    def run(self):
        print("Serveur en cours d’exécution...")
        try:
            while True:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    self.handle_message(data, addr)
                except ConnectionResetError:
                    # Ignore les erreurs quand un client quitte brutalement
                    continue
                except OSError as e:
                    print("Erreur socket:", e)
                    continue

                now = time.time()
                if now - self.last_update >= self.rate:
                    self.last_update = now
                    self.update_world()
        except KeyboardInterrupt:
            print("Arrêt du serveur...")
            self.sock.close()

    # ---------------------------
    # --- Gestion messages ---
    # ---------------------------
    def handle_message(self, data, addr):
        msg_type = data[0]

        # --- Connexion ---
        if msg_type == 10:  # 10 = connexion
            if addr not in self.players.clients:
                pid = self.players.add_player(addr)
                self.sock.sendto(struct.pack("I", pid), addr)
                print(f"Nouveau joueur {pid} ({addr})")
            return


        # --- Déconnexion ---
        if msg_type == 1:
            pid = self.players.remove_player(addr)
            print(f"Déconnexion du joueur {pid}")
            # Supprime la cible si l’ennemi le suivait
            for e in self.enemies.enemies.values():
                if e['target_player'] == pid:
                    e['target_player'] = None
            return

        # --- Mise à jour joueur ---
        if msg_type == 0 and addr in self.players.clients and len(data) >= 10:
            self.players.update_player(addr, data[1:])

        # --- Suppression ennemi ---
        if msg_type == 3 and len(data) >= 5:
            eid = struct.unpack("I", data[1:5])[0]
            if eid in self.enemies.enemies:
                del self.enemies.enemies[eid]
            return

    # ---------------------------
    # --- Mises à jour ---
    # ---------------------------
    def update_world(self):
        self.enemies.update(self.players.players)
        self.broadcast_state()

    # ---------------------------
    # --- Envoi aux clients ---
    # ---------------------------
    def broadcast_state(self):
        payload = struct.pack("B", len(self.players.players))
        for pid, (x, y, action, flip) in self.players.players.items():
            action_bytes = action.encode('utf-8')[:15]
            action_bytes += b'\x00' * (15 - len(action_bytes))
            flip_byte = b'\x01' if flip else b'\x00'
            payload += struct.pack("Iff", pid, x, y) + action_bytes + flip_byte

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
