"""
test_anatomical_and_transition_quality.py - v4.5 解剖学连续性与过渡质量自动化审计测试
覆盖：
1. 全量 875 帧四边界零裁切验证
2. 零头身分离检测（颈部到躯干竖直像素 100% 连通，绝无水平透明断裂带）
3. 统一接地底线审计（全地面动作对齐 Y = 425 ± 4px）
4. 真·过渡与首尾闭合连续性（trans_sit / trans_sleep / 派生动作首尾 bbox 偏差 <= 3px）
5. 运行时行为审计（4 次 headpat vs 5 次狂戳 dizzy、doze_off 回归 sit、Crossfade 平滑淡入淡出）
"""

import os
import sys
import json
import glob
from pathlib import Path
from PIL import Image

pet_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pet_root / "src"))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from pet.skin import SkinManager
from pet.core import PetStateMachine
from pet.ui.menu import ACTION_LABEL_MAP, build_pet_context_menu, build_pet_tray_menu
from pet.window import PetWindow


SKIN_DIR = pet_root / "skins" / "spine_red"
FRAMES_DIR = SKIN_DIR / "frames"


def _load_manifest():
    with open(SKIN_DIR / "skin.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _get_action_frames(act_name: str):
    return sorted(glob.glob(str(FRAMES_DIR / act_name / "*.png")))


def _bbox_dist(b1, b2) -> int:
    return max(abs(a - b) for a, b in zip(b1, b2))


def test_zero_clipping_all_875_frames():
    manifest = _load_manifest()
    actions = manifest["actions"]
    total = 0
    for act_name, meta in actions.items():
        files = _get_action_frames(act_name)
        assert len(files) == meta["frames_count"], f"{act_name}: count mismatch"
        total += len(files)
        for fp in files:
            with Image.open(fp) as im:
                rgba = im.convert("RGBA")
                assert rgba.size == (360, 480), f"{fp}: unexpected size {rgba.size}"
                bbox = rgba.getbbox()
                assert bbox is not None, f"{fp}: completely transparent frame"
                l, t, r, b = bbox
                assert l > 0 and t > 0 and r < 360 and b < 480, (
                    f"{fp}: clipped bbox {bbox}"
                )
    assert total == 875, f"Expected 875 total frames, got {total}"
    print(f"[PASS] test_zero_clipping_all_875_frames (verified {total} frames)")


def test_zero_head_body_detachment():
    # 所有竖直站姿/坐姿/悬空/缓冲动作：头部与躯干之间绝对不能出现整行透明断裂
    upright_actions = [
        "idle", "walk", "drag", "sit", "headpat", "dizzy", "trans_sit",
        "fall", "land", "cuddle_tail", "sharpen_knife", "alert_scout",
        "yawn_stretch", "edge_peek", "doze_off"
    ]
    checked = 0
    for act in upright_actions:
        for fp in _get_action_frames(act):
            checked += 1
            with Image.open(fp) as im:
                rgba = im.convert("RGBA")
                w, h = rgba.size
                alpha = rgba.getchannel("A")
                bbox = alpha.getbbox()
                assert bbox is not None
                _, y0, _, y1 = bbox
                span = y1 - y0
                # 取角色主体上下 25%~70% 区间（覆盖脖颈、围巾与上下身连接处）
                scan_top = int(y0 + span * 0.25)
                scan_bot = int(y0 + span * 0.70)
                raw = alpha.tobytes()
                for y in range(scan_top, scan_bot + 1):
                    row = raw[y * w : (y + 1) * w]
                    if max(row) < 20:
                        raise AssertionError(
                            f"Head/body horizontal gap detected at y={y} in {fp} (bbox={bbox})"
                        )
    print(f"[PASS] test_zero_head_body_detachment (checked {checked} upright frames)")


def test_unified_ground_line():
    manifest = _load_manifest()
    grounded_actions = [
        act for act in manifest["actions"].keys()
        if act not in ("drag", "fall")
    ]
    for act in grounded_actions:
        files = _get_action_frames(act)
        bottoms = []
        for fp in files:
            with Image.open(fp) as im:
                bbox = im.convert("RGBA").getbbox()
                bottoms.append(bbox[3])
        if act == "trans_sleep":
            assert abs(bottoms[0] - 425) <= 2, f"trans_sleep[0] bottom={bottoms[0]}"
            assert abs(bottoms[-1] - 425) <= 2, f"trans_sleep[-1] bottom={bottoms[-1]}"
            assert max(bottoms) <= 429, f"trans_sleep max bottom={max(bottoms)}"
        elif act == "land":
            # v4.2 立定屈膝着陆：首帧承接 fall[0] 脚尖微垂，中段压实吸震不跪坐，末帧严格对齐 425px
            assert abs(bottoms[-1] - 425) <= 3, f"land[-1] bottom={bottoms[-1]}"
            assert min(bottoms) >= 421 and max(bottoms) <= 445, (
                f"land ground range out of [421, 445] -> [{min(bottoms)}, {max(bottoms)}]"
            )
        else:
            min_b, max_b = min(bottoms), max(bottoms)
            assert min_b >= 421 and max_b <= 429, (
                f"{act}: ground line drift out of 425±4px -> [{min_b}, {max_b}]"
            )
    print(f"[PASS] test_unified_ground_line ({len(grounded_actions)} grounded actions)")


def test_transitions_and_loop_closure():
    def frame_bbox(act, idx):
        files = _get_action_frames(act)
        with Image.open(files[idx]) as im:
            return im.convert("RGBA").getbbox()

    idle0 = frame_bbox("idle", 0)
    sit0 = frame_bbox("sit", 0)
    sleep0 = frame_bbox("sleep", 0)

    # 双轨道真过渡首尾连续性
    assert _bbox_dist(frame_bbox("trans_sit", 0), idle0) <= 2
    assert _bbox_dist(frame_bbox("trans_sit", -1), sit0) <= 2
    assert _bbox_dist(frame_bbox("trans_sleep", 0), sit0) <= 2
    assert _bbox_dist(frame_bbox("trans_sleep", -1), sleep0) <= 2

    # 站姿完整 2.00s 周期派生动作首尾闭合于 idle[0]
    for act in ("sharpen_knife", "yawn_stretch", "edge_peek"):
        assert _bbox_dist(frame_bbox(act, 0), idle0) <= 3, f"{act}[0] vs idle[0]"
        assert _bbox_dist(frame_bbox(act, -1), idle0) <= 3, f"{act}[-1] vs idle[0]"

    # 非 2.00s 短周期动作：首帧接 idle[0]，末帧完美回归对应 Relax 同相位且脚底齐平
    short_phase_map = {
        "headpat": 45,      # 1.50s -> Relax 3/4 周期
        "alert_scout": 54,  # 1.80s -> Relax 9/10 周期
    }
    for act, idle_idx in short_phase_map.items():
        b_start = frame_bbox(act, 0)
        b_end = frame_bbox(act, -1)
        b_phase = frame_bbox("idle", idle_idx)
        assert _bbox_dist(b_start, idle0) <= 3, f"{act}[0] vs idle[0]"
        assert _bbox_dist(b_end, b_phase) <= 3, f"{act}[-1] vs idle[{idle_idx}]"
        assert abs(b_end[3] - idle0[3]) <= 2, f"{act}[-1] ground line vs idle[0]"

    assert _bbox_dist(frame_bbox("land", -1), idle0) <= 3, "land[-1] vs idle[0]"

    # 坐姿派生动作首尾闭合于 sit[0]
    for act in ("cuddle_tail", "doze_off"):
        assert _bbox_dist(frame_bbox(act, 0), sit0) <= 3, f"{act}[0] vs sit[0]"
        assert _bbox_dist(frame_bbox(act, -1), sit0) <= 3, f"{act}[-1] vs sit[0]"

    print("[PASS] test_transitions_and_loop_closure")


def test_runtime_dizzy_and_sit_return_and_crossfade():
    app = QApplication.instance() or QApplication(sys.argv)
    sm = PetStateMachine()
    assert "dizzy" in sm.VALID_STATES
    assert "dizzy" in ACTION_LABEL_MAP

    skin_mgr = SkinManager(pet_root / "skins")
    win = PetWindow(skin_mgr, initial_skin_id="spine_red")
    win.dialogues_enabled = False

    # 1. 验证 Crossfade：从 idle 切往 sharpen_knife 会触发 4 帧柔化淡入，4 帧后清空
    win.play_action("idle", force=True, use_transition=False)
    win.play_action("sharpen_knife", force=True, use_transition=False)
    assert win.state == "sharpen_knife"
    assert win._crossfade_step == 4
    assert win._prev_pixmap is not None
    for _ in range(4):
        win._next_frame()
    assert win._crossfade_step == 0
    assert win._prev_pixmap is None

    # 2. 验证 doze_off 播完自动回归 sit 而非 idle
    win.play_action("doze_off", force=True, use_transition=False)
    assert win.state == "doze_off"
    win.current_frame_idx = win.current_action.frame_count - 1
    win._next_frame()
    assert win.state == "sit", f"Expected doze_off to return to sit, got {win.state}"

    # 3. 验证 2 秒内连续点击：前 4 次为 headpat，第 5 次触发 dizzy 彩蛋
    def _simulate_click():
        local_pos = QPointF(win.width() / 2.0, win.height() / 2.0)
        global_pos = QPointF(win.mapToGlobal(local_pos.toPoint()))
        press = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            local_pos, global_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier
        )
        release = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            local_pos, global_pos, Qt.LeftButton, Qt.NoButton, Qt.NoModifier
        )
        win.mousePressEvent(press)
        win.mouseReleaseEvent(release)

    win.play_action("idle", force=True, use_transition=False)
    for i in range(4):
        _simulate_click()
        assert win.state == "headpat", f"Click {i + 1} expected headpat, got {win.state}"

    _simulate_click()
    assert win.state == "dizzy", f"5th rapid click expected dizzy, got {win.state}"
    assert len(win._recent_click_times) == 0

    # 4. 验证右键菜单与托盘菜单简洁纯文字、无 Emoji 迷你图标
    def _collect_texts(menu_obj):
        items = []
        for a in menu_obj.actions():
            if a.text():
                items.append(a.text())
            if a.menu() is not None:
                items.extend(_collect_texts(a.menu()))
        return items

    all_menu_texts = _collect_texts(build_pet_context_menu(win)) + _collect_texts(build_pet_tray_menu(win, app))
    assert len(all_menu_texts) >= 20
    for txt in all_menu_texts:
        for ch in txt:
            cp = ord(ch)
            assert not (cp >= 0x1F300 or 0x2600 <= cp <= 0x27BF or 0xFE00 <= cp <= 0xFE0F), (
                f"Menu text must be minimalist without emoji: {txt!r}"
            )

    print("[PASS] test_runtime_dizzy_and_sit_return_and_crossfade")


if __name__ == "__main__":
    test_zero_clipping_all_875_frames()
    test_zero_head_body_detachment()
    test_unified_ground_line()
    test_transitions_and_loop_closure()
    test_runtime_dizzy_and_sit_return_and_crossfade()
    print("\nALL ANATOMICAL & TRANSITION QUALITY AUDIT TESTS PASSED!")
