import socket
import struct
import time

SERVER_IP = "0.0.0.0"
SERVER_PORT = 5005
UPDATE_RATE = 1 / 30

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))
print(f"Server running on {SERVER_IP}:{SERVER_PORT}")

clients = {}   # addr -> id
players = {}   # id -> (x, y, vx, vy)
next_id = 1
last_update = time.time()

while True:
    try:
        data, addr = sock.recvfrom(24)
        if addr not in clients:
            clients[addr] = next_id
            players[next_id] = (0, 0, 0, 0)
            print(f"New player {next_id} connected {addr}")
            # on renvoie immédiatement l’ID attribué
            sock.sendto(struct.pack("I", next_id), addr)
            next_id += 1

        pid = clients[addr]
        x, y, vx, vy = struct.unpack("ffff", data)
        players[pid] = (x, y, vx, vy)

        now = time.time()
        if now - last_update >= UPDATE_RATE:
            last_update = now
            payload = struct.pack("B", len(players))
            for pid, (px, py, pvx, pvy) in players.items():
                payload += struct.pack("Iffff", pid, px, py, pvx, pvy)
            for c in clients:
                sock.sendto(payload, c)

    except Exception:
        pass
