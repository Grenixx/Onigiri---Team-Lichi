import pygame
import socket
import struct
import threading
import time
import random

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

x, y = random.randint(100, 700), random.randint(100, 500)
vx, vy = 0, 0
speed = 5
player_id = None
others = {}

# ---- Réception ----
def receiver():
    global player_id, others
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            if len(data) == 4:  # c’est notre ID
                player_id = struct.unpack("I", data)[0]
                print(f"Received player ID: {player_id}")
                continue

            n = struct.unpack_from("B", data, 0)[0]
            offset = 1
            for _ in range(n):
                pid, px, py, pvx, pvy = struct.unpack_from("Iffff", data, offset)
                offset += 20
                if pid == player_id:
                    continue  # 🔥 ignore totalement toi-même
                if pid not in others:
                    others[pid] = {"x": px, "y": py, "target_x": px, "target_y": py, "vx": 0, "vy": 0, "last": time.time()}
                others[pid].update({"target_x": px, "target_y": py, "vx": pvx, "vy": pvy, "last": time.time()})
        except:
            pass

threading.Thread(target=receiver, daemon=True).start()

# ---- Boucle principale ----
running = True
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    vx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed
    vy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed

    # Déplacement instantané et local
    x += vx * dt * 60
    y += vy * dt * 60

    # Envoi au serveur
    sock.sendto(struct.pack("ffff", x, y, vx, vy), (SERVER_IP, SERVER_PORT))

    # Mise à jour des autres joueurs
    now = time.time()
    for pid, d in others.items():
        lag = now - d["last"]
        target_x = d["target_x"] + d["vx"] * lag * 30
        target_y = d["target_y"] + d["vy"] * lag * 30
        d["x"] += (target_x - d["x"]) * 0.15
        d["y"] += (target_y - d["y"]) * 0.15

    # Affichage
    screen.fill((25, 25, 25))
    pygame.draw.rect(screen, (0, 255, 0), (x, y, 40, 40))
    for pid, d in others.items():
        pygame.draw.rect(screen, (255, 0, 0), (d["x"], d["y"], 40, 40))
    pygame.display.flip()
