import socket
import struct
import threading
import time

class ClientNetwork:
    def __init__(self, server_ip="127.0.0.1", server_port=5005):
        self.server = (server_ip, server_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.05)  # 50 ms timeout, évite le blocage complet
        self.id = None
        self.players = {}
        self.enemies = {}  # enemy_id -> (x, y) - positions des ennemis depuis le serveur
        self.running = True


        # thread de réception
        threading.Thread(target=self.listen, daemon=True).start()

    def connect(self):
        # message de type 10 = demande de connexion
        self.sock.sendto(b'\x0A', self.server)  # 0x0A = 10
        while self.id is None:
            try:
                data, _ = self.sock.recvfrom(4)
                if len(data) >= 4:
                    self.id = struct.unpack("I", data)[0]
                    print(f"Connected with ID {self.id}")
            except socket.timeout:
                pass


    def listen(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(4096)
                if not data:
                    continue

                offset = 0

                # nombre de joueurs
                count = data[offset]
                offset += 1
                new_remote_players = {}

                for _ in range(count):
                    # id(4) + x(4) + y(4) + action(15) + flip(1) = 28 bytes
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

                # nombre d'ennemis
                if len(data) >= offset + 1:
                    enemy_count = data[offset]
                    offset += 1
                    new_enemies = {}
                    for _ in range(enemy_count):
                        if len(data) >= offset + 12:  # id(4) + x(4) + y(4)
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
        """
        Envoie la position, l'action et le flip au serveur
        """
        try:
            # action : int (0=idle,1=run,2=jump,etc)
            # flip : 0 ou 1
            packet = b'\x00' + struct.pack("ffBB", x, y, action, flip)
            self.sock.sendto(packet, self.server)
        except Exception as e:
            print("Send error:", e)


    def remove_enemy(self, eid):
        """
        Envoie un message type 3 au serveur pour supprimer un monstre.
        """
        try:
            packet = b'\x03' + struct.pack("I", eid)
            self.sock.sendto(packet, self.server)
            print(f"Demande suppression du monstre {eid}")
        except Exception as e:
            print("Remove enemy error:", e)


    def disconnect(self):
        try:
            self.sock.sendto(b'\x01', self.server)
            self.running = False
            self.sock.close()
            print("Disconnected from server.")
        except Exception as e:
            print("Disconnect error:", e)
