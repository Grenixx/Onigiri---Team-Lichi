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
        self.running = True

        # thread de réception
        threading.Thread(target=self.listen, daemon=True).start()

    def connect(self):
        # on envoie un paquet vide pour que le serveur nous attribue un ID
        self.sock.sendto(b'\x00' * 24, self.server)
        while self.id is None:
            try:
                data, _ = self.sock.recvfrom(4)
                self.id = struct.unpack("I", data)[0]
                print(f"Connected with ID {self.id}")
            except socket.timeout:
                pass  # on attend la réponse

    def listen(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(4096)
                if not data:
                    continue
                count = struct.unpack("B", data[0:1])[0]
                offset = 1
                new_players = {}
                for _ in range(count):
                    pid, x, y, vx, vy = struct.unpack("Iffff", data[offset:offset + 20])
                    new_players[pid] = (x, y, vx, vy)
                    offset += 20
                self.players = new_players
            except socket.timeout:
                pass  # pas de données pour l'instant
            except OSError:
                break  # socket fermé
            except Exception as e:
                print("Listen error:", e)
                break

            time.sleep(0.01)  # évite d’utiliser 100% CPU

    def send_state(self, x, y, vx, vy):
        try:
            packet = b'\x00' + struct.pack("ffff", x, y, vx, vy)
            self.sock.sendto(packet, self.server)
        except Exception as e:
            print("Send error:", e)


    def disconnect(self):
        try:
            self.sock.sendto(b'\x01', self.server)
            self.running = False
            self.sock.close()
            print("Disconnected from server.")
        except Exception as e:
            print("Disconnect error:", e)
