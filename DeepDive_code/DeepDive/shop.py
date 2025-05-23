# shop.py
import pygame
import os
import json
import copy
from skills import skill_list
from data import load_user_data, save_user_data

def load_player_coins_and_skills(player_id, skills):
    return load_user_data(player_id, skills)

def save_player_coins_and_skills(player_id, total_coin_count, skills):
    save_user_data(player_id, total_coin_count, skills)

class ShopManager:
    def __init__(self, screen_width, screen_height, ui_manager, player_id, coin_data, skill_list, player, font_path=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ui_manager = ui_manager

        self.player_id = player_id
        self.player = player
        self.coin_data = coin_data
        self.skills = skill_list
        
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 26)
        self.coin_font = pygame.font.SysFont(None, 48)

        self.icon = self.load_and_scale("assets/ui/icon_coin.png", (40, 40))

        self.coin_data = coin_data
        self.total_coin_count = coin_data["total_coins"]  # Initialize total coin count

        self.bg_original = pygame.image.load("assets/backgrounds/background.png").convert()
        self.midground_original = pygame.image.load("assets/backgrounds/midground.png").convert_alpha()
        self.midground_x = 0
        self.midground_width = self.midground_original.get_width()

        self.show_shop_menu = False
        self.buying_skill = None
        self.confirmation_popup = False
        self.shop_menu_rect = pygame.Rect(0, 0, 0, 0)
        self.bold_small_font = pygame.font.SysFont(None, 26, bold=True)

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

        self.buy_button_images = {
            "active": pygame.image.load("assets/shop/buy_active.png").convert_alpha(),
            "nonactive": pygame.image.load("assets/shop/buy_nonactive.png").convert_alpha(),
            "sold": pygame.image.load("assets/shop/sold.png").convert_alpha(),
        }

        self.skill_icons = {}
        self.skill_buy_rects = {}
        
        load_player_coins_and_skills(self.player_id, self.skills) 

        for skill in skill_list:
            icon_path = f"assets/shop/{skill.name.lower().replace(' ', '_')}.png"
            try:
                icon_img = pygame.image.load(icon_path).convert_alpha()
                self.skill_icons[skill.name] = pygame.transform.scale(icon_img, (64, 64))
                skill.icon_path = icon_path
            except:
                skill.icon_path = None 
        
        self.confirmation_popup = False
        self.popup_ready = False
        self.popup_alpha = 0
        self.popup_surface = pygame.Surface((400, 200), pygame.SRCALPHA)

        self.not_enough_coins_popup = False
        self.ne_popup_alpha = 0
        self.ne_popup_surface = pygame.Surface((400, 160), pygame.SRCALPHA)

    def load_and_scale(self, path, size):
        return pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), size)

    def handle_shop_click(self, pos):
        if self.confirmation_popup and self.popup_ready:
            if self.yes_rect.collidepoint(pos):
                self._process_purchase_confirmation()
            elif self.no_rect.collidepoint(pos):
                self._cancel_purchase()
        elif not self.confirmation_popup:
            self._handle_skill_selection(pos)

    def _process_purchase_confirmation(self):
        if not self.buying_skill:
            return
        
        try:
            # 确保self.player是玩家对象
            if self.player:
                for skill in self.player.skills:
                    if skill.name.lower() == self.buying_skill.name.lower():
                        skill.purchased = True
                        print(f"Skill {skill.name} marked as purchased.")
                        break
                else:
                    # 如果玩家还没有这个技能对象，就添加进去
                    self.player.skills.append(self.buying_skill)
                    self.buying_skill.purchased = True
                    print(f"Skill {self.buying_skill.name} added and marked as purchased.")
                
            if self.coin_data["total_coins"] >= self.buying_skill.price > 0:
                self.buying_skill.apply(self.player)
                
                self.coin_data["total_coins"] -= self.buying_skill.price
                self.total_coin_count = self.coin_data["total_coins"]
                self.buying_skill.purchased = True
                save_player_coins_and_skills(
                    self.player_id, 
                    self.total_coin_count, 
                    self.skills
                )
            else:
                self._show_not_enough_coins()
                
        except Exception as e:
            print(f"Error: {e}")
            self._show_purchase_error()
        finally:
            self._reset_purchase_state()

    def _show_purchase_error(self):
        self.not_enough_coins_popup = True
        self.ne_popup_alpha = 0
        pygame.time.set_timer(pygame.USEREVENT + 1, 2000)  # 显示 2 秒
        print("Fail to purchase skill.")

    def _handle_skill_selection(self, pos):
        """处理技能选择逻辑"""
        for skill in self.skills:
            rect = self.skill_buy_rects.get(skill.name)
            if rect and rect.collidepoint(pos) and not skill.purchased:
                self.buying_skill = skill
                self.confirmation_popup = True
                self.popup_ready = False
                self.popup_alpha = 0
                break

    def _show_not_enough_coins(self):
        self.not_enough_coins_popup = True
        self.ne_popup_alpha = 0
        pygame.time.set_timer(pygame.USEREVENT + 1, 2000)  # 2秒后自动关闭

    def _cancel_purchase(self):
        self._reset_purchase_state()

    def _reset_purchase_state(self):
        self.confirmation_popup = False
        self.popup_ready = False
        self.buying_skill = None

    def purchase_skill(self, skill_name):
        skill = next((s for s in self.skills if s.name == skill_name), None)
        if skill and not skill.purchased and self.coin_data["total_coins"] >= skill.price:
            success = skill.apply(self.player)
            if success:
                self.coin_data["total_coins"] -= skill.price
                self.total_coin_count = self.coin_data["total_coins"]
                skill.purchased = True
                return True
        return False

    def draw_confirmation_popup(self, surface):
        width, height = 400, 200
        popup_x = (self.screen_width - width) // 2
        popup_y = (self.screen_height - height) // 2

        # 动画效果：淡入
        if self.popup_alpha < 255:
            self.popup_alpha += 10  # 每帧增加透明度，控制动画速度
        self.popup_surface.set_alpha(self.popup_alpha)

        # 清空并画弹窗背景（半透明黑 + 圆角）
        self.popup_surface.fill((0, 0, 0, 0))  # 先清空
        pygame.draw.rect(self.popup_surface, (30, 30, 30, 220), (0, 0, width, height), border_radius=12)
        pygame.draw.rect(self.popup_surface, (255, 255, 255), (0, 0, width, height), 2, border_radius=12)

        # 问题文字
        question = f"Buy {self.buying_skill.name}?"
        text = self.font.render(question, True, (255, 255, 255))
        self.popup_surface.blit(text, ((width - text.get_width()) // 2, 30))

        # YES / NO 按钮
        self.yes_rect = pygame.Rect(popup_x + 60, popup_y + 120, 100, 40)
        self.no_rect = pygame.Rect(popup_x + 240, popup_y + 120, 100, 40)

        # YES：黄绿色 + 加粗
        pygame.draw.rect(surface, (0, 0, 0, 0), self.yes_rect)  # 确保背景透明
        pygame.draw.rect(self.popup_surface, (181, 230, 29), (60, 120, 100, 40), border_radius=8)
        bold_yes = self.bold_small_font.render("YES", True, (0, 50, 0))
        self.popup_surface.blit(bold_yes, (60 + 30, 120 + 8))

        # NO：莫兰迪红色 + 加粗
        pygame.draw.rect(self.popup_surface, (169, 116, 116), (240, 120, 100, 40), border_radius=8)
        bold_no =  self.bold_small_font.render("NO", True, (50, 0, 0))
        self.popup_surface.blit(bold_no, (240 + 30, 120 + 8))

        # 将整张 popup_surface 贴到 screen 上
        surface.blit(self.popup_surface, (popup_x, popup_y))

        # 设置为可点击状态
        self.popup_ready = True

    def draw_not_enough_coins_popup(self, surface):
        width, height = 400, 160
        popup_x = (self.screen_width - width) // 2
        popup_y = (self.screen_height - height) // 2

        if self.ne_popup_alpha < 255:
            self.ne_popup_alpha += 10
        self.ne_popup_surface.set_alpha(self.ne_popup_alpha)

        self.ne_popup_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.ne_popup_surface, (40, 0, 0, 220), (0, 0, width, height), border_radius=12)
        pygame.draw.rect(self.ne_popup_surface, (255, 100, 100), (0, 0, width, height), 2, border_radius=12)

        warning_text = self.font.render("Not enough coins!", True, (255, 255, 255))
        self.ne_popup_surface.blit(warning_text, ((width - warning_text.get_width()) // 2, 50))

        surface.blit(self.ne_popup_surface, (popup_x, popup_y))

        if self.ne_popup_alpha >= 255:
            # 自动在显示 1.2 秒后关闭
            pygame.time.set_timer(pygame.USEREVENT + 1, 1200, loops=1)

    def draw_shop_menu(self, surface):
        # --- 滚动背景 ---
        self.ui_manager.midground_x -= 1
        if self.ui_manager.midground_x <= -self.ui_manager.midground_width:
            self.ui_manager.midground_x = 0

        surface.blit(self.ui_manager.background_image, (0, 0))
        surface.blit(self.ui_manager.midground_image, (self.ui_manager.midground_x, 0))
        surface.blit(self.ui_manager.midground_image, (self.ui_manager.midground_x + self.screen_width, 0))
        
        menu_width = int(self.screen_width * 0.9)
        menu_height = int(self.screen_height * 0.9)
        x = (self.screen_width - menu_width) // 2
        y = (self.screen_height - menu_height) // 2

        transparent_bg = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        transparent_bg.fill((0, 0, 0, 51))
        surface.blit(transparent_bg, (x, y))

        self.shop_menu_rect = pygame.Rect(x, y, menu_width, menu_height)

        top_padding = 60
        bottom_padding = 60
        available_height = menu_height - top_padding - bottom_padding
        skill_count = len(skill_list)
        spacing = available_height // skill_count
        icon_x = x + 40
        text_x = x + 120

        mouse_pos = pygame.mouse.get_pos()
        self.skill_buy_rects.clear()

        for i, skill in enumerate(self.skills):
            icon = self.skill_icons.get(skill.name)
            skill_y = y + top_padding + i * spacing

            if icon:
                surface.blit(icon, (icon_x, skill_y))

            name_font = pygame.font.SysFont(None, 40, bold=True)
            name_text = name_font.render(skill.name, True, (255, 255, 255))
            outline = name_font.render(skill.name, True, (0, 0, 0))
            surface.blit(outline, (text_x + 2, skill_y + 4))
            surface.blit(name_text, (text_x, skill_y + 2))

            desc_font = pygame.font.SysFont(None, 26)
            desc_text = desc_font.render(skill.description, True, (255, 255, 255))
            surface.blit(desc_text, (text_x, skill_y + 40))

            btn_x = x + menu_width - 180
            btn_y = skill_y
            default_rect = self.buy_button_images["nonactive"].get_rect(topleft=(btn_x, btn_y))
            self.skill_buy_rects[skill.name] = default_rect

            if skill.purchased:
                btn_img = self.buy_button_images["sold"]
            else:
                btn_img = self.buy_button_images["active"] if default_rect.collidepoint(mouse_pos) else self.buy_button_images["nonactive"]

            surface.blit(btn_img, default_rect.topleft)

        is_hover = self.back_button_rect.collidepoint(mouse_pos)
        back_img = self.back_button_images["active"] if is_hover else self.back_button_images["nonactive"]
        surface.blit(back_img, self.back_button_rect.topleft)

        icon_x = self.screen_width - 62
        icon_y = 30
        surface.blit(self.icon, (icon_x, icon_y))
        coin_str = str(self.coin_data["total_coins"])

        coin_color = (180, 255, 100)
        shadow_color = (0, 0, 0)
        outline_color = (80, 150, 50)

        coin_text = self.coin_font.render(coin_str, True, coin_color)
        shadow = self.coin_font.render(coin_str, True, shadow_color)
        outline = self.coin_font.render(coin_str, True, outline_color)

        text_x = icon_x - coin_text.get_width() - 10
        text_y = icon_y + (self.icon.get_height() - coin_text.get_height()) // 2

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            surface.blit(outline, (text_x + dx, text_y + dy))

        surface.blit(shadow, (text_x + 2, text_y + 2))
        surface.blit(coin_text, (text_x, text_y))

        if self.confirmation_popup:
            self.draw_confirmation_popup(surface)

        if self.not_enough_coins_popup:
            self.draw_not_enough_coins_popup(surface)

    def reset(self):
        self.selected_skill = None
        self.not_enough_coins_popup = False
        for skill in self.skills:
            skill.purchased = False
            skill.level = 1

    def get_back_button_rect(self):
        return self.back_button_rect