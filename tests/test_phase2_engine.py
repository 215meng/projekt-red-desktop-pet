# -*- coding: utf-8 -*-
"""
test_phase2_engine.py - 阶段二：渲染内核与状态机升级 自动化验收测试
"""

import os
import sys
from pathlib import Path

# 确保加载项目源码
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from PySide6.QtWidgets import QApplication

# 确保 QApplication 单例存在
app = QApplication.instance() or QApplication(sys.argv)

from pet.core import (
    ZeroAllocRenderer,
    TransitionScheduler,
    SquashAndStretch,
    DampedHarmonicOscillator,
    GazeTracker
)
from pet.skin_manager import SkinManager
from pet.window import PetWindow


def test_anim_module_and_rig_cleanup():
    print("\n--- [Test 1] 校验 anim 模块架构与旧版 rig 清理 ---")
    # 验证 ZeroAllocRenderer 不再引用旧版纸娃娃
    assert not hasattr(ZeroAllocRenderer, "draw_rig"), "ZeroAllocRenderer.draw_rig 应该已被彻底废除！"
    print("✅ ZeroAllocRenderer.draw_rig 已彻底清理，无纸娃娃残留")

    # 验证 TransitionScheduler 正常工作
    scheduler = TransitionScheduler({"idle->sit": "trans_sit"})
    assert scheduler.get_transition("idle", "sit") == "trans_sit"
    assert scheduler.get_transition("idle", "walk") is None
    print("✅ TransitionScheduler 独立状态调度器验证通过")


def test_skin_manager_spine_red():
    print("\n--- [Test 2] 校验 SkinManager 对 spine_red 工业级皮肤的装载 ---")
    skins_dir = ROOT_DIR / "skins"
    mgr = SkinManager(skins_dir)

    available = mgr.reload_skins()
    print(f"• 发现可用皮肤: {available}")
    assert "spine_red" in available, "未发现 spine_red 皮肤！"

    skin = mgr.get_skin("spine_red")
    assert skin is not None
    assert skin.base_size == (360, 480), f"尺寸不匹配: {skin.base_size}"
    assert skin.anchor_y == 466, f"接地面锚点不匹配: {skin.anchor_y}"

    expected_actions = [
        "idle", "walk", "drag", "sit", "sleep",
        "headpat", "trans_sit", "trans_sleep", "fall", "land"
    ]
    for act in expected_actions:
        assert skin.has_action(act), f"缺少关键动作: {act}"
        action_obj = skin.get_action(act)
        assert action_obj.frame_count > 0, f"动作 {act} 帧数为空！"
        print(f"  - 动作 {act:<12}: {action_obj.frame_count:3d} 帧 | 类型: {action_obj.action_type:<10} | 下一跳: {action_obj.next_action}")

    # 验证过渡切片下一跳设置
    assert skin.get_action("trans_sit").next_action == "sit"
    assert skin.get_action("trans_sleep").next_action == "sleep"
    assert skin.get_action("land").next_action == "idle"
    print("✅ spine_red 皮肤 10 大动作与过渡切片映射验证 100% 通过")


def test_pet_window_transition_state_machine():
    print("\n--- [Test 3] 校验 PetWindow 状态机无缝过渡拦截与驱动流程 ---")
    skins_dir = ROOT_DIR / "skins"
    mgr = SkinManager(skins_dir)

    window = PetWindow(
        skin_manager=mgr,
        initial_skin_id="spine_red",
        initial_scale=1.0,
        initial_activity_level="quiet"
    )

    # 1. 验证初始状态为 idle
    assert window.state == "idle", f"初始状态应为 idle, 实际为 {window.state}"
    assert window.current_action.name == "idle"
    print("  1. 初始状态为 idle 待机长呼吸 ✅")

    # 2. 模拟切换至 sit: 验证中间过渡切片 trans_sit 是否被自动拦截并插入
    window.play_action("sit")
    assert window.state == "trans_sit", f"应自动切入过渡切片 trans_sit, 实际状态为 {window.state}"
    assert window.current_action.name == "trans_sit"
    assert window.current_action.next_action == "sit"
    print("  2. 请求切换至 sit -> 成功拦截并切入 trans_sit 骨骼平滑过渡切片 ✅")

    # 模拟 trans_sit 帧推进至完成
    for _ in range(window.current_action.frame_count):
        window._next_frame()

    # 验证过渡切片播放完毕后，自动无缝接驳进入 sit 状态！
    assert window.state == "sit", f"trans_sit 播放完毕后应自动接轨进入 sit, 实际为 {window.state}"
    assert window.current_action.name == "sit"
    print("  3. trans_sit 播完 -> 自动接轨进入 sit 抱尾乖坐姿态 (0 瞬移) ✅")

    # 3. 模拟从 sit 切换至 sleep: 验证是否自动插入 trans_sleep
    window.play_action("sleep")
    assert window.state == "trans_sleep", f"应自动切入过渡切片 trans_sleep, 实际为 {window.state}"
    assert window.current_action.name == "trans_sleep"
    assert window.current_action.next_action == "sleep"
    print("  4. 请求切换至 sleep -> 成功拦截并切入 trans_sleep 骨骼平滑过渡切片 ✅")

    # 模拟 trans_sleep 帧推进至完成
    for _ in range(window.current_action.frame_count):
        window._next_frame()

    assert window.state == "sleep", f"trans_sleep 播放完毕后应自动进入 sleep, 实际为 {window.state}"
    assert window.current_action.name == "sleep"
    print("  5. trans_sleep 播完 -> 自动接轨进入 sleep 蜷缩熟睡姿态 (0 瞬移) ✅")

    # 4. 模拟摸头点击互动 (headpat)
    window.play_action("headpat")
    assert window.state == "headpat", f"应进入 headpat, 实际为 {window.state}"
    for _ in range(window.current_action.frame_count):
        window._next_frame()
    assert window.state == "idle", f"headpat 播放完毕后应回归 idle, 实际为 {window.state}"
    print("  6. 摸头互动 headpat 播放完毕 -> 自然回归 idle 待机姿态 ✅")

    # 5. 模拟悬空提溜与落地缓冲 (drag -> fall -> land -> idle)
    window.play_action("drag")
    assert window.state == "drag"
    print("  7. 鼠标拖拽提起 -> 进入 drag 悬空小短腿扑腾乱蹬姿态 ✅")

    window.play_action("fall")
    assert window.state == "fall"
    print("  8. 松开鼠标半空自由落体 -> 进入 fall 迎风翻卷姿态 ✅")

    window.play_action("land")
    assert window.state == "land"
    assert window.current_action.next_action == "idle"
    print("  9. 触地受力弹性下蹲 -> 进入 land 触地缓冲切片 ✅")

    for _ in range(window.current_action.frame_count):
        window._next_frame()
    assert window.state == "idle"
    print("  10. land 缓冲结束 -> 平稳挺身站稳，回归 idle 待机姿态 ✅")

    print("\n🎉 【全套状态机平滑迁移调度测试 100% PASS】！彻底消灭部位瞬移与肢体跳跃！")


if __name__ == "__main__":
    try:
        test_anim_module_and_rig_cleanup()
        test_skin_manager_spine_red()
        test_pet_window_transition_state_machine()
        print("\n" + "=" * 65)
        print(" 🏆 【阶段二：渲染内核与状态机升级】全部自动化测试通过！")
        print("=" * 65)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
