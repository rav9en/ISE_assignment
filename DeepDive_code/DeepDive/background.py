# baclkground.py
import pygame
import math

class Background:
    def __init__(self, screen_width, screen_height, world_width, world_height):
        # 加载背景图像
        self.bg_tile = pygame.image.load("assets/backgrounds/background.png").convert()
        self.mid_tile = pygame.image.load("assets/backgrounds/midground.png").convert_alpha()

        # 远景背景固定为屏幕大小（静止）
        self.bg_tile = pygame.transform.scale(self.bg_tile, (screen_width, screen_height))

        # 计算中景背景所需尺寸：视差因子决定所需覆盖范围
        self.parallax_factor = 0.2
        self.float_amplitude = 10
        self.float_speed = 0.005

        # 计算中景背景应该覆盖的最小宽高（视差区域 + 浮动余量）
        mid_width = int(screen_width + (world_width - screen_width) * self.parallax_factor)
        mid_height = int(screen_height + (world_height - screen_height) * self.parallax_factor + self.float_amplitude * 2)

        self.mid_tile = pygame.transform.scale(self.mid_tile, (mid_width, mid_height))
        self.mid_size = pygame.Vector2(mid_width, mid_height)

        # ✅ 用于主菜单滚动
        self.midground_x = 0
        self.midground_width = mid_width
        
    def update(self, player_x, player_y):
        # 此处保留接口以供扩展（如切换背景图层等）
        pass

    def draw(self, screen, camera_offset):
        # 背景浮动偏移
        current_time = pygame.time.get_ticks()
        offset_y = math.sin(current_time * self.float_speed) * self.float_amplitude

        # 远景背景固定在原点
        screen.blit(self.bg_tile, (0, 0))

        # 中景背景：添加视差 + 浮动
        mid_x = -camera_offset.x * self.parallax_factor
        mid_y = -camera_offset.y * self.parallax_factor + offset_y

        screen.blit(self.mid_tile, (mid_x, mid_y))
