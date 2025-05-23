import pygame
import random
import os
from coin import Coin
from treasure import Treasure
from submarine import Submarine

class Level:
    def __init__(self, folder_path, tile_map, screen_width, screen_height, num_coins=70, padding=64):
        self.tile_map = tile_map
        
        map_width = len(self.tile_map.map_data[0]) * self.tile_map.tile_size
        map_height = len(self.tile_map.map_data) * self.tile_map.tile_size
        
        self.coins = pygame.sprite.Group()
        self.treasures = pygame.sprite.Group()
        self.submarine = Submarine("assets/submarine.png", map_width, map_height)

        self.folder_path = folder_path
        self.tile_map = tile_map
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.num_coins = num_coins
        self.padding = padding

        self.generate_coins()
        self.generate_treasures()

    def generate_coins(self):
        tile_size = self.tile_map.tile_size
        map_width = len(self.tile_map.map_data[0]) * tile_size
        map_height = len(self.tile_map.map_data) * tile_size

        attempts = 0
        max_attempts = self.num_coins * 10

        while len(self.coins) < self.num_coins and attempts < max_attempts:
            attempts += 1
            x = random.randint(self.padding, map_width - self.padding)
            y = random.randint(self.padding, map_height - self.padding)
            rect = pygame.Rect(x, y, 32, 32)

            if not self.tile_map.check_collision(rect):
                coin_type = random.choice(["gold", "silver"])
                coin = Coin(self.folder_path, coin_type, x, y)
                self.coins.add(coin)

    def generate_treasures(self):
        treasure_types = ["treasure1", "treasure2", "treasure3"]
        tile_size = self.tile_map.tile_size
        map_width = len(self.tile_map.map_data[0]) * tile_size
        map_height = len(self.tile_map.map_data) * tile_size

        for treasure_type in treasure_types:
            while True:
                x = random.randint(64, map_width - 64 - 48)  # 保证右侧不越界
                y = random.randint(64, map_height - 64 - 32)  # 保证底部不越界
                rect = pygame.Rect(x, y, 48, 32)  # 使用实际宝藏大小
                if not self.tile_map.check_collision(rect):
                    treasure = Treasure(treasure_type, "assets/treasure", (x, y))
                    self.treasures.add(treasure)
                    break

    def update(self):
        self.coins.update()
        self.treasures.update()

    def draw(self, surface, camera_offset):
        for coin in self.coins:
            surface.blit(coin.image, coin.rect.topleft - camera_offset)
        for treasure in self.treasures:
            surface.blit(treasure.image, treasure.rect.topleft - camera_offset)
        surface.blit(self.submarine.image, self.submarine.rect.topleft - camera_offset)
