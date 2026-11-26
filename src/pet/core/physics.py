"""
physics.py - 核心动力学与物理模拟系统
包含：
  - DampedHarmonicOscillator: 二阶阻尼弹簧摆动器 (提溜钟摆倾角、狼尾摆动)
  - SquashAndStretch: 保体积弹性形变器 (触地挤压弹性缓冲)
  - GazeTracker: 平滑低通视线跟随
  - FallingPhysics: 自由落体与反弹动力学模拟
"""

import math
from typing import Tuple


class DampedHarmonicOscillator:
    """
    二阶阻尼弹簧质量振荡器。
    用于模拟提溜时受重力与拖拽惯性产生的拟真钟摆摆动、耳朵与狼尾动态惯性。
    """

    def __init__(self, stiffness: float = 0.18, damping: float = 0.82, mass: float = 1.0):
        self.stiffness = stiffness
        self.damping = damping
        self.mass = mass
        self.value: float = 0.0
        self.velocity: float = 0.0
        self.target: float = 0.0

    def set_target(self, target: float):
        self.target = target

    def set_value(self, value: float):
        self.value = value
        self.velocity = 0.0

    def apply_impulse(self, impulse: float):
        self.velocity += impulse / self.mass

    def update(self, dt: float = 1.0) -> float:
        """欧拉半隐式数值积分步进。计算受力与阻尼。"""
        force = -self.stiffness * (self.value - self.target)
        self.velocity = (self.velocity + (force / self.mass) * dt) * self.damping
        self.value += self.velocity * dt
        return self.value


class SquashAndStretch:
    """
    保体积弹性形变模拟器。
    模拟落地瞬间的挤压缓冲（Squash）与站起拉伸（Stretch），保持 Sx * Sy 约等于 1.0。
    """

    def __init__(self, decay: float = 0.85, frequency: float = 14.0):
        self.decay = decay
        self.frequency = frequency
        self.time: float = 0.0
        self.amplitude: float = 0.0
        self.active: bool = False

    def trigger(self, impact_strength: float = 0.16):
        """触发弹性冲击 (例如 -0.16 代表垂直挤压压缩 16%)"""
        self.amplitude = max(-0.35, min(0.35, impact_strength))
        self.time = 0.0
        self.active = True

    def update(self, dt: float = 0.033) -> Tuple[float, float]:
        """返回 (scale_x, scale_y)。静止状态返回 (1.0, 1.0)。"""
        if not self.active:
            return 1.0, 1.0

        self.time += dt
        envelope = self.amplitude * math.exp(-6.0 * self.time)
        oscillation = math.cos(self.frequency * self.time)
        sy_offset = envelope * oscillation

        if abs(envelope) < 0.005:
            self.active = False
            return 1.0, 1.0

        scale_y = max(0.65, min(1.35, 1.0 + sy_offset))
        scale_x = 1.0 / math.sqrt(scale_y)
        return scale_x, scale_y


class GazeTracker:
    """
    平滑低通滤波光标凝视追踪器。
    根据鼠标指针与桌宠中心夹角计算头部与眼睛微妙注视偏移。
    """

    def __init__(self, max_angle_deg: float = 6.0, smooth_factor: float = 0.12):
        self.max_angle = max_angle_deg
        self.smooth_factor = smooth_factor
        self.current_angle: float = 0.0
        self.current_eye_offset: float = 0.0

    def update(self, pet_center_x: float, pet_center_y: float, cursor_x: float, cursor_y: float) -> Tuple[float, float]:
        dx = cursor_x - pet_center_x
        dy = cursor_y - pet_center_y
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            target_angle = 0.0
            target_eye = 0.0
        else:
            angle_rad = math.atan2(dy, dx)
            target_angle = max(-self.max_angle, min(self.max_angle, math.degrees(angle_rad) * 0.15))
            target_eye = max(-3.0, min(3.0, dx / 80.0))

        self.current_angle += (target_angle - self.current_angle) * self.smooth_factor
        self.current_eye_offset += (target_eye - self.current_eye_offset) * self.smooth_factor
        return self.current_angle, self.current_eye_offset


class FallingPhysics:
    """
    自由落体与空气动力学。
    负责桌宠空中脱手下坠加速度、水平空气阻力衰减与屏幕边界微弹。
    """

    def __init__(self, gravity: float = 1.35, terminal_velocity: float = 22.0):
        self.gravity = gravity
        self.terminal_velocity = terminal_velocity
        self.velocity_x: float = 0.0
        self.velocity_y: float = 0.0

    def start_fall(self, release_vx: float, release_vy: float):
        self.velocity_x = max(-8.0, min(8.0, release_vx))
        self.velocity_y = max(-6.0, min(14.0, release_vy))

    def step(self, x: int, y: int, ground_y: int, screen_left: int, screen_right: int, pet_width: int) -> Tuple[int, int, bool, float]:
        """
        步进一帧物理模拟。
        返回: (new_x, new_y, has_landed, impact_strength)
        """
        new_x = x + int(self.velocity_x)
        self.velocity_x *= 0.94  # 空气阻力衰减

        # 屏幕左右碰撞微弹
        if new_x < screen_left:
            new_x = screen_left
            self.velocity_x = -self.velocity_x * 0.4
        elif new_x + pet_width > screen_right:
            new_x = screen_right - pet_width
            self.velocity_x = -self.velocity_x * 0.4

        self.velocity_y = min(self.terminal_velocity, self.velocity_y + self.gravity)
        new_y = y + int(self.velocity_y)

        if new_y >= ground_y:
            new_y = ground_y
            impact = min(0.24, max(0.12, abs(self.velocity_y) / self.terminal_velocity * 0.22))
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            return new_x, new_y, True, impact

        return new_x, new_y, False, 0.0
