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