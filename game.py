import pygame

(w,h) = (800, 600)
screen = pygame.display.set_mode((w, h))
pygame.display.flip()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 
