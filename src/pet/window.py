"""
window.py - 明日方舟红 4.0 纯净主悬浮窗
轻量化容器：装配核心渲染器、状态机、物理引擎、皮肤管理器、对话管理器与右键菜单。
"""

import time
import math
import random
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPoint, QPointF, Signal
from PySide6.QtGui import QPainter, QCursor, QGuiApplication, QScreen
from PySide6.QtWidgets import QWidget, QApplication

from pet.skin import SkinManager, PetSkin, SkinAction
from pet.core import (
    ZeroAllocRenderer,
    SquashAndStretch,
    DampedHarmonicOscillator,
    GazeTracker,
    FallingPhysics,
    TransitionScheduler,
)
from pet.dialogue import SpeechBubble, DialogueManager
from pet.ui import build_pet_context_menu, PetTrayManager


class PetWindow(QWidget):
    skin_changed = Signal(str)
    scale_changed = Signal(float)
    activity_level_changed = Signal(str)

    def __init__(
        self,
        skin_manager: SkinManager,
        initial_skin_id: str = "spine_red",
        initial_scale: float = 1.0,
        initial_activity_level: str = "quiet",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.skin_manager = skin_manager
        self.current_skin: Optional[PetSkin] = None
        self.current_action: Optional[SkinAction] = None
        self.current_frame_idx: int = 0
        self.scale_factor: float = initial_scale
        self.facing_left: bool = False  # 原始 Spine 切片原生朝右！False=朝右，True=朝左
        self.click_through: bool = False
        self.activity_level: str = initial_activity_level  # "quiet", "gentle", "active"
        self.last_interaction_time: float = time.time()
        self.locked_action: Optional[str] = None  # 用户手动点播保持标记

        # 状态机
        self.state: str = "idle"

        # 2 秒内连续点击计时器（触发狂戳晕眩彩蛋）
        self._recent_click_times: list[float] = []

        # 运行时跨动作 120ms 帧间柔化混合（Crossfade）
        self._prev_pixmap = None
        self._prev_facing_left: bool = False
        self._crossfade_step: int = 0
        self._crossfade_total: int = 4

        # 运动学参数 (绝对对齐：facing_left=False => 向右位移; facing_left=True => 向左位移)
        self.walk_speed: int = 3
        self.walk_direction: int = 1  # 1 = 向右, -1 = 向左
        self.walk_steps_remaining: int = 0

        # 核心动力学系统
        self.falling_physics = FallingPhysics(gravity=1.35, terminal_velocity=22.0)
        self.squash_stretch = SquashAndStretch(decay=0.85, frequency=14.0)
        self.transition_scheduler = TransitionScheduler()
        self.drag_pendulum = DampedHarmonicOscillator(stiffness=0.18, damping=0.82)
        self.gaze_tracker = GazeTracker()

        # 鼠标拖拽状态
        self.is_dragging: bool = False
        self.has_dragged: bool = False
        self.drag_start_pos: QPoint = QPoint()
        self.window_start_pos: QPoint = QPoint()
        self.last_mouse_pos: QPoint = QPoint()
        self.last_mouse_time: float = 0.0
        self.release_velocity: QPointF = QPointF(0.0, 0.0)
        self.current_tilt_deg: float = 0.0

        # 对话与气泡系统
        self.dialogue_manager = DialogueManager()
        self.bubble = SpeechBubble(self)

        # 定时器
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._next_frame)

        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self._physics_step)

        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self._decide_behavior)

        self.elastic_timer = QTimer(self)
        self.elastic_timer.timeout.connect(self._elastic_step)

        # 加载初始皮肤与缩放
        self.set_skin(initial_skin_id)
        self.set_scale(initial_scale)

        # 托盘管理器 (统一由 app.py 单例管理，严禁在此重复实例化导致双托盘图标)
        self.tray_manager = None

        # 初始化地平线吸附定位
        self._init_position()

        # 启动自主行为循环
        self._schedule_next_behavior()

    # ---------------- 窗口基础与定位 (多显示器自适应) ----------------

    def get_current_screen(self) -> QScreen:
        """
        动态自适应获取桌宠当前所处的多显示器屏幕对象 (支持任意副屏与虚拟桌面跨屏)。
        """
        center = self.geometry().center()
        screen = QGuiApplication.screenAt(center)
        if screen is not None:
            return screen
        screen = self.screen()
        if screen is not None:
            return screen
        return QApplication.primaryScreen()

    def get_ground_y(self, target_screen: Optional[QScreen] = None) -> int:
        screen = target_screen or self.get_current_screen()
        geom = screen.availableGeometry() if screen else QApplication.primaryScreen().availableGeometry()
        if self.current_skin:
            anchor_y = getattr(self.current_skin, "anchor_y", None)
            if anchor_y is None:
                anchor_y = self.current_skin.base_size[1]
            ground_offset = int(anchor_y * self.scale_factor)
        else:
            ground_offset = self.height()
        return geom.bottom() - ground_offset

    def _init_position(self, target_screen: Optional[QScreen] = None):
        screen = target_screen or QApplication.primaryScreen()
        geom = screen.availableGeometry()
        x = geom.right() - self.width() - 80
        y = self.get_ground_y(screen)
        self.move(x, y)

    def reset_position(self, target_screen: Optional[QScreen] = None):
        # 默认重置到当前桌宠所在的屏幕底部，保证副屏重置不乱飞
        scr = target_screen or self.get_current_screen()
        self._init_position(scr)

    def move_to_screen(self, target_screen: QScreen):
        """一键平稳传送至指定显示器右下角或底部"""
        self._init_position(target_screen)
        self.facing_left = True
        self.play_action("idle")

    @property
    def velocity_x(self) -> float:
        return self.falling_physics.velocity_x

    @velocity_x.setter
    def velocity_x(self, val: float):
        self.falling_physics.velocity_x = val

    @property
    def velocity_y(self) -> float:
        return self.falling_physics.velocity_y

    @velocity_y.setter
    def velocity_y(self, val: float):
        self.falling_physics.velocity_y = val

    @property
    def gravity(self) -> float:
        return self.falling_physics.gravity

    @property
    def terminal_velocity(self) -> float:
        return self.falling_physics.terminal_velocity

    def set_skin(self, skin_id: str):
        skin = self.skin_manager.get_skin(skin_id)
        if not skin:
            avail = self.skin_manager.get_available_skins()
            if avail:
                skin = avail[0]
            else:
                return
        self.current_skin = skin
        if getattr(skin, "transitions", None):
            self.transition_scheduler = TransitionScheduler(skin.transitions)
        else:
            self.transition_scheduler = TransitionScheduler()

        if getattr(skin, "dialogues", None):
            self.dialogue_manager.set_skin_dialogues(skin.dialogues)

        w, h = skin.base_size
        self.resize(int(w * self.scale_factor), int(h * self.scale_factor))
        self.move(self.x(), self.get_ground_y())
        self.play_action("idle", force=True, use_transition=False)
        self.skin_changed.emit(skin.skin_id)

    def set_scale(self, scale: float):
        self.scale_factor = max(0.20, min(3.0, scale))
        if self.current_skin:
            w, h = self.current_skin.base_size
            self.resize(int(w * self.scale_factor), int(h * self.scale_factor))
            self.move(self.x(), self.get_ground_y())
            self.update()
        self.scale_changed.emit(self.scale_factor)

    # ---------------- 动作点播与锁定 ----------------

    def select_action(self, action_name: str, lock: bool = True):
        """用户通过菜单显式点播动作：平滑过渡、姿态保持与气泡提示"""
        self.last_interaction_time = time.time()
        self.play_action(action_name, force=True, use_transition=True)

        act_obj = self.current_skin.get_action(action_name) if self.current_skin else None
        is_loop = (act_obj and act_obj.loop) or (action_name in ("idle", "sit", "sleep", "walk", "drag", "cuddle_tail", "sharpen_knife"))
        if (is_loop and lock) or action_name.startswith("trans_"):
            target_state = "sit" if action_name == "trans_sit" else ("sleep" if action_name == "trans_sleep" else action_name)
            self.locked_action = target_state
            self.behavior_timer.stop()
            self.behavior_timer.start(300000)  # 5分钟防打扰

            # 漫步方向智能设定：朝向当前屏幕中心走
            if action_name == "walk":
                screen = self.get_current_screen()
                geom = screen.availableGeometry() if screen else QApplication.primaryScreen().availableGeometry()
                if self.x() > geom.center().x():
                    self.facing_left = True
                    self.walk_direction = -1
                else:
                    self.facing_left = False
                    self.walk_direction = 1
                self.walk_steps_remaining = 999999
        else:
            self.locked_action = None
            self._schedule_next_behavior()

        if self.dialogues_enabled:
            name_cn = {
                "idle": "待机长呼吸", "sit": "抱尾乖坐", "sleep": "蜷缩熟睡",
                "walk": "欢快漫步", "headpat": "开心摸头", "drag": "提溜扑腾",
                "trans_sit": "站姿转坐", "trans_sleep": "坐姿转睡", "fall": "半空飘落", "land": "落地缓冲",
                "cuddle_tail": "抱尾蹭脸", "sharpen_knife": "磨刀拭刃", "alert_scout": "警惕耸耳", "yawn_stretch": "舒展哈欠",
                "edge_peek": "边缘探头", "doze_off": "深夜瞌睡", "dizzy": "戳晕防备"
            }.get(action_name, action_name)
            head_pos = self.mapToGlobal(QPoint(self.width() // 2, 0))
            self.bubble.show_text(f"已固定姿态：{name_cn}", head_pos, duration_ms=2500)

    def unlock_action(self):
        """解除用户姿态锁定，恢复自由自主陪伴"""
        self.locked_action = None
        self.play_action("idle", force=True, use_transition=False)
        self._schedule_next_behavior()
        if self.dialogues_enabled:
            head_pos = self.mapToGlobal(QPoint(self.width() // 2, 0))
            self.bubble.show_text("已恢复自由陪伴状态~", head_pos, duration_ms=2000)

    # ---------------- 动作播放与帧步进 ----------------

    def play_action(self, action_name: str, force: bool = False, use_transition: bool = True):
        if not self.current_skin:
            return

        mapped_name = action_name
        if mapped_name == "click" and not self.current_skin.has_action("click") and self.current_skin.has_action("headpat"):
            mapped_name = "headpat"
        elif mapped_name == "headpat" and not self.current_skin.has_action("headpat") and self.current_skin.has_action("click"):
            mapped_name = "click"

        if self.state == mapped_name and not force:
            return

        # 已经骨骼级 0px 精准对接的过渡链无需做 Crossfade 叠影，避免重影
        seamless_pairs = {
            ("fall", "land"),
            ("idle", "trans_sit"),
            ("trans_sit", "sit"),
            ("sit", "trans_sleep"),
            ("trans_sleep", "sleep"),
        }

        def _capture_crossfade(target_state: str):
            if (
                self.current_action
                and 0 <= self.current_frame_idx < self.current_action.frame_count
                and self.state != target_state
                and (self.state, target_state) not in seamless_pairs
            ):
                self._prev_pixmap = self.current_action.frames[self.current_frame_idx]
                self._prev_facing_left = self.facing_left
                self._crossfade_step = self._crossfade_total
            else:
                self._prev_pixmap = None
                self._crossfade_step = 0

        # 检查跨姿态平滑过渡切片
        if use_transition and not force and self.current_action:
            if getattr(self.current_action, "action_type", "") == "transition":
                return

            planned_act, next_act = self.transition_scheduler.plan_transition(
                self.state, mapped_name, self.current_skin.actions
            )
            if planned_act != mapped_name:
                trans_action = self.current_skin.get_action(planned_act)
                if trans_action and trans_action.frame_count > 0:
                    _capture_crossfade(planned_act)
                    trans_action.next_action = next_act or mapped_name
                    self.state = planned_act
                    self.current_action = trans_action
                    self.current_frame_idx = 0
                    self.anim_timer.stop()
                    self.anim_timer.start(trans_action.frame_delay_ms)
                    self.update()
                    return

        action = self.current_skin.get_action(mapped_name)
        if not action or action.frame_count == 0:
            action = self.current_skin.get_action("idle")
            if not action or action.frame_count == 0:
                return
            mapped_name = "idle"

        _capture_crossfade(mapped_name)
        self.state = mapped_name
        self.current_action = action
        self.current_frame_idx = 0

        # 非漫步动作默认保持正面展示 (edge_peek 保留碰撞边缘定向朝向)
        if mapped_name in ("idle", "greet", "land", "sit", "sleep", "click", "headpat", "dizzy", "trans_sit", "trans_sleep", "cuddle_tail", "sharpen_knife", "alert_scout", "yawn_stretch", "doze_off"):
            self.facing_left = False

        if mapped_name == "walk":
            self.walk_speed = getattr(action, "speed", 3)
            if self.walk_steps_remaining <= 0:
                self.walk_steps_remaining = random.randint(45, 80)

        frame_delay = action.frame_delay_ms
        self.anim_timer.stop()
        self.anim_timer.start(frame_delay)
        self.update()

    def _next_frame(self):
        if not self.current_action:
            return

        if self._crossfade_step > 0:
            self._crossfade_step -= 1
            if self._crossfade_step == 0:
                self._prev_pixmap = None

        self.current_frame_idx += 1
        if self.current_frame_idx >= self.current_action.frame_count:
            if self.current_action.loop:
                self.current_frame_idx = 0
            else:
                if self.state in ("doze_off", "cuddle_tail"):
                    next_act = "sit"
                else:
                    next_act = self.current_action.next_action or "idle"
                self.play_action(next_act, force=True, use_transition=False)
                return

        # 漫步状态驱动位移
        if self.state == "walk":
            self._walk_step()

        self.update()

    # ---------------- 漫步动力学 (彻底消灭太空步) ----------------

    def _walk_step(self):
        # 物理唯一公理：facing_left 为 True 必向左走 (-dx)，为 False 必向右走 (+dx)
        dx = -self.walk_speed if self.facing_left else self.walk_speed
        screen = self.get_current_screen()
        geom = screen.availableGeometry() if screen else QApplication.primaryScreen().availableGeometry()
        new_x = self.x() + dx

        # 当前屏幕边缘碰撞平滑反弹转向 (完美支持副屏独立巡逻)
        hit_left = (new_x < geom.left())
        hit_right = (new_x + self.width() > geom.right())

        if hit_left:
            new_x = geom.left()
            self.facing_left = False  # 转向朝右前进
            self.walk_direction = 1
        elif hit_right:
            new_x = geom.right() - self.width()
            self.facing_left = True   # 转向朝左前进
            self.walk_direction = -1

        self.move(new_x, self.get_ground_y(screen))
        self.walk_steps_remaining -= 1

        # 步数走完且脚步稳稳踏地时回归待机或触发边缘探头
        is_stride_grounded = (
            self.current_frame_idx % 28 == 0 or
            self.current_frame_idx >= self.current_action.frame_count - 1 or
            self.walk_steps_remaining < -15
        )
        if self.locked_action != "walk" and self.walk_steps_remaining <= 0 and is_stride_grounded:
            at_edge = (abs(self.x() - geom.left()) < 15 or abs(self.x() + self.width() - geom.right()) < 15)
            if at_edge and self.current_skin and self.current_skin.has_action("edge_peek") and random.random() < 0.50:
                self.play_action("edge_peek")
            else:
                self.play_action("idle")
            self._schedule_next_behavior()

    # ---------------- 自主静谧行为循环 ----------------

    def set_activity_level(self, level: str):
        if level in ("quiet", "gentle", "active"):
            self.activity_level = level
            self._schedule_next_behavior()
            self.activity_level_changed.emit(level)

    def _schedule_next_behavior(self):
        if self.activity_level == "quiet":
            delay = random.randint(9000, 18000)
        elif self.activity_level == "gentle":
            delay = random.randint(6000, 11000)
        else:
            delay = random.randint(3000, 6000)
        self.behavior_timer.start(delay)

    def _decide_behavior(self):
        if self.is_dragging or self.locked_action is not None:
            self.behavior_timer.start(120000)
            return

        inactive_sec = time.time() - self.last_interaction_time

        import datetime
        cur_hour = datetime.datetime.now().hour
        is_late_night = (cur_hour >= 23 or cur_hour < 6)

        if self.state == "sleep":
            r = random.random()
            wake_prob = 0.05 if is_late_night else 0.10
            if r < wake_prob:
                self.play_action("idle")
            self._schedule_next_behavior()
            return

        if self.state == "sit":
            r = random.random()
            if is_late_night:
                if r < 0.35:
                    self.play_action("doze_off")
                    if self.dialogues_enabled and random.random() < 0.50:
                        self.say_random_dialogue()
                elif r < 0.65:
                    self.play_action("sleep")
                elif r < 0.85:
                    self.play_action("cuddle_tail")
                else:
                    self.play_action("idle")
            elif inactive_sec > 150:
                if r < 0.25:
                    self.play_action("sleep")
                elif r < 0.45:
                    self.play_action("idle")
            else:
                if r < 0.20:
                    self.play_action("cuddle_tail")
                elif r < 0.45:
                    self.play_action("idle")
            self._schedule_next_behavior()
            return

        # 待机状态下的自主动作决策 (生物钟感知)
        walk_prob = 0.04 if is_late_night else (0.10 if self.activity_level == "quiet" else (0.20 if self.activity_level == "gentle" else 0.35))
        r = random.random()
        if r < walk_prob:
            # 随机朝向并迈出同向步伐
            self.facing_left = (random.random() < 0.5)
            self.walk_direction = -1 if self.facing_left else 1
            self.walk_steps_remaining = random.randint(45, 80)
            self.play_action("walk")
        elif is_late_night and r < 0.60:
            if r < 0.30:
                self.play_action("doze_off")
                if self.dialogues_enabled:
                    self.say_random_dialogue()
            else:
                self.play_action("sit")
        elif inactive_sec > 100 and r < walk_prob + 0.30:
            self.play_action("sit")
        elif r < walk_prob + 0.18:
            # 偶发招牌特质动作 (磨刀、警惕耸耳、打哈欠伸懒腰、抱尾)
            flavor_act = random.choice(["sharpen_knife", "alert_scout", "yawn_stretch", "cuddle_tail"])
            self.play_action(flavor_act)
        else:
            self.play_action("idle")
            if self.dialogues_enabled and random.random() < 0.25:
                self.say_random_dialogue()
            self._schedule_next_behavior()

    # ---------------- 鼠标交互与提溜悬空 ----------------

    def mousePressEvent(self, event):
        self.last_interaction_time = time.time()
        if event.button() == Qt.LeftButton:
            self.locked_action = None
            self.is_dragging = True
            self.has_dragged = False
            self.drag_start_pos = event.globalPosition().toPoint()
            self.window_start_pos = self.pos()
            self.last_mouse_pos = self.drag_start_pos
            self.last_mouse_time = time.time()
            self.release_velocity = QPointF(0.0, 0.0)
            self.physics_timer.stop()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.last_interaction_time = time.time()
            curr_pos = event.globalPosition().toPoint()
            delta = curr_pos - self.drag_start_pos
            now = time.time()
            dt = max(0.001, min(0.1, now - self.last_mouse_time))

            inst_vx = (curr_pos.x() - self.last_mouse_pos.x()) / dt
            inst_vy = (curr_pos.y() - self.last_mouse_pos.y()) / dt
            self.release_velocity = QPointF(
                self.release_velocity.x() * 0.60 + inst_vx * 0.012 * 0.40,
                self.release_velocity.y() * 0.60 + inst_vy * 0.012 * 0.40
            )

            # 提溜钟摆摆动物理倾角
            tilt_target = max(-14.0, min(14.0, inst_vx * 0.018))
            self.drag_pendulum.set_target(tilt_target)

            self.last_mouse_pos = curr_pos
            self.last_mouse_time = now

            if not self.has_dragged and delta.manhattanLength() > 5:
                self.has_dragged = True
                self.play_action("drag")
                if self.dialogues_enabled:
                    self.say_context_dialogue("drag")

            self.move(self.window_start_pos + delta)
            self._start_elastic_animation()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.last_interaction_time = time.time()
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.drag_pendulum.set_target(0.0)
            ground_y = self.get_ground_y()

            if not self.has_dragged:
                # 统计 2.0 秒内的连击频率：常规点击摸头笑脸，连续狂戳 >= 5 次触发傲娇晕眩彩蛋
                now = time.time()
                self._recent_click_times = [ts for ts in self._recent_click_times if now - ts <= 2.0]
                self._recent_click_times.append(now)

                self.squash_stretch.trigger(-0.12)
                self._start_elastic_animation()

                if (
                    len(self._recent_click_times) >= 5
                    and self.current_skin
                    and self.current_skin.has_action("dizzy")
                ):
                    self._recent_click_times.clear()
                    self.play_action("dizzy", force=True)
                    if self.dialogues_enabled:
                        head_pos = self.mapToGlobal(QPoint(self.width() // 2, 0))
                        self.bubble.show_text("博士……别一直戳红的脑袋，会晕的……", head_pos, duration_ms=2600)
                else:
                    act = "headpat" if self.current_skin and self.current_skin.has_action("headpat") else "idle"
                    self.play_action(act)
                    if self.dialogues_enabled:
                        self.say_context_dialogue("headpat")
            else:
                if self.y() < ground_y:
                    # 空中脱手 -> 继承横向与纵向释放惯性，进入自由落体
                    self.falling_physics.start_fall(
                        self.release_velocity.x(),
                        self.release_velocity.y()
                    )
                    self.play_action("fall")
                    self.physics_timer.start(33)  # 30 FPS 物理下落模拟
                else:
                    self.move(self.x(), ground_y)
                    self.squash_stretch.trigger(-0.04)
                    self._start_elastic_animation()
                    if self.current_skin and self.current_skin.has_action("land"):
                        self.play_action("land")
                    else:
                        self.play_action("idle")
            event.accept()

    # ---------------- 物理与下落模拟 ----------------

    def _start_elastic_animation(self):
        if not self.elastic_timer.isActive():
            self.elastic_timer.start(25)

    def _elastic_step(self):
        self.current_tilt_deg = self.drag_pendulum.update(0.8)
        if not self.is_dragging:
            self.drag_pendulum.set_target(0.0)

        is_oscillating = abs(self.current_tilt_deg) > 0.1 or abs(self.drag_pendulum.velocity) > 0.05
        if self.squash_stretch.active or is_oscillating:
            self.update()
        else:
            self.current_tilt_deg = 0.0
            self.elastic_timer.stop()
            self.update()

    def _physics_step(self):
        """自由落体下坠动力学：每步同步推进动画，绝不在空中停滞 (支持任意屏幕边界)"""
        screen = self.get_current_screen()
        geom = screen.availableGeometry() if screen else QApplication.primaryScreen().availableGeometry()
        ground_y = self.get_ground_y(screen)

        new_x, new_y, has_landed, impact = self.falling_physics.step(
            self.x(), self.y(), ground_y,
            geom.left(), geom.right(), self.width()
        )

        if has_landed:
            self.move(new_x, new_y)
            self.physics_timer.stop()

            # 落地触地受力轻微弹性辅助震动 (主要屈膝缓冲由 land 骨骼动画承担)
            self.squash_stretch.trigger(-min(0.05, max(0.02, impact * 0.25)))
            self._start_elastic_animation()

            if self.current_skin and self.current_skin.has_action("land"):
                self.play_action("land")
                if self.dialogues_enabled:
                    self.say_context_dialogue("land")
            else:
                self.play_action("idle")
        else:
            self.move(new_x, new_y)
            # 在半空自由下坠期间，主动步进下落动作帧，生动飘飞！
            self._next_frame()

    # ---------------- 对话台词 ----------------

    @property
    def dialogues_enabled(self) -> bool:
        return self.dialogue_manager.enabled

    @dialogues_enabled.setter
    def dialogues_enabled(self, val: bool):
        self.dialogue_manager.enabled = val

    def say_random_dialogue(self):
        text = self.dialogue_manager.get_random_dialogue()
        if text:
            head_pos = self.mapToGlobal(QPoint(self.width() // 2, 0))
            self.bubble.show_text(text, head_pos)

    def say_context_dialogue(self, context: str):
        text = self.dialogue_manager.get_context_dialogue(context)
        if text:
            head_pos = self.mapToGlobal(QPoint(self.width() // 2, 0))
            self.bubble.show_text(text, head_pos)

    # ---------------- 菜单与穿透控制 ----------------

    def show_context_menu(self, global_pos: QPoint):
        menu = build_pet_context_menu(self)
        menu.exec(global_pos)

    def set_click_through(self, enabled: bool):
        self.click_through = enabled
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)

    def toggle_click_through(self):
        self.set_click_through(not self.click_through)

    # ---------------- 绘图渲染 ----------------

    def paintEvent(self, event):
        if not self.current_action or self.current_action.frame_count == 0:
            return

        pixmap = self.current_action.frames[self.current_frame_idx]
        if pixmap.isNull():
            return

        painter = QPainter(self)
        squash = self.squash_stretch.update(0.025)
        tilt = self.current_tilt_deg

        if (
            self._crossfade_step > 0
            and self._prev_pixmap is not None
            and not self._prev_pixmap.isNull()
        ):
            t_norm = 1.0 - (self._crossfade_step / float(self._crossfade_total + 1))
            alpha_new = 0.5 * (1.0 - math.cos(math.pi * t_norm))
            alpha_old = 1.0 - alpha_new
            ZeroAllocRenderer.draw_frame(
                painter,
                self._prev_pixmap,
                self.width(),
                self.height(),
                facing_left=self._prev_facing_left,
                squash_stretch=squash,
                anchor_bottom=True,
                rotation_deg=tilt,
                opacity=alpha_old
            )
            ZeroAllocRenderer.draw_frame(
                painter,
                pixmap,
                self.width(),
                self.height(),
                facing_left=self.facing_left,
                squash_stretch=squash,
                anchor_bottom=True,
                rotation_deg=tilt,
                opacity=alpha_new
            )
        else:
            ZeroAllocRenderer.draw_frame(
                painter,
                pixmap,
                self.width(),
                self.height(),
                facing_left=self.facing_left,
                squash_stretch=squash,
                anchor_bottom=True,
                rotation_deg=tilt
            )

