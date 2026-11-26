# -*- coding: utf-8 -*-
"""
test_phase3_physics.py - 阶段三：物理引擎与桌面交互打磨 自动化验收测试
"""

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QPointF

app = QApplication.instance() or QApplication(sys.argv)

from pet.skin_manager import SkinManager
from pet.window import PetWindow


def get_test_window() -> PetWindow:
    skins_dir = ROOT_DIR / "skins"
    mgr = SkinManager(skins_dir)
    win = PetWindow(
        skin_manager=mgr,
        initial_skin_id="spine_red",
        initial_scale=1.0,
        initial_activity_level="quiet"
    )
    return win


def test_drag_and_pendulum_physics():
    print("\n--- [Test 1] 校验鼠标提溜手感与钟摆受力倾角 ---")
    win = get_test_window()

    # 模拟鼠标按下
    class DummyPressEvent:
        def button(self): return Qt.LeftButton
        def globalPosition(self): return QPointF(500, 500)
        def accept(self): pass

    win.mousePressEvent(DummyPressEvent())
    assert win.is_dragging is True
    assert win.has_dragged is False

    # 模拟鼠标向右快速拖拽位移 (横向拖动 80px)
    class DummyMoveEvent:
        def globalPosition(self): return QPointF(580, 480)
        def accept(self): pass

    # 延时 10ms 制造真实瞬时速度
    time.sleep(0.015)
    win.mouseMoveEvent(DummyMoveEvent())

    assert win.has_dragged is True
    assert win.state == "drag", f"拖拽状态应为 drag, 实际为 {win.state}"
    assert win.current_action.name == "drag"
    print(f"  • 提溜状态正确切入: {win.state} (小短腿扑腾乱蹬)")

    # 验证钟摆产生横向受力倾斜目标
    assert win.drag_pendulum.target > 0.0, "向右拖动应施加向右正向摆角冲量"
    print(f"  • 钟摆倾角目标: {win.drag_pendulum.target:.2f}° (受力自然传导)")

    # 模拟弹性衰减时钟推进 1 步
    win._elastic_step()
    assert abs(win.current_tilt_deg) > 0.0
    print(f"  • 动态倾角生效: {win.current_tilt_deg:.2f}°")
    print("✅ 鼠标提溜悬空扑腾与钟摆惯性手感校验通过")


def test_gravity_free_fall_and_landing():
    print("\n--- [Test 2] 校验半空脱手自由落体抛物线与触地缓冲 ---")
    win = get_test_window()
    ground_y = win.get_ground_y()

    # 1. 模拟将小人提至半空 (离地面 250px)
    win.is_dragging = True
    win.has_dragged = True
    win.move(win.x(), ground_y - 250)
    win.release_velocity = QPointF(4.5, -2.0)  # 赋予横向甩出与向上扬起的轻微初速

    # 2. 模拟松开鼠标
    class DummyReleaseEvent:
        def button(self): return Qt.LeftButton
        def accept(self): pass

    win.mouseReleaseEvent(DummyReleaseEvent())

    assert win.is_dragging is False
    assert win.state == "fall", f"半空脱手应切入 fall, 实际为 {win.state}"
    assert win.physics_timer.isActive() is True, "物理自由落体计时器应激活"
    assert win.velocity_x == 4.5, "应继承横向释放速度"
    assert win.velocity_y == -2.0, "应继承纵向释放速度"
    print("  • 脱手成功进入 fall 状态，并继承释放瞬时速度 ✅")

    # 3. 步进物理自由落体下落循环
    steps_count = 0
    while win.physics_timer.isActive() and steps_count < 60:
        win._physics_step()
        steps_count += 1
        assert win.velocity_y <= win.terminal_velocity, "下落速度不能超过终端速度"

    # 4. 触地着陆判定
    assert win.y() == ground_y, f"触地后 Y 应完全对齐 ground_y ({ground_y}), 实际: {win.y()}"
    assert win.physics_timer.isActive() is False, "触地后物理计时器应停止"
    assert win.squash_stretch.active is True, "触地受力弹性挤压应激活"
    assert win.state == "land", f"触地应切入 land 缓冲动画, 实际为 {win.state}"
    print(f"  • 触地着陆成功！共经过 {steps_count} 物理步，自动切入 land 触地弹性缓冲 ✅")

    # 5. 模拟 land 动作播放完毕
    for _ in range(win.current_action.frame_count):
        win._next_frame()

    assert win.state == "idle", f"land 缓冲播完后应平稳站稳回归 idle, 实际为 {win.state}"
    print("  • land 缓冲播完 -> 平稳挺身站稳，回归 idle 待机长呼吸 ✅")
    print("✅ 自由落体拟真加速度与 1.0s 着陆缓冲动画同步校验通过")


