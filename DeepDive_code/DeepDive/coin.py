# coin.py
import pygame
import os

class Coin(pygame.sprite.Sprite):
    def __init__(self, folder_path, coin_type, x, y):
        super().__init__()
        self.coin_type = coin_type
        self.images = self.load_images(os.path.join(folder_path, coin_type))
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))

        self.animation_timer = 0
        self.animation_speed = 0.15
        self.value = 5 if coin_type == "gold" else 1

        self.magnet_active = False
        self.magnet_target = None
        self.magnet_speed = 8  # 每帧吸附速度


    def load_images(self, path):
        return [
            pygame.image.load(os.path.join(path, img)).convert_alpha()
            for img in sorted(os.listdir(path)) if img.endswith(".png")
        ]

    def update(self):
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.frame_index = (self.frame_index + 1) % len(self.images)
            self.image = self.images[self.frame_index]
            self.animation_timer = 0

        # 吸附逻辑
        if self.magnet_active and self.magnet_target:
            dx = self.magnet_target.rect.centerx - self.rect.centerx
            dy = self.magnet_target.rect.centery - self.rect.centery
            distance = (dx**2 + dy**2) ** 0.5

            # 只有在玩家靠近范围内才吸附
            if distance <= self.magnet_target.coin_magnet_radius:
                if distance < 5:  # 非常接近玩家时，金币被收集
                    self.kill()  # 移除金币精灵
                    self.magnet_target.collect_coin(self)
                else:
                    move_x = self.magnet_speed * dx / distance
                    move_y = self.magnet_speed * dy / distance
                    self.rect.x += int(move_x)
                    self.rect.y += int(move_y)

    def activate_magnet(self, player):
        self.magnet_active = True
        self.magnet_target = player