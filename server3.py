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

        # --- Déconnexion ---
        elif msg_type == 1:
            if addr in clients:
                pid = clients[addr]
                print(f"Player {pid} disconnected {addr}")
                del players[pid]
                del clients[addr]
            continue

        # --- Update position ---
        if msg_type == 0 and addr in clients:
            pid = clients[addr]
            # data = [type(1 byte)] + 4 floats (16 bytes)
            if len(data) >= 17:
                x, y, vx, vy = struct.unpack("ffff", data[1:17])
                players[pid] = (x, y, vx, vy)

        # --- Envoi des mises à jour ---
        now = time.time()
        if now - last_update >= UPDATE_RATE:
            last_update = now
            payload = struct.pack("B", len(players))
            for pid, (px, py, pvx, pvy) in players.items():
                payload += struct.pack("Iffff", pid, px, py, pvx, pvy)
            for c in clients:
                sock.sendto(payload, c)

    except Exception as e:
        # print("Error:", e)
        pass
