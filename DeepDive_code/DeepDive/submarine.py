# submarine.py
import pygame

class Submarine(pygame.sprite.Sprite):
    def __init__(self, image_path, map_width, map_height):
        super().__init__()
        # 加载并缩小潜艇图像为原来的一半
        original_image = pygame.image.load(image_path).convert_alpha()
        width, height = original_image.get_size()
        scaled_width, scaled_height = width // 3, height // 3
        self.image = pygame.transform.smoothscale(original_image, (scaled_width, scaled_height))

        # 将潜艇放置在地图右下角
        x = map_width - scaled_width
        y = map_height - scaled_height
        self.rect = self.image.get_rect(topleft=(x, y))
