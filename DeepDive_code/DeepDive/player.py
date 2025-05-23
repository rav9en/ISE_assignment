# player.py
import pygame
import os
clock = pygame.time.Clock()

class Player(pygame.sprite.Sprite):
    def __init__(self, asset_path, skills):
        super().__init__()

        self.skills = skills or []

        self.active_skills = {}  # {技能名: {remaining, duration, cooldown, on_cooldown}}
        self.cooldowns = {}      # {技能名: cooldown_remaining_time_in_ms}

        for skill in self.skills:
            skill_id = skill.name.lower().replace(" ", "_")
            self.cooldowns[skill_id] = 0
            self.active_skills[skill_id] = {"duration": 0, "remaining": 0}

        self.animations = {
            "idle": self.load_images(os.path.join(asset_path, "idle")),
            "swimming": self.load_images(os.path.join(asset_path, "default_swimming"))
        }

        self.state = "idle"  # Initial state
        self.image_index = 0
        self.image = self.animations[self.state][self.image_index]

        # Player world position (in virtual world space)
        self.world_rect = self.image.get_rect(center=(400, 300))  # Initial position
        self.rect = self.world_rect  # Add rect property for sprite collision

        self.animation_timer = 0
        self.animation_speed = 0.1
        self.velocity = pygame.math.Vector2(0, 0)

        # Skill-related attributes
        self.base_oxygen_max = 100
        self.oxygen_max = self.base_oxygen_max
        self.oxygen = self.oxygen_max
        self.oxygen_consumption_multiplier = 1.0  # 可被技能修改

        self.base_health_max = 100 
        self.health_max = self.base_health_max
        self.health = self.health_max

        self.swim_speed = 4
        self.swim_speed_max = self.swim_speed
        self.swim_speed = self.swim_speed_max

        self.coin_magnet_radius = 180

        self.base_flashlight_radius = 125

        self.invincible_timer = 2.0
        self.damage_cooldown = 0.5
        self.shield_active = False

        self.shield_count = 3 if self.has_skill("invincibility shield") else 0
        self.shield_recharge_time = 10.0  # 10秒充能时间
        self.shield_recharge_timer = 0.0

        # Player stats
        self.invincible = False
        self.magnet_active = False
        self.oxygen_consumption_multiplier = 1.0
        self.flashlight_multiplier = 1.0

        self.apply_skill_effects()

        if self.has_skill("swim speed"):
            self.swim_speed *= 1.25

    def load_images(self, folder):
        """Load images from the specified folder."""
        images = []
        for filename in sorted(os.listdir(folder)):
            if filename.endswith('.png'):
                path = os.path.join(folder, filename)
                images.append(pygame.image.load(path).convert_alpha())
        return images

    def take_damage(self, amount):
        if getattr(self, 'invincible', False):
            return

        if self.has_skill("invincibility shield") and self.shield_count > 0:
            self.shield_count -= 1
            print(f"[DEBUG] Shield blocked damage. Charges remaining: {self.shield_count}")
            self.invincible = True
            self.invincible_timer = 2.0  # Brief invincibility after blocking
            return False

        self.health -= amount
        self.health = max(0, self.health)

        self.invincible = True
        self.invincible_timer = 2.0

        print(f"[DEBUG] Took damage: {amount}, Health now: {self.health}")

        return self.health <= 0

    def set_image_alpha(self, image, alpha):
        img = image.copy()
        img.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        return img

    def has_skill(self, skill_name):
        skill_name = skill_name.lower()
        return any(skill.name.lower() == skill_name and skill.purchased for skill in self.skills)

    def apply_skill_effects(self):
        # Health
        health_percent = self.health / self.health_max if self.health_max > 0 else 1.0
        new_max = int(self.base_health_max * 1.2) if self.has_skill("extra health") else self.base_health_max
        self.health_max = new_max
        self.health = int(self.health_max * health_percent)
        self.health = max(0, self.health)
        print(f"[DEBUG] Health adjusted: {self.health}/{self.health_max} ({health_percent*100:.1f}%)")

        # Oxygen
        oxygen_percent = (self.oxygen / self.oxygen_max) if (hasattr(self, "oxygen") and self.oxygen_max > 0) else 1.0
        self.oxygen_max = int(self.base_oxygen_max * 1.2) if self.has_skill("larger oxygen capacity") else self.base_oxygen_max
        self.oxygen = int(self.oxygen_max * oxygen_percent)
        self.oxygen = max(0, self.oxygen)  # 至少为 0

        print(f"[DEBUG] apply_skill_effects: oxygen={self.oxygen}, max={self.oxygen_max}, percent={oxygen_percent}")
    
        # Swim Speed
        if hasattr(self, "base_swim_speed"):
            self.swim_speed = self.base_swim_speed
        if self.has_skill("swim faster"):
            self.swim_speed *= 1.25

        print(f"[DEBUG] apply_skill_effects: swim_speed={self.swim_speed}/{self.swim_speed_max}")
 
        # Invincibility Shield
        self.has_invincibility_shield = self.has_skill("invincibility shield")

    def update_oxygen(self, decay_amount: float):
        self.oxygen = max(0, self.oxygen - decay_amount * self.oxygen_consumption_multiplier)
        return self.oxygen > 0

    def collect_coin(self, coin):
        self.coin_count += coin.value
        self.total_coins += coin.value
        self.coin_data["total_coins"] = self.total_coins
        self.save_user_progress()
        print(f"[DEBUG] Collected {coin.value} coin(s). Total: {self.total_coins}")

    def update(self, keys_pressed, world_width, world_height, tile_map, dt):
        self.velocity.x = 0
        self.velocity.y = 0

        self.update_skills(dt)

        # Movement input
        speed = self.swim_speed
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.velocity.x = -speed
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.velocity.x = speed
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.velocity.y = -speed
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.velocity.y = speed

        # Apply movement with bounds of the virtual world
        new_x = self.world_rect.x + self.velocity.x
        new_y = self.world_rect.y + self.velocity.y

        # Get the map bounds
        map_width = len(tile_map.map_data[0]) * tile_map.tile_size
        map_height = len(tile_map.map_data) * tile_map.tile_size

        # Calculate new rectangle position
        new_rect = self.world_rect.copy()
        new_rect.x = max(0, min(new_x, map_width - self.world_rect.width))
        new_rect.y = max(0, min(new_y, map_height - self.world_rect.height))

        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
                self.invincible_timer = 0
        
        if (self.has_skill("invincibility shield") 
            and self.shield_count < 3 
            and not self.invincible):
            self.shield_recharge_timer += dt
            if self.shield_recharge_timer >= self.shield_recharge_time:
                self.shield_count += 1
                self.shield_recharge_timer = 0
                print(f"[DEBUG] Shield recharged. Total charges: {self.shield_count}")

        # Check for collisions with the tile map
        if not tile_map.check_collision(new_rect):
            self.world_rect = new_rect  # 没有碰撞，更新玩家位置

        # Sync the rect to the world position
        self.rect = self.world_rect

        # Determine animation state based on movement
        prev_state = self.state
        if self.velocity.length_squared() > 0:
            self.velocity = self.velocity.normalize() * speed
            self.state = "swimming"
        else:
            self.state = "idle"
        if self.state != prev_state:
            self.image_index = 0

        self.animate()
        self.update_active_skill_effects()

    def update_skills(self, dt):
        for skill in self.skills:
            if skill.purchased and not skill.is_passive:
                skill.update(dt, self)

    def update_active_skill_effects(self):
        # Coin Magnet
        self.magnet_active = self.has_skill("coin magnet")
        
        # Oxygen Efficiency
        self.oxygen_consumption_multiplier = 0.5 if self.has_skill("oxygen reduction") else 1.0

        # Flashlight
        self.flashlight_multiplier = 1.5 if self.has_skill("flashlight boost") else 1.0

    def animate(self):
        """Update the player's animation based on state and movement."""
        if self.state not in self.animations or not self.animations[self.state]:
            print(f"[ERROR] No animation frames for state: {self.state}")
            return

        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            self.image_index = (self.image_index + 1) % len(self.animations[self.state])

        # 获取当前帧图像
        new_image = self.animations[self.state][self.image_index]
        if self.velocity.x < 0:
            new_image = pygame.transform.flip(new_image, True, False)

        
        self.image = new_image
