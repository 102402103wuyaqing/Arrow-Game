import pygame
import sys
import math
import os
from enum import Enum

# ==================== 配置 ====================
CELL_SIZE = 70
GRID_COLS = 8
GRID_ROWS = 8
HUD_HEIGHT = 100  # 从 90 调整为 100，增加空间
WIDTH = CELL_SIZE * GRID_COLS
HEIGHT = HUD_HEIGHT + CELL_SIZE * GRID_ROWS
FPS = 60

# 颜色配置
BG_COLOR = (28, 30, 42)
HUD_BG_COLOR = (20, 22, 32)
GRID_LINE_COLOR = (55, 60, 80)
ARROW_COLOR = (230, 230, 240)
TEXT_COLOR = (220, 225, 240)
DIM_TEXT_COLOR = (150, 155, 175)
WIN_COLOR = (110, 220, 130)
LOSE_COLOR = (235, 105, 105)
ACCENT_COLOR = (255, 200, 80)
BTN_COLOR = (70, 130, 180)
BTN_HOVER = (100, 160, 210)
BTN_TEXT = (255, 255, 255)
COLLISION_COLOR = (255, 70, 70)


# ==================== 方向与箭头 ====================
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class Arrow:
    def __init__(self, x, y, direction, alive=True):
        self.x = x
        self.y = y
        self.direction = direction
        self.alive = alive

        # --- 抖动 & 闪烁特效 ---
        self.shake_time = 0.0
        self.shake_duration = 0.3
        self.shake_amplitude = 12
        self.flash_time = 0.0
        self.flash_duration = 0.4

        # --- 飞出动画属性 ---
        self.flying = False
        self.fly_speed = 1100.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    def start_shake(self):
        self.shake_time = self.shake_duration
        self.flash_time = self.flash_duration

    def start_fly(self):
        self.flying = True
        self.offset_x = 0.0
        self.offset_y = 0.0


# ==================== 路径检测 ====================
def check_path(arrow, arrow_list, grid_size):
    rows, cols = grid_size
    dx, dy = arrow.direction.value

    nx, ny = arrow.x + dx, arrow.y + dy
    while 0 <= nx < cols and 0 <= ny < rows:
        for other in arrow_list:
            if other is arrow or not other.alive:
                continue
            if other.x == nx and other.y == ny:
                return False
        nx += dx
        ny += dy
    return True


# ==================== 关卡数据 ====================
def make_empty_grid():
    return [[None] * GRID_COLS for _ in range(GRID_ROWS)]


def build_levels():
    levels = []
    # ---- 第 1 关 ----
    g1 = make_empty_grid()
    g1[2][2] = Direction.DOWN
    g1[4][2] = Direction.RIGHT
    levels.append({"name": "第 1 关", "grid": g1, "max_mistakes": 3})

    # ---- 第 2 关 ----
    g2 = make_empty_grid()
    g2[1][1] = Direction.DOWN
    g2[3][2] = Direction.LEFT
    g2[3][5] = Direction.LEFT
    g2[6][7] = Direction.UP
    levels.append({"name": "第 2 关", "grid": g2, "max_mistakes": 3})

    # ---- 第 3 关 ----
    g3 = make_empty_grid()
    g3[0][3] = Direction.DOWN
    g3[3][3] = Direction.RIGHT
    g3[3][6] = Direction.RIGHT
    g3[5][3] = Direction.DOWN
    g3[7][6] = Direction.UP
    levels.append({"name": "第 3 关", "grid": g3, "max_mistakes": 4})

    return levels


# ==================== 箭头形状 ====================
ARROW_SHAPES = {
    Direction.RIGHT: [(1, 0), (-0.62, -0.75), (-0.62, 0.75)],
    Direction.LEFT:  [(-1, 0), (0.62, -0.75), (0.62, 0.75)],
    Direction.UP:    [(0, -1), (-0.75, 0.62), (0.75, 0.62)],
    Direction.DOWN:  [(0, 1), (-0.75, -0.62), (0.75, -0.62)],
}


