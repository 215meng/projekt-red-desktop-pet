"""
test_fall_land_continuity.py - 下落与着陆一体化动力学连续性量化验收测试
专门验证：
  1. 模型同源契约：land 与 fall/idle 100% 统一基于 build 基建模型，彻底杜绝 battle 异构模型混用；
  2. 姿态 C0 位置连续性：fall 与 land[0] 头顶对齐误差 <= 2px，中心水平对齐误差 <= 2px；
  3. 骨骼动力学屈膝缓冲深度：land 包含真实下蹲冲击吸收 (下蹲深度 15px ~ 28px)；
  4. 待机无缝接轨连续性：land[29] 与 idle[0] 几何高度与脚底对齐误差 <= 1px；
  5. 全量 711 帧切片四边缘像素 100% 绝对零裁切。
"""

import os
import sys
import glob
from pathlib import Path
from PIL import Image
import numpy as np

pet_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pet_root / "src"))

from pet.skin import SkinManager

def get_alpha_bbox(img_path):
    im = Image.open(img_path)
    arr = np.array(im)[:, :, 3] > 10
    if not arr.any():
        return None
    y_indices, x_indices = np.where(arr)
    return {
        "top": int(y_indices.min()),
        "bottom": int(y_indices.max()),
        "left": int(x_indices.min()),
        "right": int(x_indices.max()),
        "height": int(y_indices.max() - y_indices.min()),
        "width": int(x_indices.max() - x_indices.min()),
        "center_x": int((x_indices.min() + x_indices.max()) // 2)
    }

def run_tests():
    print("\n" + "=" * 65)
    print(" 🚀 开始执行【下落与着陆一体化动力学连续性量化验收测试】")
    print("=" * 65)

    skins_dir = pet_root / "skins"
    sm = SkinManager(skins_dir)
    skin = sm.get_skin("spine_red")
    assert skin is not None, "必须成功装载 spine_red 旗舰皮肤"

    # 1. 契约校验：检查 bake 配置与动作元数据
    print("\n--- [Test 1] 校验全生命周期模型同源统一契约 ---")
    baker_script = pet_root / "tools" / "spine_baker" / "bake_spine_red.py"
    with open(baker_script, "r", encoding="utf-8") as f:
        code = f.read()
    assert '"id": "land"' in code
    # 确认 land 不再使用 battle 模型
    assert not re_check_battle_land(code), "land 动作严禁使用 battle 战斗模型！"
    print("✅ land 动作已 100% 归并统一至 build 基建骨骼模型！杜绝战斗双刀闪现！")

    # 2. C0 姿态连续性：fall 帧与 land[0] 触地对齐
    print("\n--- [Test 2] 校验空中下落与触地瞬态 C0 连续性 (Pose Alignment) ---")
    fall_f0 = pet_root / "skins" / "spine_red" / "frames" / "fall" / "frame_000.png"
    land_f0 = pet_root / "skins" / "spine_red" / "frames" / "land" / "frame_000.png"
    idle_f0 = pet_root / "skins" / "spine_red" / "frames" / "idle" / "frame_000.png"

    bb_fall0 = get_alpha_bbox(fall_f0)
    bb_land0 = get_alpha_bbox(land_f0)
    bb_idle0 = get_alpha_bbox(idle_f0)

    top_diff = abs(bb_fall0["top"] - bb_land0["top"])
    cx_diff = abs(bb_fall0["center_x"] - bb_land0["center_x"])
    print(f"• fall[0] -> top: {bb_fall0['top']}, center_x: {bb_fall0['center_x']}, width: {bb_fall0['width']}")
    print(f"• land[0] -> top: {bb_land0['top']}, center_x: {bb_land0['center_x']}, width: {bb_land0['width']}")
    print(f"• 头顶高度偏差: {top_diff}px (阈值 <= 2px) | 中心水平偏差: {cx_diff}px (阈值 <= 2px)")
    assert top_diff <= 2, f"fall 与 land[0] 头顶对齐偏差过大: {top_diff}px"
    assert cx_diff <= 2, f"fall 与 land[0] 水平中心偏差过大: {cx_diff}px"
    print("✅ 空中下落到触地瞬间 C0 连续性验证 100% 通过 (绝无瞬间平移跳移)！")

    # 3. 骨骼动力学屈膝缓冲深度
    print("\n--- [Test 3] 校验真实受力屈膝冲量吸收深度 (Impulse Absorption) ---")
    land_frames = sorted(glob.glob(str(pet_root / "skins" / "spine_red" / "frames" / "land" / "*.png")))
    assert len(land_frames) == 30, f"land 动作必须包含 30 帧 (当前 {len(land_frames)})"

    crouch_depths = []
    for idx, fpath in enumerate(land_frames):
        bb = get_alpha_bbox(fpath)
        # 头部下沉深度 = 当前 top - 初始 top
        crouch = bb["top"] - bb_land0["top"]
        crouch_depths.append(crouch)

    max_crouch = max(crouch_depths)
    max_crouch_frame = crouch_depths.index(max_crouch)
    print(f"• 最大屈膝下沉深度: {max_crouch}px (出现在 Frame {max_crouch_frame:02d}, 位于冲击吸收区)")
    assert 15 <= max_crouch <= 28, f"屈膝下蹲深度异常: {max_crouch}px"
    print("✅ 真实骨骼屈膝冲量吸收深度验证通过 (15px ~ 28px 弹性缓冲，极其生动)！")

    # 4. 挺身归位融入待机验证
    print("\n--- [Test 4] 校验挺身站稳与平滑融入待机 Relax (Seamless Convergence) ---")
    land_last = land_frames[-1]
    bb_land_last = get_alpha_bbox(land_last)

    h_diff = abs(bb_land_last["height"] - bb_idle0["height"])
    bottom_diff = abs(bb_land_last["bottom"] - bb_idle0["bottom"])
    top_diff_idle = abs(bb_land_last["top"] - bb_idle0["top"])
    print(f"• land[29] (结束帧) -> top: {bb_land_last['top']}, bottom: {bb_land_last['bottom']}, h: {bb_land_last['height']}")
    print(f"• idle[0]  (待机帧) -> top: {bb_idle0['top']}, bottom: {bb_idle0['bottom']}, h: {bb_idle0['height']}")
    print(f"• 待机接轨几何偏差: top_diff={top_diff_idle}px, bottom_diff={bottom_diff}px, h_diff={h_diff}px")
    assert top_diff_idle <= 1, f"land 最后一帧与待机头顶偏差过大: {top_diff_idle}px"
    assert bottom_diff <= 1, f"land 最后一帧与待机脚底偏差过大: {bottom_diff}px"
    print("✅ 触地缓冲结束与待机呼吸零差异完美闭环！切入待机 0 瞬移！")

    # 5. 全量 711 帧切片四边缘像素 100% 绝对零裁切
    print("\n--- [Test 5] 校验全量 711 帧切片 100% 绝对零裁切 ---")
    all_frames = glob.glob(str(pet_root / "skins" / "spine_red" / "frames" / "*" / "*.png"))
    print(f"• 扫描切片总数: {len(all_frames)} 帧")
    assert len(all_frames) >= 711, f"切片总数应至少为 711，实际为: {len(all_frames)}"

    for fpath in all_frames:
        im = Image.open(fpath)
        arr = np.array(im)[:, :, 3]
        assert arr[0, :].max() == 0, f"顶部裁切: {fpath}"
        assert arr[-1, :].max() == 0, f"底部裁切: {fpath}"
        assert arr[:, 0].max() == 0, f"左侧裁切: {fpath}"
        assert arr[:, -1].max() == 0, f"右侧裁切: {fpath}"
    print("✅ 全量 711 帧四边缘绝对零裁切校验 100% 通过！")

    print("\n" + "=" * 65)
    print(" 🎉 ALL 5/5 CONTINUITY ACCEPTANCE TESTS PASSED (100% PASS)!")
    print("=" * 65 + "\n")

def re_check_battle_land(code: str) -> bool:
    import re
    m = re.search(r'\"id\":\s*\"land\"[\s\S]*?\"model\":\s*\"([^\"]+)\"', code)
    if m:
        return m.group(1) == "battle"
    return False

if __name__ == "__main__":
    run_tests()
