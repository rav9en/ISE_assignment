# treasure.py
import pygame
import os

class Treasure(pygame.sprite.Sprite):
    def __init__(self, treasure_type, base_path, pos):
        super().__init__()
        self.images = []
        self.load_images(base_path, treasure_type)
        self.index = 0
        self.image = self.images[0]
        self.rect = self.image.get_rect(topleft=pos)
        self.animation_speed = 0.1

        self.collected = False
        self.animating = False

    def load_images(self, base_path, treasure_type):
        folder_path = os.path.join(base_path, treasure_type)
        for i in range(10):
            img_path = os.path.join(folder_path, f"{i}.png")
            image = pygame.image.load(img_path).convert_alpha()
            # 缩放为 48x32
            image = pygame.transform.scale(image, (96,64))
            self.images.append(image)

    def trigger_animation(self):
        if not self.collected and not self.animating:
            self.animating = True
            self.index = 0  # 每次播放从头开始

    def update(self):
        if self.animating:
            self.index += self.animation_speed
            if self.index >= len(self.images):
                self.index = len(self.images) - 1
                self.animating = False
                self.collected = True
            self.image = self.images[int(self.index)]
        elif self.collected:
            # 保持最后一帧
            self.image = self.images[-1]
