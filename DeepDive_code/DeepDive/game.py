import pygame
import os
import random
import math
import json

from config import FPS
from player import Player
from background import Background
from coin import Coin
from ui import UIManager
from map import TileMap
from bubble import Bubble
from level import Level
from shop import ShopManager
from data import load_user_data, save_user_data
from skills import skill_list
from enemy import EnemyManager

class Game:
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.screen_width, self.screen_height = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Deep Dive Dash")

        self.camera_offset = pygame.Vector2(0, 0)
        self.clock = pygame.time.Clock()

        self.tile_map = TileMap("assets/tiles/map.csv", "assets/tiles/tileset.png", 64)
        map_width = len(self.tile_map.map_data[0]) * self.tile_map.tile_size
        map_height = len(self.tile_map.map_data) * self.tile_map.tile_size
        self.background = Background(self.screen_width, self.screen_height, map_width, map_height)
        
        self.player_id = "default_player"
        self.skills = skill_list

        total_coins = load_user_data(self.player_id, self.skills)
        self.coin_data = {"total_coins": total_coins}
    
        self.player = Player("assets/characters", self.skills)
        self.all_sprites = pygame.sprite.Group(self.player)

        player_start_pos = pygame.Vector2(self.player.world_rect.center)
        self.enemy_manager = EnemyManager(self.tile_map, player_start_pos, self.player)

        self.bubbles = pygame.sprite.Group()
        self.bubble_timer = 0
        self.bubble_spawn_interval = 150

        self.level = Level("assets/coins", self.tile_map, self.screen_width, self.screen_height)
        self.coins = self.level.coins
        self.treasures = self.level.treasures
        self.submarine = self.level.submarine

        self.coin_count = 0
        self.collected_treasures = 0

        self.total_coins = self.coin_data["total_coins"]

        self.state = 'menu'
        self.game_result = False

        self.ui_manager = UIManager(self.screen_width, self.screen_height, player_id=self.player_id)
        self.shop_manager = ShopManager(
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            ui_manager=self.ui_manager,
            player_id="default_player",  # 或你的实际玩家ID
            coin_data=self.coin_data,
            skill_list=self.skills,
            player=self.player,
        )
        self.skills = self.shop_manager.skills

    def save_user_progress(self):
        save_user_data(self.player_id, self.coin_data["total_coins"], self.shop_manager.skills)

    def get_skill(self, name):
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    def update_game_logic(self):
        dt = self.clock.get_time() / 1000.0

        current_time = pygame.time.get_ticks()

        keys = pygame.key.get_pressed()
        self.player.update(keys, self.screen_width, self.screen_height, self.tile_map, dt)

        self.player.update_skills(dt)

        for enemy in self.enemy_manager.enemy_list:
            if self.player.rect.colliderect(enemy.rect) and not self.player.invincible:
                player_died = self.player.take_damage(20)
                if player_died:
                    self.state = 'gameover'
                    self.game_result = False
                    print("[DEBUG] Player died from enemy collision.")
                    return

        map_width = len(self.tile_map.map_data[0]) * self.tile_map.tile_size
        map_height = len(self.tile_map.map_data) * self.tile_map.tile_size
        half_w, half_h = self.screen_width // 2, self.screen_height // 2
        player_center = self.player.world_rect.center
        offset_x = max(0, min(player_center[0] - half_w, map_width - self.screen_width))
        offset_y = max(0, min(player_center[1] - half_h, map_height - self.screen_height))
        self.camera_offset.update(offset_x, offset_y)

        self.enemy_manager.update_all(dt)

        if current_time - self.bubble_timer > self.bubble_spawn_interval:
            Bubble.emit_bubble(
                self.bubbles,
                x=self.player.rect.centerx,
                y=self.player.rect.top,
                count=random.randint(1, 2) 
            )
            self.bubble_timer = current_time
        
        for bubble in self.bubbles.sprites():
            bubble.update()

        self.coins.update()
        self.treasures.update()

        if self.player.has_skill("coin magnet"):
            for coin in self.coins:
                coin.activate_magnet(self.player)

        for coin in pygame.sprite.spritecollide(self.player, self.coins, dokill=True):
            self.coin_count += coin.value
            self.total_coins += coin.value
            self.coin_data["total_coins"] = self.total_coins
            self.save_user_progress()

        if self.state == 'running':
            base_decay = 5 * dt
            self.player.update_oxygen(base_decay)
        
            if self.player.oxygen <= 0:
                self.state = 'gameover'
                self.game_result = False
                return

        for treasure in self.treasures:
            if self.player.rect.colliderect(treasure.rect) and not treasure.collected:
                treasure.trigger_animation()

        self.collected_treasures = sum(1 for t in self.treasures if t.collected)

        if self.collected_treasures >= 3 and self.player.rect.colliderect(self.submarine.rect):
            self.state = 'gameover'
            self.game_result = True

        self.background.update(self.player.rect.centerx, self.player.rect.centery)

    def run(self):
        running = True  
        while running:
            self.clock.tick(FPS)

            if self.state == 'menu':
                self.ui_manager.midground_x -= 1
                if self.ui_manager.midground_x <= -self.ui_manager.midground_width:
                    self.ui_manager.midground_x = 0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.ui_manager.handle_event(event)
                        if self.ui_manager.show_shop_menu:
                            self.shop_manager.handle_shop_click(event.pos)
                        if self.ui_manager.play_requested:
                            self.state = 'running'
                            self.ui_manager.play_requested = False
                            self.player.oxygen = self.player.oxygen_max
                            self.coin_count = 0
                            self.collected_treasures = 0
                        elif self.ui_manager.exit_requested:
                            running = False
                            self.ui_manager.exit_requested = False
                    elif event.type == pygame.USEREVENT + 1:
                        self.shop_manager.not_enough_coins_popup = False
                    
                # 绘制界面
                if self.ui_manager.show_shop_menu:
                    self.shop_manager.draw_shop_menu(self.screen)
                else:
                    self.ui_manager.draw_main_menu(self.screen)

                pygame.display.flip() 

            elif self.state == 'running':
                keys = pygame.key.get_pressed()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        running = False

                self.update_game_logic()
                self.draw()

            elif self.state == 'gameover':
                retry_btn, exit_btn = self.ui_manager.draw_game_over(self.screen, win=self.game_result)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if retry_btn.collidepoint(event.pos):
                            self.__init__()
                        elif exit_btn.collidepoint(event.pos):
                            running = False

        self.save_user_progress()
        pygame.quit()

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.background.draw(self.screen, self.camera_offset)
        self.tile_map.draw(self.screen, self.camera_offset)

        # 绘制硬币
        for coin in self.coins:
            screen_pos = coin.rect.topleft - self.camera_offset
            self.screen.blit(coin.image, screen_pos)

        # 绘制宝藏
        for treasure in self.treasures:
            screen_pos = treasure.rect.topleft - self.camera_offset
            self.screen.blit(treasure.image, screen_pos)

        # 绘制潜水艇
        submarine_pos = self.submarine.rect.topleft - self.camera_offset
        self.screen.blit(self.submarine.image, submarine_pos)

        # ===== 修改的玩家渲染部分 =====
        player_screen_pos = self.player.world_rect.topleft - self.camera_offset
        self.screen.blit(self.player.image, player_screen_pos)

        # 绘制敌人
        self.enemy_manager.draw_all(self.screen, self.camera_offset)

        # 绘制气泡
        for bubble in self.bubbles:
            screen_pos = bubble.rect.topleft - self.camera_offset
            self.screen.blit(bubble.image, screen_pos)

        self.draw_darkness_overlay()

        # 绘制UI
        self.ui_manager.draw(
            self.screen,
            self.player,
            coin_count=self.coin_count,
            treasure_count=self.collected_treasures,
        )

        self.ui_manager.draw_skill_hud(self.screen, self.player)

        pygame.display.flip()

    def get_flashlight_surface(self):
        radius = int(self.player.base_flashlight_radius * self.player.flashlight_multiplier)
        return self.create_flashlight_gradient(radius)

    def create_flashlight_gradient(self, radius):
        surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)

        for i in range(radius, 0, -1):
            alpha = int(255 * (i / radius) ** 2.5)  # 中心亮，边缘弱
            color = (0, 0, 0, 255 - alpha)  # 越靠近中心透明度越高
            pygame.draw.circle(surface, color, (radius, radius), i)

        return surface
    
    def draw_darkness_overlay(self):
        player_y = self.player.world_rect.centery
        map_height = len(self.tile_map.map_data) * self.tile_map.tile_size

        # 深度决定黑暗程度
        depth_ratio = min(1, max(0, player_y / map_height))
        max_darkness = 255  # 最深暗度
        alpha = int(depth_ratio * max_darkness)

        # 整体黑暗遮罩
        darkness_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        darkness_overlay.fill((0, 0, 0, alpha))

        # 生成/更新光圈渐变（当技能改变时重新生成）
        current_radius = int(self.player.base_flashlight_radius * self.player.flashlight_multiplier)
        if not hasattr(self, "flashlight_gradient") or \
        self.flashlight_gradient.get_size()[0] != current_radius * 2:
            self.flashlight_gradient = self.create_flashlight_gradient(current_radius)
            
        # 玩家在屏幕的中心位置
        player_screen_x = self.player.world_rect.centerx - self.camera_offset.x
        player_screen_y = self.player.world_rect.centery - self.camera_offset.y

        # 在 darkness_overlay 上减去光圈亮度区域
        darkness_overlay.blit(
            self.flashlight_gradient,
            (player_screen_x - current_radius, player_screen_y - current_radius),
            special_flags=pygame.BLEND_RGBA_SUB
        )

        # 绘制最终黑暗遮罩
        self.screen.blit(darkness_overlay, (0, 0))

if __name__ == "__main__":
    game = Game()
    game.run()