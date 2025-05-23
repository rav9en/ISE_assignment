import pygame
import os
import random

ENEMY_COUNT = 6
ENEMY_PATH = "assets/enemies"
SCALE_FACTOR = 2.4

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_id, tile_map):
        super().__init__()
        self.enemy_id = enemy_id
        self.tile_map = tile_map

        self.walk_frames = self.load_frames("walk")
        self.attack_frames = self.load_frames("attack")
        self.current_frames = self.walk_frames
        self.frame_index = 0
        self.animation_speed = 0.1

        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.direction = pygame.Vector2(random.choice([-1, 1]), 0)
        self.speed = 100

        map_width = len(tile_map.map_data[0]) * tile_map.tile_size
        map_height = len(tile_map.map_data) * tile_map.tile_size
        margin = 5 * tile_map.tile_size
        self.world_pos = pygame.Vector2(
            random.randint(margin, map_width - margin),
            random.randint(margin, map_height - margin)
        )

    def load_frames(self, action):
        path = os.path.join(ENEMY_PATH, str(self.enemy_id), action)
        max_frame_count = 10
        frames = []

        for i in range(1, max_frame_count + 1):
            frame_path = os.path.join(path, f"{i}.png")
            try:
                img = pygame.image.load(frame_path).convert_alpha()
                img = pygame.transform.scale_by(img, SCALE_FACTOR)
                frames.append(img)
            except FileNotFoundError:
                continue

        if not frames:
            dummy_surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            frames.append(dummy_surface)

        return frames

    def update(self, dt):
        if hasattr(self, "player"):
            distance = self.world_pos.distance_to(self.player.world_rect.center)
            new_frames = self.attack_frames if distance < 80 else self.walk_frames
            if new_frames != self.current_frames:
                self.current_frames = new_frames
                self.frame_index = 0


        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.current_frames):
            self.frame_index = 0

        raw_image = self.current_frames[int(self.frame_index)]
        if self.direction.x < 0:
            self.image = pygame.transform.flip(raw_image, True, False)
        else:
            self.image = raw_image

        move_vector = self.direction * self.speed * dt
        new_pos = self.world_pos + move_vector
        new_rect = self.image.get_rect(center=new_pos)

        if self.tile_map.check_collision(new_rect):
            self.direction.x *= -1
        else:
            self.world_pos = new_pos

        self.rect = self.image.get_rect(center=self.world_pos)

    def draw(self, surface, camera_offset):
        draw_pos = self.rect.topleft - camera_offset
        surface.blit(self.image, draw_pos)

    def set_player_reference(self, player):
        self.player = player

class EnemyManager:
    def __init__(self, tile_map, player_start_pos, player):
        self.enemies = pygame.sprite.Group()
        self.enemy_list = []
        self.player = player
        self.spawn_all_enemies(tile_map, player_start_pos)

    def spawn_all_enemies(self, tile_map, player_start_pos):
        used_y_positions = set()
        max_tries = 50
        y_distance_threshold = 80
        min_distance_to_player = 150

        for enemy_id in range(1, ENEMY_COUNT + 1):
            success = False
            for _ in range(max_tries):
                new_enemy = Enemy(enemy_id, tile_map)
                y = int(new_enemy.world_pos.y)
                dist_to_player = new_enemy.world_pos.distance_to(player_start_pos)

                test_rect = new_enemy.image.get_rect(center=new_enemy.world_pos)
                if (all(abs(y - oy) > y_distance_threshold for oy in used_y_positions)
                    and dist_to_player > min_distance_to_player
                    and not tile_map.check_collision(test_rect)):  # ✅ 检查是否碰撞
                    new_enemy.set_player_reference(self.player)
                    used_y_positions.add(y)
                    self.enemy_list.append(new_enemy)
                    self.enemies.add(new_enemy)
                    success = True
                    break

            if not success:
                print(f"[⚠️] Enemy {enemy_id} failed to spawn after {max_tries} tries.")

    def update_all(self, dt):
        for enemy in self.enemies:
            enemy.update(dt)

    def draw_all(self, surface, camera_offset):
        for enemy in self.enemies:
            enemy.draw(surface, camera_offset)
