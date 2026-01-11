import os
import pygame
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

BASE_IMG_PATH = 'data/images/'

def load_image(path, convert_alpha=False):
    """path doit être relatif à BASE_IMG_PATH"""
    full_path = resource_path(os.path.join(BASE_IMG_PATH, path))
    img = pygame.image.load(full_path)
    if convert_alpha:
        img = img.convert_alpha()
    else:
        img = img.convert()
    img.set_colorkey((0, 0, 0))
    return img


def load_images(path, convert_alpha=False):
    """path doit être relatif à BASE_IMG_PATH"""
    folder_path = resource_path(os.path.join(BASE_IMG_PATH, path))
    images = []
    for img_name in sorted(os.listdir(folder_path)):
        images.append(load_image(os.path.join(path, img_name), convert_alpha=convert_alpha))  # ne pas rajouter BASE_IMG_PATH ici !
    return images


class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    def update(self, dt =1):
        self.img_duration * dt
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        return self.images[int(self.frame / self.img_duration)]
