"""
test_v4_4_context_actions.py - v4.4 环境感知与情境动作专项测试套件
验证屏幕边缘探头张望 (edge_peek) 与深夜瞌睡伴守 (doze_off) 的契约、切片与状态迁移。
"""

import os
import sys
import json
import glob
from pathlib import Path

pet_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pet_root / "src"))

# 确保无头环境
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from pet.skin import SkinManager
from pet.core import PetStateMachine
from pet.ui.menu import ACTION_LABEL_MAP
from pet.window import PetWindow

def test_v4_4_manifest_contract():
    skin_path = str(pet_root / "skins" / "spine_red" / "skin.json")
    with open(skin_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    actions = data.get("actions", {})
    assert "edge_peek" in actions, "Missing edge_peek action in skin.json!"
    assert "doze_off" in actions, "Missing doze_off action in skin.json!"

    ep = actions["edge_peek"]
    do = actions["doze_off"]

    assert ep["frames_count"] == 60, f"edge_peek frames mismatch: {ep['frames_count']}"
    assert ep["duration"] >= 1.0, f"edge_peek duration too short: {ep['duration']}"
    assert do["frames_count"] == 80, f"doze_off frames mismatch: {do['frames_count']}"
    assert do["duration"] >= 1.0, f"doze_off duration too short: {do['duration']}"
    print("[PASS] test_v4_4_manifest_contract")

def test_v4_4_frames_integrity():
    ep_dir = str(pet_root / "skins" / "spine_red" / "frames" / "edge_peek")
    do_dir = str(pet_root / "skins" / "spine_red" / "frames" / "doze_off")

    ep_files = sorted(glob.glob(os.path.join(ep_dir, "*.png")))
    do_files = sorted(glob.glob(os.path.join(do_dir, "*.png")))

    assert len(ep_files) == 60, f"Expected 60 frames for edge_peek, got {len(ep_files)}"
    assert len(do_files) == 80, f"Expected 80 frames for doze_off, got {len(do_files)}"

    for f in ep_files[:5] + do_files[:5]:
        assert os.path.getsize(f) > 1000, f"Frame too small or corrupted: {f}"

    print("[PASS] test_v4_4_frames_integrity")

def test_v4_4_ui_menu_mapping():
    assert "edge_peek" in ACTION_LABEL_MAP, "edge_peek missing in ACTION_LABEL_MAP"
    assert "doze_off" in ACTION_LABEL_MAP, "doze_off missing in ACTION_LABEL_MAP"
    print("[PASS] test_v4_4_ui_menu_mapping")

def test_v4_4_state_machine_and_playback():
    app = QApplication.instance() or QApplication(sys.argv)
    sm = PetStateMachine()
    assert "edge_peek" in sm.VALID_STATES, "edge_peek missing in PetStateMachine.VALID_STATES"
    assert "doze_off" in sm.VALID_STATES, "doze_off missing in PetStateMachine.VALID_STATES"

    skin_mgr = SkinManager(pet_root / "skins")
    win = PetWindow(skin_mgr, initial_skin_id="spine_red")

    # 验证点播 edge_peek
    win.play_action("edge_peek", force=True)
    assert win.state == "edge_peek", f"Expected state edge_peek, got {win.state}"
    assert win.current_action.frame_count == 60, "Current action frame count mismatch for edge_peek"

    # 验证点播 doze_off
    win.play_action("doze_off", force=True)
    assert win.state == "doze_off", f"Expected state doze_off, got {win.state}"
    assert win.current_action.frame_count == 80, "Current action frame count mismatch for doze_off"

    print("[PASS] test_v4_4_state_machine_and_playback")

if __name__ == "__main__":
    test_v4_4_manifest_contract()
    test_v4_4_frames_integrity()
    test_v4_4_ui_menu_mapping()
    test_v4_4_state_machine_and_playback()
    print("\nALL V4.4 CONTEXT ACTION TESTS PASSED!")