def test_walk_boundary_turn_and_stride_completion():
    print("\n--- [Test 3] 校验左右边缘折返转向与完整步态收脚立正 ---")
    win = get_test_window()
    screen = QApplication.primaryScreen().availableGeometry()

    win.play_action("walk", force=True, use_transition=False)
    win.walk_direction = -1  # 向左走
    win.facing_left = True
    win.walk_steps_remaining = 5

    # 模拟向左走到超出屏幕左边缘
    win.move(screen.left() - 5, win.get_ground_y())
    win._walk_step()

    # 验证左边缘碰撞反弹并朝向右
    assert win.x() >= screen.left(), "不能超出屏幕左边缘"
    assert win.walk_direction == 1, "碰到左边缘应转向右侧"
    assert win.facing_left is False, "朝向应更新为朝右"
    print("  • 屏幕左边缘碰撞检测与自动转向朝右验证通过 ✅")

    # 模拟向右走到超出屏幕右边缘
    win.move(screen.right() + 10, win.get_ground_y())
    win._walk_step()

    # 验证右边缘碰撞反弹并朝向左
    assert win.x() <= screen.right() - win.width(), "不能超出屏幕右边缘"
    assert win.walk_direction == -1, "碰到右边缘应转向左侧"
    assert win.facing_left is True, "朝向应更新为朝左"
    print("  • 屏幕右边缘碰撞检测与自动转向朝左验证通过 ✅")

    # 验证步伐耗尽时脚踏实地收步立正
    win.walk_steps_remaining = 0
    win.current_frame_idx = 10  # 迈步半空中 (非落地帧)
    win._walk_step()
    assert win.state == "walk", "半空迈腿时不能突然刹车中断动作"

    win.current_frame_idx = 28  # 到达跨步周期接地帧
    win._walk_step()
    assert win.state in ("idle", "edge_peek"), "双脚稳稳踩实地平线时自然收脚立正回到 idle 或边缘好奇张望 edge_peek"
    print("  • 步态周期完整收脚立定逻辑验证通过 ✅")
    print("✅ 漫步巡逻屏幕边缘转向与防掉落逻辑校验通过")


def test_headpat_interaction():
    print("\n--- [Test 4] 校验摸头互动与弹性恢复 ---")
    win = get_test_window()

    class DummyClickEvent:
        def button(self): return Qt.LeftButton
        def globalPosition(self): return QPointF(200, 200)
        def accept(self): pass

    win.mousePressEvent(DummyClickEvent())
    # 模拟无位移直接松手 (单击摸头)
    win.mouseReleaseEvent(DummyClickEvent())

    assert win.state == "headpat", f"摸头后应播放 headpat 互动, 实际为 {win.state}"
    assert win.squash_stretch.active is True, "摸头应触发轻微受力弹性形变"
    print("  • 摸头点击触发 headpat 互动与轻微弹性缓冲 ✅")

    for _ in range(win.current_action.frame_count):
        win._next_frame()

    assert win.state == "idle", "摸头完毕后平稳回归 idle 待机姿态"
    print("  • headpat 播毕平稳回归 idle ✅")
    print("✅ 摸头互动反馈与弹性恢复校验通过")


if __name__ == "__main__":
    try:
        test_drag_and_pendulum_physics()
        test_gravity_free_fall_and_landing()
        test_walk_boundary_turn_and_stride_completion()
        test_headpat_interaction()
        print("\n" + "=" * 65)
        print(" 🏆 【阶段三：物理引擎与桌面交互打磨】全部测试 100% 通过！")
        print("=" * 65)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
