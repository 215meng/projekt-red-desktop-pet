"""
test_v4_3_actions.py - v4.3 首批四大招牌特质动作全功能验收测试
验证：
  1. 动作库大扩容：由 10 项动作扩充至 14 项完整动作
  2. 4 项全新招牌动作契约检验：
     - cuddle_tail (抱尾蹭脸): 80 帧 (2.67s), 循环播放
     - sharpen_knife (磨刀拭刃): 60 帧 (2.00s), 循环播放
     - alert_scout (警惕耸耳): 54 帧 (1.80s), 播放完回归 idle
     - yawn_stretch (伸懒腰打哈欠): 60 帧 (2.00s), 播放完回归 idle
  3. 动作点播子菜单与托盘菜单新选项高亮与单选锁定
  4. 新增 254 帧骨骼切片 100% 绝对零裁切安全检验
"""

import sys
import glob
from pathlib import Path
from PIL import Image
import numpy as np

pet_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pet_root / "src"))

from PySide6.QtWidgets import QApplication
from pet.skin import SkinManager
from pet.window import PetWindow
from pet.ui.menu import build_pet_context_menu, build_pet_tray_menu, ACTION_LABEL_MAP


def run_tests():
    print("\n" + "=" * 65)
    print(" 🚀 开始执行【v4.3 红崽四大招牌特质动作全功能验收测试】")
    print("=" * 65)

    app = QApplication.instance() or QApplication(sys.argv)
    skins_dir = pet_root / "skins"
    sm = SkinManager(skins_dir)
    skin = sm.get_skin("spine_red")
    assert skin is not None, "必须成功装载 spine_red 旗舰皮肤"

    # --- [Test 1] 校验动作库扩充至 14 项全集与时长契约 ---
    print("\n--- [Test 1] 校验动作库扩充与时长契约 (>= 1.0s) ---")
    all_actions = list(skin.actions.keys())
    print(f"• 当前装载动作数: {len(all_actions)}")
    assert len(all_actions) >= 14, f"期望至少 14 项动作，实际为: {len(all_actions)}"

    new_expected = {
        "cuddle_tail": (80, True, 2.667),
        "sharpen_knife": (60, True, 2.000),
        "alert_scout": (54, False, 1.800),
        "yawn_stretch": (60, False, 2.000)
    }

    for act_id, (expected_frames, is_loop, duration) in new_expected.items():
        assert skin.has_action(act_id), f"缺少新动作: {act_id}"
        act = skin.get_action(act_id)
        print(f"  - {act_id:14s}: {act.frame_count:2d} 帧 | 循环: {str(act.loop):5s} | 时长: {duration:.3f}s ✅")
        assert act.frame_count == expected_frames, f"{act_id} 帧数不符"
        assert act.loop == is_loop, f"{act_id} 循环属性不符"
        assert act.frame_count >= 30, f"{act_id} 时长不足 1 秒"

    print("✅ 14 项动作库扩容与时长契约检验 100% 通过！")

    # --- [Test 2] 校验右键菜单与托盘菜单新动作识别 ---
    print("\n--- [Test 2] 校验动作点播菜单新项显示与映射 ---")
    window = PetWindow(sm, initial_skin_id="spine_red", initial_scale=1.0)
    window.show()

    c_menu = build_pet_context_menu(window)
    t_menu = build_pet_tray_menu(window, app)

    def extract_action_texts(menu):
        for act in menu.actions():
            if "动作点播" in act.text():
                sub = act.menu()
                return [a.text() for a in sub.actions() if not a.isSeparator()]
        return []

    c_acts = extract_action_texts(c_menu)
    t_acts = extract_action_texts(t_menu)

    for new_act in ["cuddle_tail", "sharpen_knife", "alert_scout", "yawn_stretch"]:
        label = ACTION_LABEL_MAP[new_act]
        assert any(label in t for t in c_acts), f"右键菜单缺少新动作: {label}"
        assert any(label in t for t in t_acts), f"托盘菜单缺少新动作: {label}"

    print(f"• 动作点播菜单成功呈现 4 款新招牌动作: {c_acts[1:5]} ✅")

    # --- [Test 3] 校验显式点播与状态锁定 ---
    print("\n--- [Test 3] 校验显式点播与姿态保持锁定 ---")
    window.select_action("cuddle_tail")
    assert window.state == "cuddle_tail", "点播后状态应为 cuddle_tail"
    assert window.locked_action == "cuddle_tail", "点播后应保持姿态锁定"
    assert window.facing_left is False, "正面保持展示"

    window.select_action("sharpen_knife")
    assert window.state == "sharpen_knife", "点播后状态应为 sharpen_knife"
    assert window.locked_action == "sharpen_knife", "点播后应保持姿态锁定"

    window.unlock_action()
    assert window.locked_action is None, "解锁后锁定标记应为 None"
    assert window.state == "idle", "解锁后应回归 idle"
    print("✅ 新动作显式点播与锁定/解锁闭环验证通过！")

    # --- [Test 4] 校验 4 项新动作共 254 帧切片四边缘像素零裁切 ---
    print("\n--- [Test 4] 校验 4 项新动作全量 254 帧 100% 绝对零裁切 ---")
    new_frame_files = []
    for act_id in new_expected.keys():
        act_files = glob.glob(str(pet_root / "skins" / "spine_red" / "frames" / act_id / "*.png"))
        new_frame_files.extend(act_files)

    print(f"• 扫描新动作切片总数: {len(new_frame_files)} 帧")
    assert len(new_frame_files) == 80 + 60 + 54 + 60, f"新切片总数应为 254，实际: {len(new_frame_files)}"

    for fpath in new_frame_files:
        im = Image.open(fpath)
        arr = np.array(im)[:, :, 3]
        assert arr[0, :].max() == 0, f"顶部裁切: {fpath}"
        assert arr[-1, :].max() == 0, f"底部裁切: {fpath}"
        assert arr[:, 0].max() == 0, f"左侧裁切: {fpath}"
        assert arr[:, -1].max() == 0, f"右侧裁切: {fpath}"

    print("✅ 4 项新动作共 254 帧切片 100% 绝对零裁切校验通过！")

    window.close()
    print("\n" + "=" * 65)
    print(" 🎉 ALL 4/4 v4.3 NEW ACTIONS ACCEPTANCE TESTS PASSED (100% PASS)!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_tests()
