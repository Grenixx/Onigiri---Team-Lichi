import socket
import struct
import threading
import time

class ClientNetwork:
    def __init__(self, server_ip="127.0.0.1", server_port=5005):
        self.server = (server_ip, server_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.05)
        self.id = None
        self.players = {}
        self.enemies = {}
        self.running = True

        self.remote_players = {}
        self.ping = 0.0  # <--- Nouveau

        # thread de réception
        threading.Thread(target=self.listen, daemon=True).start()

        # thread ping régulier
        threading.Thread(target=self._ping_loop, daemon=True).start()  # <--- Nouveau


    def connect(self):
        print("Connexion au serveur...")
        while self.id is None and self.running:
            try:
                # envoyer le paquet de connexion
                self.sock.sendto(b'\x0A', self.server)
                start_time = time.time()

                while time.time() - start_time < 2:  # attente max 2 secondes
                    try:
                        data, _ = self.sock.recvfrom(4096)
                        if len(data) == 4:
                            self.id = struct.unpack("I", data)[0]
                            print(f"Connected with ID {self.id}")
                            break
                        else:
                            print("Paquet inattendu reçu, en attente du PID...")
                    except socket.timeout:
                        pass

                if self.id is None:
                    print("Timeout, nouvelle tentative de connexion...")
                    time.sleep(0.5)

            except ConnectionResetError:
                print("Serveur injoignable, nouvelle tentative...")
                time.sleep(0.5)

    def listen(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(4096)
                if not data:
                    continue

                # Si le message commence par \x09 → c’est un pong
                if data[0] == 9 and len(data) >= 9:
                    sent_time = struct.unpack("d", data[1:9])[0]
                    self.ping = (time.time() - sent_time) * 1000  # ms
                    continue

                offset = 0
                count = data[offset]
                offset += 1
                new_remote_players = {}

                for _ in range(count):
                    if len(data) >= offset + 28:
                        pid = struct.unpack("I", data[offset:offset+4])[0]
                        x, y = struct.unpack("ff", data[offset+4:offset+12])
                        action = data[offset+12:offset+27].decode('utf-8').rstrip('\x00')
                        flip = data[offset+27] == 1
                        new_remote_players[pid] = (x, y, action, flip)
                        offset += 28
                    else:
                        break
                self.remote_players = new_remote_players

                if len(data) >= offset + 1:
                    enemy_count = data[offset]
                    offset += 1
                    new_enemies = {}
                    for _ in range(enemy_count):
                        if len(data) >= offset + 12:
                            eid, x, y = struct.unpack("Iff", data[offset:offset+12])
                            new_enemies[eid] = (x, y)
                            offset += 12
                    self.enemies = new_enemies

            except socket.timeout:
                pass
            except Exception as e:
                print("Listen error:", e)
                break
            time.sleep(0.01)


    def send_state(self, x, y, action, flip):
        try:
            packet = b'\x00' + struct.pack("ffBB", x, y, action, flip)
            self.sock.sendto(packet, self.server)
        except Exception as e:
            print("Send error:", e)


    def remove_enemy(self, eid):
        try:
            packet = b'\x03' + struct.pack("I", eid)
            self.sock.sendto(packet, self.server)
            print(f"Demande suppression du monstre {eid}")
        except Exception as e:
            print("Remove enemy error:", e)


    def _ping_loop(self):
        """Thread séparé qui envoie périodiquement un ping."""
        while self.running:
            try:
                packet = b'\x09' + struct.pack("d", time.time())
                self.sock.sendto(packet, self.server)
            except Exception:
                pass
            time.sleep(1.0)  # ping toutes les 1 seconde


    def disconnect(self):
        try:
            self.sock.sendto(b'\x01', self.server)
            self.running = False
            self.sock.close()
            print("Disconnected from server.")
        except Exception as e:
            print("Disconnect error:", e)
