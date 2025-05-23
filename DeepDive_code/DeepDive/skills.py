# skills.py
import json
import os

class Skill:
    def __init__(self, name, description, price, apply_func, is_passive=True, duration=0, cooldown=0):
        self.name = name
        self.description = description
        self.price = price
        self.apply_func = apply_func
        self.purchased = False
        self.is_passive = is_passive  # True = 被动，False = 主动技能
        self.duration = duration      # 持续时间（秒）
        self.cooldown = cooldown      # 冷却时间（秒）
        self.active = False
        self.cooldown_timer = 0

    def apply(self, player):
        self.apply_func(player)
    
    def update(self, dt, player):
        if self.active and self.duration > 0:
            self.duration -= dt
            if self.duration <= 0:
                self.active = False
                self.deactivate(player)

        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0, self.cooldown_timer - dt)
    
    def activate(self, player):
        if self.cooldown_timer == 0:
            self.active = True
            self.duration_timer = self.duration
            self.apply(player)
            self.cooldown_timer = self.cooldown


class ExtraHealthSkill(Skill):
    def __init__(self):
        super().__init__(
            name="Extra Health",
            description="Increase your maximum health by 20% to survive longer.",
            price=30,
            is_passive=True
        )
        self.multiplier = 1.2  # 保持与氧气技能相同的乘数命名

    def apply(self, player):
        print(f"Applying health skill - before: {player.health_max}")  # 调试
        if not hasattr(player, 'base_health_max'):
            player.base_health_max = player.health_max
            print(f"Base health saved: {player.base_health_max}")  # 调试
        
        player.health_max = int(player.base_health_max * self.multiplier)
        print(f"After apply: base={player.base_health_max}, max={player.health_max}")  # 调试
        player.health = min(player.health, player.health_max)
        self.purchased = True

    def deactivate(self, player):
        """与氧气技能完全一致的撤销逻辑"""
        if hasattr(player, 'base_health_max'):
            # 确保先恢复上限再调整当前值
            player.health = min(player.health, player.base_health_max)  # 防止溢出
            player.health_max = player.base_health_max
            del player.base_health_max  # 同样的属性清理方式

class OxygenCapacitySkill(Skill):
    def __init__(self):
        super().__init__(
            name="Larger Oxygen Capacity",
            description="Increase your maximum oxygen by 20% for longer dives.",
            price=30,
            is_passive=True
        )
        self.multiplier = 1.2

    def apply(self, player):
        if not hasattr(player, 'base_oxygen_max'):
            player.base_oxygen_max = player.oxygen_max
        
        player.oxygen_max = int(player.base_oxygen_max * self.multiplier)
        player.oxygen = min(player.oxygen, player.oxygen_max)  # 确保不溢出
        self.purchased = True

    def deactivate(self, player):
        if hasattr(player, 'base_oxygen_max'):
            player.oxygen_max = player.base_oxygen_max
            player.oxygen = min(player.oxygen, player.oxygen_max)

class SwimFasterSkill(Skill):
    def __init__(self):
        super().__init__(
            name="Swim Faster",
            description="Increase your swim speed by 50% to explore more efficiently.",
            price=35,
            is_passive=True
        )
        self.multiplier = 1.5

    def apply(self, player):
        if not hasattr(player, 'base_swim_speed'):
            player.base_swim_speed = player.swim_speed

        player.swim_speed = player.base_swim_speed * self.multiplier
        self.purchased = True

    def deactivate(self, player):
        if hasattr(player, 'base_swim_speed'):
            player.swim_speed = player.base_swim_speed

class OxygenReductionSkill(Skill):
    def __init__(self):
        super().__init__(
            name="Oxygen Reduction",
            description="Reduce oxygen consumption permanently by 50%.",
            price=35,
            is_passive=True  # 改为被动技能
        )
        self.multiplier = 0.5

    def apply(self, player):
        if not hasattr(player, 'base_oxygen_consumption_multiplier'):
            player.base_oxygen_consumption_multiplier = getattr(player, 'oxygen_consumption_multiplier', 1.0)
        
        player.oxygen_consumption_multiplier = player.base_oxygen_consumption_multiplier * self.multiplier
        self.purchased = True
        print("[DEBUG] Oxygen reduction passive applied: multiplier =", player.oxygen_consumption_multiplier)

    def deactivate(self, player):
        # 如果你有重置技能的逻辑（例如重新开始游戏时）
        if hasattr(player, 'base_oxygen_consumption_multiplier'):
            player.oxygen_consumption_multiplier = player.base_oxygen_consumption_multiplier
            del player.base_oxygen_consumption_multiplier