# ==================== 视觉效果类 ====================
class CollisionEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.max_radius = 50
        self.life = 0.3
        self.max_life = 0.3

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            return False
        self.radius = self.max_radius * (1 - self.life / self.max_life)
        return True

    def draw(self, surface, offset):
        alpha = int(255 * (self.life / self.max_life))
        color = (*COLLISION_COLOR, alpha)
        pygame.draw.circle(surface, color, (int(self.x + offset[0]), int(self.y + offset[1])), int(self.radius), 4)
        if self.radius > 10:
            pygame.draw.circle(surface, color, (int(self.x + offset[0]), int(self.y + offset[1])), int(self.radius * 0.6), 2)


# ==================== UI 按钮类 ====================
class Button:
    def __init__(self, x, y, w, h, text, font, bg_color=BTN_COLOR, hover_color=BTN_HOVER):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        text_surf = self.font.render(self.text, True, BTN_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ==================== 主游戏类 ====================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("一箭又一箭")
        self.clock = pygame.time.Clock()

        # ---------- 字体加载 ----------
        def get_chinese_font(size, bold=False):
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
                "C:/Windows/Fonts/simsun.ttc"
            ]
            for path in font_paths:
                if os.path.exists(path):
                    f = pygame.font.Font(path, size)
                    if bold: f.set_bold(True)
                    return f
            f = pygame.font.Font(None, size)
            if bold: f.set_bold(True)
            return f

        self.font = get_chinese_font(20)
        self.font_mid = get_chinese_font(22, bold=True)
        self.font_big = get_chinese_font(48, bold=True)
        self.font_title = get_chinese_font(64, bold=True)

        # ---------- 初始化按钮 ----------
        # 开始界面按钮
        self.btn_start = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 60, "开始游戏", self.font_mid)

        # HUD 按钮（重新排版：高度 36，间距 10，右侧留白 20）
        # 计算：WIDTH = 560。右侧边距 20。总按钮区域 = 20 + 100 + 10 + 100 + 20 = 250。
        # 起始 X = 560 - 230 = 330
        self.btn_restart_hud = Button(WIDTH - 230, 32, 100, 36, "重开本关", self.font)
        self.btn_back_home = Button(WIDTH - 120, 32, 100, 36, "返回主页", self.font)

        # 结算界面按钮
        self.btn_next = Button(WIDTH // 2 - 90, HEIGHT // 2 + 30, 180, 55, "下一关", self.font_mid)
        self.btn_retry = Button(WIDTH // 2 - 90, HEIGHT // 2 + 30, 180, 55, "重新挑战", self.font_mid)

        self.levels = build_levels()
        self.level_index = 0

        self.game_state = "start"
        self.flying_arrows = []
        self.arrows = []
        self.grid = []
        self.mistakes = 0
        self.max_mistakes = 3
        self.level_name = ""
        self.win_animation_done = False

        # 屏幕震动
        self.screen_shake_time = 0.0
        self.screen_shake_duration = 0.2
        self.collision_effects = []

    # ---------- 关卡管理 ----------
    def load_level(self, index):
        if index >= len(self.levels):
            index = 0
        self.level_index = index
        data = self.levels[index]

        self.level_name = data["name"]
        self.max_mistakes = data["max_mistakes"]
        self.mistakes = 0
        self.game_state = "playing"
        self.win_animation_done = False

        self.grid = make_empty_grid()
        self.arrows = []
        self.flying_arrows = []
        self.collision_effects.clear()

        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                d = data["grid"][y][x]
                if d is not None:
                    a = Arrow(x, y, d)
                    self.grid[y][x] = a
                    self.arrows.append(a)

    def restart_level(self):
        self.load_level(self.level_index)

    def next_level(self):
        self.load_level((self.level_index + 1) % len(self.levels))

    def go_home(self):
        self.game_state = "start"

    # ---------- 坐标转换 ----------
    def screen_to_grid(self, mx, my):
        if my < HUD_HEIGHT:
            return None
        gx = mx // CELL_SIZE
        gy = (my - HUD_HEIGHT) // CELL_SIZE
        if 0 <= gx < GRID_COLS and 0 <= gy < GRID_ROWS:
            return int(gx), int(gy)
        return None

    # ---------- 鼠标点击事件 ----------
    def handle_click(self, mx, my):
        if self.game_state == "start":
            if self.btn_start.is_clicked((mx, my)):
                self.load_level(0)
            return

        if self.game_state == "win" and self.win_animation_done:
            if self.btn_next.is_clicked((mx, my)):
                self.next_level()
            return
        if self.game_state == "lose":
            if self.btn_retry.is_clicked((mx, my)):
                self.restart_level()
            return

        if self.game_state == "playing":
            if self.btn_restart_hud.is_clicked((mx, my)):
                self.restart_level()
                return
            if self.btn_back_home.is_clicked((mx, my)):
                self.go_home()
                return

            cell = self.screen_to_grid(mx, my)
            if cell is None:
                return
            x, y = cell
            arrow = self.grid[y][x]
            if arrow is None or not arrow.alive:
                return

            alive_list = [a for a in self.arrows if a.alive]
            can_fly = check_path(arrow, alive_list, (GRID_ROWS, GRID_COLS))

            if can_fly:
                arrow.start_fly()
                arrow.alive = False
                self.grid[y][x] = None
                self.flying_arrows.append(arrow)

                if not any(a.alive for a in self.arrows):
                    self.game_state = "win"
                    self.win_animation_done = False
            else:
                arrow.start_shake()
                self.mistakes += 1
                self.screen_shake_time = self.screen_shake_duration

                ex = arrow.x * CELL_SIZE + CELL_SIZE / 2
                ey = HUD_HEIGHT + arrow.y * CELL_SIZE + CELL_SIZE / 2
                self.collision_effects.append(CollisionEffect(ex, ey))

                if self.mistakes >= self.max_mistakes:
                    self.game_state = "lose"

    # ---------- 动画状态更新 ----------
    def update(self, dt):
        if self.screen_shake_time > 0:
            self.screen_shake_time = max(0.0, self.screen_shake_time - dt)

        for a in self.arrows:
            if a.shake_time > 0:
                a.shake_time = max(0.0, a.shake_time - dt)
            if a.flash_time > 0:
                a.flash_time = max(0.0, a.flash_time - dt)

        self.collision_effects = [e for e in self.collision_effects if e.update(dt)]

        margin = CELL_SIZE * 2
        still_flying = []
        for a in self.flying_arrows:
            dx, dy = a.direction.value
            a.offset_x += dx * a.fly_speed * dt
            a.offset_y += dy * a.fly_speed * dt

            cx = a.x * CELL_SIZE + CELL_SIZE / 2 + a.offset_x
            cy = HUD_HEIGHT + a.y * CELL_SIZE + CELL_SIZE / 2 + a.offset_y

            if (cx < -margin or cx > WIDTH + margin or
                    cy < -margin or cy > HEIGHT + margin):
                continue
            still_flying.append(a)
        self.flying_arrows = still_flying

        if self.game_state == "win" and len(self.flying_arrows) == 0:
            self.win_animation_done = True

    # ---------- 绘制 ----------
    def draw_arrow_at(self, arrow, offset_x=0.0, offset_y=0.0):
        cx = arrow.x * CELL_SIZE + CELL_SIZE / 2 + offset_x
        cy = HUD_HEIGHT + arrow.y * CELL_SIZE + CELL_SIZE / 2 + offset_y

        if arrow.shake_time > 0:
            t = 1.0 - arrow.shake_time / arrow.shake_duration
            shake = math.sin(t * math.pi * 6) * arrow.shake_amplitude * (1 - t)
            cx += shake

        color = ARROW_COLOR
        if arrow.flash_time > 0:
            if int(arrow.flash_time * 20) % 2 == 0:
                color = COLLISION_COLOR
            else:
                color = (255, 150, 150)

        size = CELL_SIZE * 0.32
        pts = [(cx + px * size, cy + py * size)
               for px, py in ARROW_SHAPES[arrow.direction]]
        pygame.draw.polygon(self.screen, color, pts)

    def draw_board(self, offset):
        pygame.draw.rect(self.screen, BG_COLOR,
                         (0, HUD_HEIGHT, WIDTH, HEIGHT - HUD_HEIGHT))

        for x in range(GRID_COLS + 1):
            px = x * CELL_SIZE + offset[0]
            pygame.draw.line(self.screen, GRID_LINE_COLOR,
                             (px, HUD_HEIGHT + offset[1]), (px, HEIGHT + offset[1]), 1)
        for y in range(GRID_ROWS + 1):
            py = HUD_HEIGHT + y * CELL_SIZE + offset[1]
            pygame.draw.line(self.screen, GRID_LINE_COLOR,
                             (offset[0], py), (WIDTH + offset[0], py), 1)

        for a in self.arrows:
            if a.alive and not a.flying:
                self.draw_arrow_at(a)

        for a in self.flying_arrows:
            self.draw_arrow_at(a, a.offset_x, a.offset_y)

        for e in self.collision_effects:
            e.draw(self.screen, offset)

    def draw_hud(self, offset):
        pygame.draw.rect(self.screen, HUD_BG_COLOR, (0, 0, WIDTH, HUD_HEIGHT))
        pygame.draw.line(self.screen, GRID_LINE_COLOR,
                         (0, HUD_HEIGHT - 1), (WIDTH, HUD_HEIGHT - 1), 2)

        # 左侧第一行：关卡名称
        title = self.font_mid.render(self.level_name, True, ACCENT_COLOR)
        self.screen.blit(title, (24, 20))

        # 左侧第二行：失误次数（格式微调，更紧凑）
        mist_color = LOSE_COLOR if self.mistakes >= self.max_mistakes else TEXT_COLOR
        mt = self.font.render(f"失误：{self.mistakes} / {self.max_mistakes}", True, mist_color)
        self.screen.blit(mt, (24, 56))

        # 中间：剩余箭头（计算一个相对居中的位置，避开左侧文字和右侧按钮）
        remaining = sum(1 for a in self.arrows if a.alive)
        rt = self.font.render(f"剩余箭头：{remaining}", True, TEXT_COLOR)
        # 左侧文字预计占用到 x=160，右侧按钮起始于 x=330
        # 中间区域为 160~330，中心点为 245
        center_x = 245 - rt.get_width() // 2
        self.screen.blit(rt, (center_x, 42))

        # 绘制 HUD 按钮
        self.btn_restart_hud.draw(self.screen)
        self.btn_back_home.draw(self.screen)

    def draw_start_screen(self):
        self.screen.fill(BG_COLOR)

        start_y = 120

        title = self.font_title.render("一箭又一箭", True, ACCENT_COLOR)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, start_y))

        lines = [
            "游戏规则：",
            "1. 点击箭头，它会沿着箭头方向同行/同列飞行。",
            "2. 如果前方没有其他箭头，它会飞出棋盘并消失。",
            "3. 如果前方有箭头阻挡，会发生碰撞，消耗 1 次失误机会。",
            "4. 清空所有箭头即可过关。"
        ]

        line_y = start_y + 120
        for i, line in enumerate(lines):
            color = ACCENT_COLOR if i == 0 else TEXT_COLOR
            surf = self.font.render(line, True, color)
            x = WIDTH // 2 - surf.get_width() // 2
            self.screen.blit(surf, (x, line_y + i * 40))

        self.btn_start.draw(self.screen)

    def draw_overlay(self, offset):
        if self.game_state == "playing":
            return

        if self.game_state == "win" and not self.win_animation_done:
            return

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        if self.game_state == "win":
            text, color = "过关！", WIN_COLOR
            btn = self.btn_next
        else:
            text, color = "失败", LOSE_COLOR
            btn = self.btn_retry

        big = self.font_big.render(text, True, color)
        self.screen.blit(big, (WIDTH // 2 - big.get_width() // 2, HEIGHT // 2 - 100))

        btn.draw(self.screen)

    def draw(self):
        if self.game_state == "start":
            self.draw_start_screen()
        else:
            self.screen.fill(BG_COLOR)

            offset = (0, 0)
            if self.screen_shake_time > 0:
                shake_amp = 8 * (self.screen_shake_time / self.screen_shake_duration)
                offset = (math.sin(pygame.time.get_ticks() * 0.05) * shake_amp,
                          math.cos(pygame.time.get_ticks() * 0.07) * shake_amp)

            self.draw_board(offset)
            self.draw_hud(offset)
            self.draw_overlay(offset)

        pygame.display.flip()

    # ---------- 主循环 ----------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state == "playing":
                            self.go_home()
                        else:
                            pygame.quit()
                            sys.exit()
                    elif event.key == pygame.K_r and self.game_state == "playing":
                        self.restart_level()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(*event.pos)

            self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()
    #最终版本
