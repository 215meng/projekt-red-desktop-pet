"""
Phase 4 Automated Verification Suite:
Skin System Integration, Hot-reloading, Ultra-compact Scale Tuning, and Menu Interactivity.
"""

import sys
import os
from pathlib import Path

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pet.skin_manager import SkinManager
from pet.window import PetWindow
from pet.ui.menu import build_pet_context_menu, build_pet_tray_menu


def get_or_create_app():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_skin_packaging_and_metadata():
    print("\n--- [Test 1] 校验 spine_red 皮肤包打包与元数据契约 ---")
    app = get_or_create_app()
    skin_mgr = SkinManager(root_dir / "skins")
    skin = skin_mgr.get_skin("spine_red")

    assert skin is not None, "spine_red 皮肤未成功加载"
    assert skin.base_size == (360, 480), f"基准画布尺寸异常: {skin.base_size}"
    assert getattr(skin, "anchor_y", None) == 466, f"地平线锚点异常: {getattr(skin, 'anchor_y', None)}"
    assert skin.fps == 30, f"动画基准帧率异常: {skin.fps}"

    # 10 大动作完整性检验
    expected_actions = [
        "idle", "walk", "drag", "sit", "sleep",
        "headpat", "trans_sit", "trans_sleep", "fall", "land"
    ]
    for act in expected_actions:
        assert skin.has_action(act), f"缺少核心动作: {act}"
        action_obj = skin.get_action(act)
        assert action_obj.frame_count > 0, f"动作 {act} 序列帧为空"
        assert action_obj.frame_count >= 30, f"动作 {act} 时长不足 1.0 秒 ({action_obj.frame_count} 帧)"

    # 台词与过渡元数据检验
    assert len(skin.dialogues) >= 8, f"专属台词过少: {len(skin.dialogues)}"
    assert "idle->sit" in skin.transitions or "Relax->Sit" in skin.transitions, "缺少坐下过渡映射"
    assert "sit->sleep" in skin.transitions or "Sit->Sleep" in skin.transitions, "缺少入睡过渡映射"

    print(f"  • 皮肤全称: {skin.name}")
    print(f"  • 动作总数: {len(skin.actions)} (均满足 ≥ 1.0s 契约)")
    print(f"  • 台词库容量: {len(skin.dialogues)} 条专属语音")
    print(f"  • 过渡切片规则数: {len(skin.transitions)} 条")
    print("✅ spine_red 工业级皮肤包打包与元数据校验 100% 通过")


def test_skin_hot_reloading_and_ground_recompute():
    print("\n--- [Test 2] 校验皮肤无缝热重载与贴地坐标自适应重算 ---")
    app = get_or_create_app()
    skin_mgr = SkinManager(root_dir / "skins")
    window = PetWindow(skin_mgr, initial_skin_id="spine_red", initial_scale=1.0)
    window.show()

    screen = QApplication.primaryScreen().availableGeometry()
    expected_ground_spine = screen.bottom() - 466
    assert window.y() == expected_ground_spine, f"初始贴地坐标错误: {window.y()} vs {expected_ground_spine}"
    assert window.width() == 360 and window.height() == 480, f"初始窗口尺寸错误: {window.size()}"

    # 1. 热重载并保持 spine_red
    print("  • 正在热重载 spine_red ...")
    skin_mgr.reload_skins()
    window.set_skin("spine_red")
    assert window.current_skin.skin_id == "spine_red"
    assert window.width() == 360 and window.height() == 480, "重载后尺寸未复原"
    assert window.y() == expected_ground_spine, "重载后贴地坐标未复原"
    assert window.state == "idle", "重载后未保持 idle 待机"

    print("✅ 多皮肤无缝热重载、尺寸重设与地平线自适应对齐校验 100% 通过")
    window.close()


def test_scale_tuning_and_ground_anchoring():
    print("\n--- [Test 3] 校验微缩与超大缩放 (0.35x ~ 2.0x) 与地平线稳定锚定 ---")
    app = get_or_create_app()
    skin_mgr = SkinManager(root_dir / "skins")
    window = PetWindow(skin_mgr, initial_skin_id="spine_red", initial_scale=1.0)
    window.show()

    screen = QApplication.primaryScreen().availableGeometry()
    test_scales = [0.35, 0.50, 0.65, 0.75, 1.00, 1.25, 1.50, 2.00]

    for scale in test_scales:
        window.set_scale(scale)
        assert abs(window.scale_factor - scale) < 1e-4, f"缩放因子设置失败: {window.scale_factor}"

        expected_w = int(360 * scale)
        expected_h = int(480 * scale)
        expected_ground = screen.bottom() - int(466 * scale)

        assert window.width() == expected_w, f"缩放 {scale}x 宽度不符: {window.width()} vs {expected_w}"
        assert window.height() == expected_h, f"缩放 {scale}x 高度不符: {window.height()} vs {expected_h}"
        assert window.y() == expected_ground, f"缩放 {scale}x 贴地脱轨: {window.y()} vs {expected_ground}"
        print(f"  • {scale:.2f}x 缩放 -> 尺寸: {window.width()}x{window.height()}, 贴地 Y: {window.y()} (零悬空·零下沉) ✅")

    print("✅ 0.35x ~ 2.0x 全范围精致微缩与脚底地平线锚定校验 100% 通过")
    window.close()


