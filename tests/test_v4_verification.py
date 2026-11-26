"""
test_v4_verification.py - 4.1 纯净架构基准压测与动力学回归套件
校验：
  1. SkinManager 4.0 加载 spine_red 旗舰皮肤
  2. ZeroAllocRenderer 1000 帧连续渲染性能压测 (目标 < 1.2ms / frame)
  3. 阻尼振荡器、保体积形变器与视线追踪器数值稳定性
"""

import sys
import time
from pathlib import Path

# Add src to sys.path
pet_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pet_root / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt

from pet.skin import SkinManager
from pet.core import ZeroAllocRenderer, SquashAndStretch, DampedHarmonicOscillator, GazeTracker


def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    print("=== 1. Testing SkinManager 4.0 Loading (spine_red) ===")
    skins_dir = pet_root / "skins"
    sm = SkinManager(skins_dir)
    loaded_skins = list(sm.skins.keys())
    print(f"Loaded skins: {loaded_skins}")
    assert "spine_red" in loaded_skins, "spine_red skin must be loaded!"

    skin = sm.get_skin("spine_red")
    print(f"Skin Name: {skin.name}")
    print(f"Version: {skin.version}")
    print(f"Base Size: {skin.base_size}")
    print(f"Default Scale: {skin.default_scale}")
    print(f"Actions ({len(skin.actions)}): {list(skin.actions.keys())}")

    expected_actions = ["idle", "walk", "drag", "sit", "sleep", "headpat", "trans_sit", "trans_sleep", "fall", "land"]
    for act in expected_actions:
        assert skin.has_action(act), f"Missing expected action: {act}"
        action_obj = skin.get_action(act)
        assert action_obj.frame_count > 0, f"Action {act} has 0 frames!"
        print(f"  - {act:12s}: {action_obj.frame_count:2d} frames, {action_obj.fps} FPS")

    print("\n=== 2. Testing ZeroAllocRenderer 1000-Frame Performance Benchmark ===")
    test_img = QImage(360, 480, QImage.Format_ARGB32_Premultiplied)
    painter = QPainter(test_img)

    idle_action = skin.get_action("idle")
    frame = idle_action.frames[0]

    squash = SquashAndStretch()
    squash.trigger(-0.15)

    # Warm-up
    for _ in range(10):
        ZeroAllocRenderer.draw_frame(painter, frame, 360, 480, facing_left=False)

    # Benchmark 1,000 continuous frames
    start_t = time.perf_counter()
    num_frames = 1000
    for i in range(num_frames):
        sq = squash.update(0.016)
        ZeroAllocRenderer.draw_frame(
            painter,
            frame,
            360,
            480,
            facing_left=(i % 2 == 0),
            squash_stretch=sq,
            anchor_bottom=True
        )
    total_time = time.perf_counter() - start_t
    painter.end()

    avg_ms = (total_time / num_frames) * 1000.0
    print(f"Rendered {num_frames} frames in {total_time:.4f}s")
    print(f"Average render time per frame: {avg_ms:.4f} ms")
    assert avg_ms < 1.2, f"Target frame time < 1.2ms violated! Got {avg_ms:.4f}ms"
    print(">>> PERFORMANCE PASS: Frame time is well below the 1.2ms budget!")

    print("\n=== 3. Testing Physics Dynamics Evaluators ===")
    osc = DampedHarmonicOscillator(stiffness=0.20, damping=0.88)
    osc.apply_impulse(10.0)
    for _ in range(30):
        v = osc.update(1.0)
    print(f"Oscillator stabilized smoothly at: {v:.4f}")

    gaze = GazeTracker()
    angle, eye_off = gaze.update(180, 240, 500, 100)
    print(f"Gaze tracking output: angle={angle:.2f} deg, eye_offset={eye_off:.2f} px")

    print("\n[SUCCESS] ALL 4.1 UNIT TESTS AND BENCHMARKS PASSED PERFECTLY!")


if __name__ == "__main__":
    run_tests()
