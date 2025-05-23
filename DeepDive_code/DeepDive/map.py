# map.py
import pygame
import csv
import os

class TileMap:
    def __init__(self, csv_path, tileset_path, tile_size):
        self.tile_size = tile_size
        self.tiles = self.load_tiles(tileset_path)
        self.map_data = self.load_csv(csv_path)

        # 创建一个用于碰撞检测的二维矩阵
        self.collidable_tiles = self.create_collidable_tiles()

    def load_tiles(self, path):
        image = pygame.image.load(path).convert_alpha()
        tiles = []
        image_width, image_height = image.get_size()
        for y in range(0, image_height, self.tile_size):
            for x in range(0, image_width, self.tile_size):
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                tile = image.subsurface(rect)
                tiles.append(tile)
        return tiles

    def load_csv(self, path):
        with open(path) as f:
            reader = csv.reader(f)
            return [[int(tile) for tile in row] for row in reader]

    def create_collidable_tiles(self):
        """根据tile的ID创建一个碰撞矩阵。"""
        collidable = []
        for row in self.map_data:
            collidable_row = []
            for tile_id in row:
                # 这里假设tile_id < 0的tile是不能碰撞的
                if tile_id >= 0:
                    collidable_row.append(True)
                else:
                    collidable_row.append(False)
            collidable.append(collidable_row)
        return collidable

    def check_collision(self, rect):
        """检查玩家的矩形是否与任何平台碰撞"""
        # 计算玩家矩形的范围
        left = rect.left // self.tile_size
        right = (rect.right - 1) // self.tile_size
        top = rect.top // self.tile_size
        bottom = (rect.bottom - 1) // self.tile_size

        # 检查玩家的矩形是否与任何collidable的tile重叠
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                if self.collidable_tiles[y][x]:
                    return True  # 如果发生碰撞
        return False

    def draw(self, surface, camera_offset):
        for y, row in enumerate(self.map_data):
            for x, tile_index in enumerate(row):
                if tile_index == -1:
                    continue
                tile_rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                screen_pos = tile_rect.topleft - camera_offset
                surface.blit(self.tiles[tile_index], screen_pos)