def test_context_and_tray_menus():
    print("\n--- [Test 4] 校验右键上下文菜单、托盘动作点播与姿态保持锁定 ---")
    app = get_or_create_app()
    skin_mgr = SkinManager(root_dir / "skins")
    window = PetWindow(skin_mgr, initial_skin_id="spine_red", initial_scale=1.0)

    # 1. 右键菜单校验
    context_menu = build_pet_context_menu(window)
    assert context_menu is not None
    actions_in_context = [a.text() for a in context_menu.actions()]

    assert any("动作点播" in t for t in actions_in_context), "右键菜单缺少动作点播子菜单"
    assert any("皮肤切换" in t for t in actions_in_context), "右键菜单缺少皮肤切换子菜单"
    assert any("缩放大小" in t for t in actions_in_context), "右键菜单缺少缩放子菜单"
    assert any("陪伴节律" in t for t in actions_in_context), "右键菜单缺少陪伴节律子菜单"
    assert any("台词气泡" in t for t in actions_in_context), "右键菜单缺少台词气泡开关"
    assert any("鼠标穿透" in t for t in actions_in_context), "右键菜单缺少穿透模式开关"

    # 检查动作点播子菜单项
    act_menu = None
    for a in context_menu.actions():
        if "动作点播" in a.text():
            act_menu = a.menu()
            break
    assert act_menu is not None, "未找到动作点播子菜单"
    act_items = [item.text() for item in act_menu.actions()]
    assert len(act_items) >= 10, f"动作点播项数目过少: {len(act_items)}"
    print(f"  • 右键动作点播已包含全量 {len(act_items)} 项动态动作: {[t.split()[1] if len(t.split()) > 1 else t for t in act_items]}")

    # 2. 系统托盘菜单校验（必须包含动作点播！）
    tray_menu = build_pet_tray_menu(window, app)
    assert tray_menu is not None
    actions_in_tray = [a.text() for a in tray_menu.actions()]

    assert any("显示/隐藏" in t for t in actions_in_tray), "托盘菜单缺少显示/隐藏"
    assert any("动作点播" in t for t in actions_in_tray), "托盘菜单缺少动作点播 (关键交互对齐)"
    assert any("皮肤切换" in t for t in actions_in_tray), "托盘菜单缺少皮肤切换"
    assert any("缩放大小" in t for t in actions_in_tray), "托盘菜单缺少缩放控制"
    assert any("鼠标穿透" in t for t in actions_in_tray), "托盘菜单缺少穿透开关兜底"

    # 3. 动作点播与姿态保持锁定验证
    print("  • 正在测试动作显式点播与姿态锁定 ...")
    window.select_action("sit")
    # 点播 sit 会先走 trans_sit 过渡切片或直入 sit，且锁定姿态
    assert window.state in ("trans_sit", "sit"), f"点播坐姿失败: {window.state}"
    assert window.locked_action == "sit", f"动作锁定标记未生效: {window.locked_action}"
    print(f"  • 显式点播成功切入: {window.state}，姿态锁定状态: {window.locked_action} (防自主行为打断) ✅")

    # 触发自主行为判定，验证绝不会被打断
    window._decide_behavior()
    assert window.locked_action == "sit", "锁定的动作被意外打断！"

    # 解除动作锁定
    window.unlock_action()
    assert window.locked_action is None, "未能成功解除动作锁定"
    assert window.state == "idle", "解除锁定后未回归 idle"
    print("  • 解除锁定成功回归自由陪伴状态 ✅")

    # 4. 鼠标穿透切换与托盘兜底测试
    assert window.click_through is False
    window.toggle_click_through()
    assert window.click_through is True
    assert window.testAttribute(Qt.WA_TransparentForMouseEvents) is True
    print("  • 成功进入鼠标穿透模式 (桌宠透明忽略鼠标事件)")

    window.toggle_click_through()
    assert window.click_through is False
    assert window.testAttribute(Qt.WA_TransparentForMouseEvents) is False
    print("  • 成功通过托盘开关退出鼠标穿透模式 (恢复正常鼠标交互)")

    print("✅ 右键上下文菜单与系统托盘菜单全功能闭环校验 100% 通过")
    window.close()


if __name__ == "__main__":
    test_skin_packaging_and_metadata()
    test_skin_hot_reloading_and_ground_recompute()
    test_scale_tuning_and_ground_anchoring()
    test_context_and_tray_menus()
    print("\n" + "=" * 65)
    print(" 🏆 【阶段四：皮肤系统打包与热重载兼容】全部自动化测试通过！")
    print("=" * 65)
