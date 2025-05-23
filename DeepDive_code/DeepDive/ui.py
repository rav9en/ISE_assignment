import pygame
import json
import os
from skills import skill_list, get_skill_by_name
from shop import ShopManager
from data import load_user_data, save_user_data

class UIManager:
    def __init__(self, screen_width, screen_height, font_path=None, player_id="player1"):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.Font(font_path, 36) if font_path else pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 26)

        self.icon = self.load_and_scale("assets/ui/icon_coin.png", (40, 40))
        self.coin_font = pygame.font.SysFont(None, 48)
        self.coin_icon_pos = (20, 20) 

        self.treasure_icon_pos = (self.coin_icon_pos[0], self.coin_icon_pos[1] + 48 + 10)
        self.treasure_icon = self.load_and_scale("assets/ui/icon_treasure.png", (40, 40))
        self.treasure_font = pygame.font.SysFont(None, 48)

        self.bar_bg = pygame.transform.scale_by(pygame.image.load("assets/ui/valueBar.png").convert_alpha(), 2)
        self.bar_red = pygame.transform.scale_by(pygame.image.load("assets/ui/valueRed.png").convert_alpha(), 2)
        self.bar_blue = pygame.transform.scale_by(pygame.image.load("assets/ui/valueBlue.png").convert_alpha(), 2)

        self.bg_original = pygame.image.load("assets/backgrounds/background.png").convert()
        self.midground_original = pygame.image.load("assets/backgrounds/midground.png").convert_alpha()
        self.midground_x = 0
        self.midground_width = self.midground_original.get_width()

        self.button_images = {
            "Play": self.load_button("start"),
            "Shop": self.load_button("shop"),
            "Exit": self.load_button("exit"),
        }
        self.buttons = []

        self.show_shop_menu = False
        self.buying_skill = None
        self.confirmation_popup = False

        self.background_image = pygame.transform.scale(self.bg_original, (self.screen_width, self.screen_height))
        self.midground_image = pygame.transform.scale(self.midground_original, (self.screen_width, self.screen_height))

        back_active = pygame.image.load("assets/shop/back_active.png").convert_alpha()
        back_nonactive = pygame.image.load("assets/shop/back_nonactive.png").convert_alpha()

        scale_factor = 0.5
        new_size = (int(back_active.get_width() * scale_factor), int(back_active.get_height() * scale_factor))

        self.back_button_images = {
            "active": pygame.transform.smoothscale(back_active, new_size),
            "nonactive": pygame.transform.smoothscale(back_nonactive, new_size)
        }
        self.back_button_rect = self.back_button_images["nonactive"].get_rect()
        self.back_button_rect.topleft = (30, self.screen_height - self.back_button_images["nonactive"].get_height() - 30)

        self.player_id = player_id
        self.total_coin_count = load_user_data(self.player_id, skill_list)

        self.buy_button_images = {
            "active": pygame.image.load("assets/shop/buy_active.png").convert_alpha(),
            "nonactive": pygame.image.load("assets/shop/buy_nonactive.png").convert_alpha(),
            "sold": pygame.image.load("assets/shop/sold.png").convert_alpha(),
        }

        self.skill_icons = {}
        self.skill_buy_rects = {}
        self.skills = skill_list
        self.skill_key_mapping = {
            skill.name: str(i + 1) for i, skill in enumerate(self.skills)
        }
        self.font_small = pygame.font.SysFont("arial", 18)
        self.font_small_bold = pygame.font.SysFont("arial", 25, bold=True)
        self.skill_bg_box = pygame.image.load("assets/shop/box.png").convert_alpha()
        self.skill_bg_box = pygame.transform.scale(self.skill_bg_box, (34, 34))

        self.last_hud_update_time = 0
        self.cached_skill_hud = pygame.Surface((1, 1), pygame.SRCALPHA)
        for skill_name, icon in self.skill_icons.items():
            self.skill_icons[skill_name] = pygame.transform.smoothscale(icon, (64, 64))

        for skill in skill_list:
            icon_path = f"assets/shop/{skill.name.lower().replace(' ', '_')}.png"
            try:
                icon_img = pygame.image.load(icon_path).convert_alpha()
                self.skill_icons[skill.name] = pygame.transform.scale(icon_img, (64, 64))
                skill.icon_path = icon_path
            except:
                skill.icon_path = None

        self.play_requested = False
        self.exit_requested = False
        self.shop_requested = False

    def load_button(self, name):
        return {
            "active": pygame.image.load(f"assets/main_menu/button/{name}_active.png").convert_alpha(),
            "nonactive": pygame.image.load(f"assets/main_menu/button/{name}_nonactive.png").convert_alpha()
        }

    def load_and_scale(self, path, size):
        return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if not self.show_shop_menu:
                for label, rect in self.buttons:
                    if rect.collidepoint(mouse_pos):
                        if label == "Play":
                            self.play_requested = True
                        elif label == "Exit":
                            self.exit_requested = True
                        elif label == "Shop":
                            self.show_shop_menu = True   # 这里设置了显示商店菜单
            else:
                if self.back_button_rect.collidepoint(mouse_pos):
                    self.show_shop_menu = False

    def draw_skill_hud(self, surface, player):
        current_time = pygame.time.get_ticks()
        if not hasattr(self, "skills") or not self.skills or not player:
            return

        # 每 200ms 更新一次 HUD surface 缓存
        if current_time - getattr(self, "last_hud_update_time", 0) > 200:
            self.cached_skill_hud = self._build_skill_hud(player)
            self.last_hud_update_time = current_time

        screen_width, screen_height = surface.get_size()
        hud_x = 20
        hud_y = screen_height - self.cached_skill_hud.get_height() - 20
        hud_pos = (hud_x, hud_y)
        surface.blit(self.cached_skill_hud, hud_pos)

        # 检查鼠标悬停，显示 tooltip
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for rect, description in self.skill_icon_rects:
            global_rect = rect.move(hud_x, hud_y)  # 修正相对 HUD 的坐标
            if global_rect.collidepoint(mouse_x, mouse_y):
                self._draw_tooltip(surface, description, (mouse_x + 10, mouse_y + 10))
                break

    def _build_skill_hud(self, player):
        icon_size = 40
        box_size = 50
        spacing = 50  # 再次加大技能之间的距离
        hud_width = 340
        skill_number = 1

        # 字体设置
        font_name = self.font_small     # 技能名
        font_cd = self.font_small_bold  # CD时间
        font_index = self.font_small_bold  # 序号

        purchased_skills = [s for s in self.skills if s.purchased]
        hud_height = (box_size + spacing) * len(purchased_skills)
        hud_surface = pygame.Surface((hud_width, hud_height), pygame.SRCALPHA)

        self.skill_icon_rects = []  # 用于悬停检测

        y = 0
        for skill in purchased_skills:
            internal_name = skill.name.lower().replace(" ", "_")
            icon = self.skill_icons.get(skill.name)
            if not icon:
                skill_number += 1
                continue

            # 图标和框缩放
            icon_resized = pygame.transform.scale(icon, (icon_size, icon_size))
            box_x = 30
            box_y = y

            # 绘制背景框
            box_resized = pygame.transform.scale(self.skill_bg_box, (box_size, box_size))
            hud_surface.blit(box_resized, (box_x, box_y))

            # 图标位置（居中在背景框中）
            icon_x = box_x + (box_size - icon_size) // 2
            icon_y = box_y + (box_size - icon_size) // 2

            hud_surface.blit(icon_resized, (icon_x, icon_y))

            # 保存悬停区域
            rect = pygame.Rect(icon_x, icon_y, icon_size, icon_size)
            self.skill_icon_rects.append((rect, skill.description))

            # 技能名（图标下方左对齐）
            name_surface = font_name.render(skill.name, True, (255, 255, 255))
            hud_surface.blit(name_surface, (box_x, box_y + box_size + 6))

            # 序号左上角
            index_surface = font_index.render(str(skill_number), True, (200, 200, 200))
            hud_surface.blit(index_surface, (0, y + 6))

            y += box_size + spacing
            skill_number += 1

        return hud_surface

    def _draw_tooltip(self, surface, text, pos):
        font = self.font_small
        lines = text.split("\n")
        rendered_lines = [font.render(line, True, (255, 255, 255)) for line in lines]
        width = max(line.get_width() for line in rendered_lines) + 12
        height = sum(line.get_height() for line in rendered_lines) + 12

        tooltip_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        tooltip_surface.fill((30, 30, 30, 220))
        pygame.draw.rect(tooltip_surface, (200, 200, 200), tooltip_surface.get_rect(), 1)

        y = 6
        for line in rendered_lines:
            tooltip_surface.blit(line, (6, y))
            y += line.get_height()

        surface.blit(tooltip_surface, pos)

    def draw_hover_tooltip(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        for rect, description in self.skill_icon_rects:
            global_rect = rect.move(self.hud_x, self.hud_y)  # <== 添加全局坐标转换
            if global_rect.collidepoint(mouse_pos):
                self._draw_tooltip(surface, description, (mouse_pos[0] + 10, mouse_pos[1] + 10))
                break

    def draw_status_bar(self, surface, value, color_bar, label, y_offset, text_override=None, is_oxygen=False, is_health=False, player=None):
        # 预计算常用值
        base_x = 20
        bar_w, bar_h = self.bar_bg.get_size()
        color_w, color_h = color_bar.get_size()
        pad_x = 8
        fill_width = min(int((value / 100) * color_w), color_w)  # 确保不超出范围
        
        # 1. 绘制背景条（静态部分）
        surface.blit(self.bar_bg, (base_x, y_offset))
        
        # 2. 绘制动态填充部分
        if fill_width > 0:
            filled = color_bar.subsurface(pygame.Rect(0, 0, fill_width, color_h))
            offset_y = (bar_h - color_h) // 2
            surface.blit(filled, (base_x + pad_x, y_offset + offset_y))
        
        # 3. 特殊标记处理（氧气/生命值）
        if player:
            # 氧气条特殊标记
            if is_oxygen and hasattr(player, 'base_oxygen_max') and player.oxygen_max > player.base_oxygen_max:
                base_max_ratio = player.base_oxygen_max / player.oxygen_max
                mark_pos = base_x + pad_x + int(color_w * base_max_ratio)
                self._draw_mark_line(surface, mark_pos, y_offset, bar_h, (255, 215, 0))  # 黄色标记
            
            # 生命值条特殊标记
            if is_health and hasattr(player, 'base_health_max') and player.health_max > player.base_health_max:
                base_max_ratio = player.base_health_max / player.health_max
                mark_pos = base_x + pad_x + int(color_w * base_max_ratio)
                self._draw_mark_line(surface, mark_pos, y_offset, bar_h, (255, 215, 0)) 
        
        # 4. 文本渲染（使用缓存优化）
        text_str = f"{label}: {text_override if text_override else int(value)}"
        
        # 文本缓存机制
        if not hasattr(self, 'text_cache'):
            self.text_cache = {}
        
        cache_key = (text_str, label)  # 使用组合键避免冲突
        if cache_key not in self.text_cache:
            self.text_cache[cache_key] = self.small_font.render(text_str, True, (255, 255, 255))
        
        text_surface = self.text_cache[cache_key]
        text_y = y_offset + (bar_h - text_surface.get_height()) // 2
        surface.blit(text_surface, (base_x + bar_w + 10, text_y))
        
        return y_offset + bar_h + 10

    def _draw_mark_line(self, surface, x_pos, y_offset, bar_h, color):
        """绘制标记线的辅助方法"""
        if not hasattr(self, 'mark_line_cache'):
            self.mark_line_cache = {}
        
        cache_key = (color, bar_h)
        if cache_key not in self.mark_line_cache:
            line_height = bar_h + 6
            line_surface = pygame.Surface((3, line_height), pygame.SRCALPHA)
            line_surface.fill((*color, 255))  # 使用传入的颜色
            self.mark_line_cache[cache_key] = line_surface
        
        surface.blit(self.mark_line_cache[cache_key], 
                    (x_pos, y_offset - 3))
        
    def draw(self, surface, player, coin_count, treasure_count):
        y = 20

        health_percent = player.health / player.health_max * 100
        text_override = f"{int(health_percent)}%"

        y = self.draw_status_bar(surface, health_percent, self.bar_red, "HP", y, 
                                 text_override=text_override,
                                 is_health=True,
                                 player=player)

        oxygen_percent = player.oxygen / player.oxygen_max * 100
        oxygen_text_override = f"{int(oxygen_percent)}%"  # 显示当前百分比
        y = self.draw_status_bar(surface, oxygen_percent, self.bar_blue, "Oxygen", y, 
                                text_override=oxygen_text_override,
                                is_oxygen=True,
                                player=player)
        
        icon_x = 20
        icon_y = y
        surface.blit(self.icon, (icon_x, icon_y))

        coin_str = str(coin_count)
        coin_text = self.coin_font.render(coin_str, True, (255, 255, 0))
        shadow = self.coin_font.render(coin_str, True, (0, 0, 0))
        outline = self.coin_font.render(coin_str, True, (50, 50, 0))

        text_x = icon_x + self.icon.get_width() + 10
        text_y = y + (self.icon.get_height() - coin_text.get_height()) // 2

        surface.blit(shadow, (text_x + 2, text_y + 2))
        surface.blit(outline, (text_x - 1, text_y - 1))
        surface.blit(coin_text, (text_x, text_y))

        # ---------- Treasure ----------
        treasure_icon_y = icon_y + self.icon.get_height() + 15
        surface.blit(self.treasure_icon, (icon_x, treasure_icon_y))

        treasure_str = f"{treasure_count} / 3"
        treasure_text = self.coin_font.render(treasure_str, True, (255, 255, 0))
        shadow = self.coin_font.render(treasure_str, True, (0, 0, 0))
        outline = self.coin_font.render(treasure_str, True, (50, 50, 0))

        treasure_text_x = text_x
        treasure_text_y = treasure_icon_y + (self.treasure_icon.get_height() - treasure_text.get_height()) // 2

        surface.blit(shadow, (treasure_text_x + 2, treasure_text_y + 2))
        surface.blit(outline, (treasure_text_x - 1, treasure_text_y - 1))
        surface.blit(treasure_text, (treasure_text_x, treasure_text_y))


    def draw_main_menu(self, surface):
        screen_width, screen_height = surface.get_size()
        self.bg = pygame.transform.scale(self.bg_original, (screen_width, screen_height))
        self.midground = pygame.transform.scale(self.midground_original, (screen_width, screen_height))
        self.midground_width = screen_width

        surface.blit(self.bg, (0, 0))
        surface.blit(self.midground, (self.midground_x, 0))
        surface.blit(self.midground, (self.midground_x + screen_width, 0))
        self.midground_x -= 0.1
        if self.midground_x <= -screen_width:
            self.midground_x = 0

        if not self.show_shop_menu:
            self.buttons.clear()
            mouse_pos = pygame.mouse.get_pos()
            labels = ["Play", "Shop", "Exit"]
            total_height = sum(self.button_images[l]["active"].get_height() + 40 for l in labels) - 40
            start_y = (screen_height - total_height) // 2

            for label in labels:
                active_img = self.button_images[label]["active"]
                nonactive_img = self.button_images[label]["nonactive"]
                rect = nonactive_img.get_rect(center=(screen_width // 2, start_y))
                img = active_img if rect.collidepoint(mouse_pos) else nonactive_img
                surface.blit(img, rect.topleft)
                self.buttons.append((label, rect))
                start_y += rect.height + 40
        else:
            self.draw_shop_menu(surface)

        pygame.display.flip()

    def draw_game_over(self, surface, win=False):
        surface.fill((0, 0, 0))
        message = "You Win!" if win else "Game Over"
        msg_render = self.font.render(message, True, (255, 255, 0))
        surface.blit(msg_render, (self.screen_width // 2 - msg_render.get_width() // 2, 200))

        retry_y = self.screen_height // 2
        exit_y = retry_y + 100

        retry_btn = pygame.Rect(self.screen_width // 2 - 100, retry_y, 200, 60)
        exit_btn = pygame.Rect(self.screen_width // 2 - 100, exit_y, 200, 60)

        pygame.draw.rect(surface, (0, 100, 200), retry_btn, border_radius=10)
        pygame.draw.rect(surface, (150, 0, 0), exit_btn, border_radius=10)

        surface.blit(self.font.render("Retry", True, (255, 255, 255)), (retry_btn.x + 60, retry_btn.y + 15))
        surface.blit(self.font.render("Exit", True, (255, 255, 255)), (exit_btn.x + 70, exit_btn.y + 15))

        pygame.display.flip()
        return retry_btn, exit_btn
