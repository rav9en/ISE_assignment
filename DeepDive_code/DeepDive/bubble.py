import pygame
import random
from pygame import gfxdraw  # 更平滑的圆形绘制

class Bubble(pygame.sprite.Sprite):
    # 类变量缓存已生成的泡泡表面
    _size_cache = {}
    
    def __init__(self, x, y):
        super().__init__()
        self.size = random.randint(12, 20)
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = (x, y)
        
        # 使用缓存或创建新表面
        if self.size not in self._size_cache:
            self._create_surface()
            self._size_cache[self.size] = self.image
        else:
            self.image = self._size_cache[self.size].copy()
        
        self.alpha = 180
        self.speed_y = random.uniform(0.4, 0.8)
        self.fade_speed = random.uniform(1.5, 2.5)  # 随机消失速度
        self.float_direction = random.choice([-0.2, 0, 0.2])  # 水平漂移

    def _create_surface(self):
        """创建带透明通道的泡泡表面"""
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        color = (173, 216, 230, 180)  # 固定初始透明度
        pygame.gfxdraw.filled_circle(
            self.image,
            self.size // 2,
            self.size // 2,
            self.size // 2,
            color
        )
        # 添加高光效果
        highlight_pos = (self.size // 3, self.size // 3)
        pygame.gfxdraw.filled_circle(
            self.image,
            *highlight_pos,
            max(2, self.size // 6),
            (255, 255, 255, 100)
        )

    def update(self):
        """优化后的更新逻辑"""
        self.rect.y -= self.speed_y
        self.rect.x += self.float_direction
        self.alpha = max(0, self.alpha - self.fade_speed)
        
        if self.alpha <= 0:
            self.kill()
        else:
            # 仅当需要更新透明度时才重新绘制
            if self.fade_speed > 0:
                self.image.set_alpha(int(self.alpha))

    @classmethod
    def emit_bubble(cls, group, x, y, count=1):
        """批量生成泡泡的优化方法"""
        new_bubbles = [cls(x + random.randint(-10, 10), 
                       y + random.randint(-5, 5)) for _ in range(count)]
        group.add(*new_bubbles)
        
        # 自动清理超过100个泡泡的情况
        if len(group) > 100:
            for bubble in list(group)[:10]:  # 移除最早的10个
                bubble.kill()