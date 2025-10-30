import pygame
import socket
import struct
import threading
import time
import random
from collections import deque

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

INTERP_DELAY = 0.1  # 100ms de retard affiché pour interpolation fluide

# ---- Réception ----
def receiver():
    global player_id, others
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            if len(data) == 4:  # notre ID
                player_id = struct.unpack("I", data)[0]
                print(f"Received player ID: {player_id}")
                continue

            n = struct.unpack_from("B", data, 0)[0]
            offset = 1
            now = time.time()
            for _ in range(n):
                pid, px, py, pvx, pvy = struct.unpack_from("Iffff", data, offset)
                offset += 20
                if pid == player_id:
                    continue  # ignore soi-même
                if pid not in others:
                    others[pid] = {"history": deque(maxlen=30)}
                others[pid]["history"].append((now, px, py))
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

    x += vx * dt * 60
    y += vy * dt * 60

    sock.sendto(struct.pack("ffff", x, y, vx, vy), (SERVER_IP, SERVER_PORT))

    # ---- Affichage ----
    screen.fill((25, 25, 25))
    pygame.draw.rect(screen, (0, 255, 0), (x, y, 40, 40))

    render_time = time.time() - INTERP_DELAY
    for pid, d in others.items():
        h = d["history"]
        if len(h) < 2:
            continue

        # Trouve deux positions autour du temps d'affichage (interpolation linéaire)
        for i in range(len(h) - 1):
            t0, x0, y0 = h[i]
            t1, x1, y1 = h[i + 1]
            if t0 <= render_time <= t1:
                factor = (render_time - t0) / (t1 - t0)
                ix = x0 + (x1 - x0) * factor
                iy = y0 + (y1 - y0) * factor
                pygame.draw.rect(screen, (255, 0, 0), (ix, iy, 40, 40))
                break
        else:
            # si on est après la dernière frame connue (léger extrapolation)
            t_last, lx, ly = h[-1]
            pygame.draw.rect(screen, (255, 0, 0), (lx, ly, 40, 40))

    pygame.display.flip()