class CoinMagnetSkill(Skill):
    def __init__(self):
        super().__init__(
            name="Coin Magnet",
            description="Attract nearby coins automatically with a passive magnetic field.",
            price=40,
            is_passive=True
        )
        self.range_multiplier = 1.5  # 你可以调整吸引范围的倍率

    def apply(self, player):
        if not hasattr(player, 'base_coin_magnet_radius'):
            player.base_coin_magnet_radius = getattr(player, 'coin_magnet_radius', 100)  # 默认范围100

        player.coin_magnet_radius = player.base_coin_magnet_radius * self.range_multiplier
        self.purchased = True
        print("[DEBUG] Coin Magnet passive applied: radius =", player.coin_magnet_radius)

    def deactivate(self, player):
        if hasattr(player, 'base_coin_magnet_radius'):
            player.coin_magnet_radius = player.base_coin_magnet_radius
            del player.base_coin_magnet_radius

class InvincibilityShieldSkill(Skill):
    def __init__(self):
        super().__init__(
            name="Invincibility Shield",
            description="Grants 3 automatic shields that block damage.",
            price=50,
            is_passive=True 
        )
        self.max_charges = 3

    def apply(self, player):
        # 初始化护盾计数
        player.invincibility_charges = self.max_charges
        player.has_invincibility_shield = True
        self.purchased = True
        print(f"[DEBUG] Invincibility Shield applied: {self.max_charges} charges.")

    def deactivate(self, player):
        player.has_invincibility_shield = False
        if hasattr(player, 'invincibility_charges'):
            del player.invincibility_charges
        print(f"[DEBUG] Invincibility Shield removed.")


# --- Skill Functions ---
def apply_extra_health(player):
    player.health_max = int(player.health_max * 1.2)
    player.health = player.health_max

def apply_extra_oxygen(player):
    player.oxygen_max = int(player.oxygen_max * 1.2)
    player.oxygen = player.oxygen_max

def apply_swim_speed(player):
    player.swim_speed *= 1.25

def apply_coin_magnet(player):
    player.has_coin_magnet = True

def apply_invincibility_shield(player):
    player.is_invincible = True

def apply_oxygen_reduction(player):
    if not hasattr(player, 'base_oxygen_consumption_multiplier'):
        player.base_oxygen_consumption_multiplier = getattr(player, 'oxygen_consumption_multiplier', 1.0)

    player.oxygen_consumption_multiplier = player.base_oxygen_consumption_multiplier * 0.5

def apply_flashlight_boost(player):
    if not hasattr(player, 'base_flashlight_radius'):
        player.base_flashlight_radius = player.flashlight_radius
    player.flashlight_radius = player.base_flashlight_radius * 1.5

# --- Skill Definitions ---
extra_health = Skill(
    name="Extra Health",
    description="Increase your maximum health by 20% to survive longer.",
    price=30,
    apply_func=apply_extra_health
)

extra_oxygen = Skill(
    name="Larger Oxygen Capacity",
    description="Increase your maximum oxygen by 20% for longer dives.",
    price=30,
    apply_func=apply_extra_oxygen
)

swim_speed = Skill(
    name="Swim Faster",
    description="Increase your swim speed by 25% to explore more efficiently.",
    price=35,
    apply_func=apply_swim_speed
)

coin_magnet = Skill(
    name="Coin Magnet",
    description="Temporarily attract coins within a small radius (10 seconds).",
    price=40,
    apply_func=apply_coin_magnet,
    is_passive=False,
    duration=10
)

invincibility_shield = Skill(
    name="Invincibility Shield",
    description="Become immune to damage for 3 times.",
    price=50,
    apply_func=apply_invincibility_shield,
)

oxygen_reduction = Skill(
    name="Oxygen Reduction",
    description="Temporarily reduce oxygen consumption by 50%.",
    price=35,
    apply_func=apply_oxygen_reduction,
)

flashlight_boost = Skill(
    name="Flashlight Boost",
    description="Increase flashlight radius by 50% for better visibility.",
    price=25,
    apply_func=apply_flashlight_boost
)

# --- Skill Registry ---
skill_list = [
    extra_health,
    extra_oxygen,
    swim_speed,
    coin_magnet,
    invincibility_shield,
    oxygen_reduction,
    flashlight_boost
]

# --- Skill Utility ---
def get_skill_by_name(name):
    for skill in skill_list:
        if skill.name == name:
            return skill
    return None
