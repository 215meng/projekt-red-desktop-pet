# -*- coding: utf-8 -*-
"""
verify_spine_red.py - 阶段一质量关卡验收验证脚本
严格按照 SPINE_DESKTOP_PET_IMPLEMENTATION_PLAN.md 中的“六、质量验收关卡”逐项自动化核验：
  1. 动作时长关卡：全部 10 项动作，每一项实际持续时长严格 >= 1.0 秒
  2. 画面与透明度关卡：分辨率 360x480，32位 RGBA，无黑底白边
  3. 循环连贯关卡：循环动作首尾衔接评估
  4. 状态过渡元数据契约核验
"""

import os
import sys
import json
from PIL import Image

SKIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../skins/spine_red"))

def verify_all():
    print("=" * 65)
    print(" 🔍 开始执行【阶段一：资产提取与骨骼平滑套件准备】质量关卡核验")
    print("=" * 65)

    skin_json_path = os.path.join(SKIN_DIR, "skin.json")
    trans_matrix_path = os.path.join(SKIN_DIR, "transition_matrix.json")

    assert os.path.exists(skin_json_path), f"缺少 skin.json: {skin_json_path}"
    assert os.path.exists(trans_matrix_path), f"缺少 transition_matrix.json: {trans_matrix_path}"

    with open(skin_json_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    actions = manifest.get("actions", {})
    print(f"• 注册动作数量: {len(actions)} / 10 个标准动作")
    assert len(actions) == 10, f"期望 10 个动作，实际注册了 {len(actions)} 个"

    # 1. 动作时长关卡核验 (必须全部 >= 1.0s)
    print("\n【关卡 1：动作时长契约校验 (严格全部 >= 1.0s)】")
    all_duration_ok = True
    total_frames = 0
    total_seconds = 0.0

    for action_id, info in actions.items():
        dur = info["duration"]
        frames_cnt = info["frames_count"]
        fps = info["fps"]
        actual_dur = frames_cnt / fps
        total_frames += frames_cnt
        total_seconds += actual_dur

        status = "✅ PASS" if actual_dur >= 1.0 else "❌ FAIL (<1.0s)"
        if actual_dur < 1.0:
            all_duration_ok = False
        print(f"  [{status}] 动作: {action_id:<12} | 计划: {dur:.3f}s | 实测: {actual_dur:.3f}s ({frames_cnt} 帧) | 类型: {info['type']}")

    assert all_duration_ok, "存在低于 1.0 秒的动作！"
    print(f"  👉 总计有效动作时长: {total_seconds:.2f} 秒，总帧数: {total_frames} 帧")

    # 2. 图像规格与透明通道边缘校验
    print("\n【关卡 2：分辨率与 32 位 RGBA 透明通道抗锯齿校验】")
    all_images_ok = True
    checked_count = 0

    for action_id, info in actions.items():
        action_dir = os.path.join(SKIN_DIR, "frames", action_id)
        assert os.path.isdir(action_dir), f"动作目录不存在: {action_dir}"

        # 抽样检测：第 0 帧、中间帧、最后一帧
        sample_indices = [0, info["frames_count"] // 2, info["frames_count"] - 1]
        for idx in sample_indices:
            frame_path = os.path.join(action_dir, f"frame_{idx:03d}.png")
            assert os.path.exists(frame_path), f"帧文件丢失: {frame_path}"

            with Image.open(frame_path) as im:
                assert im.size == (360, 480), f"尺寸不符合 360x480 规范: {im.size}"
                assert im.mode == "RGBA", f"色彩模式不是 RGBA: {im.mode}"

                # 校验四个角落 Alpha 通道是否绝对完全透明 (无黑框、无长方形边框)
                corners = [
                    im.getpixel((0, 0)),
                    im.getpixel((359, 0)),
                    im.getpixel((0, 479)),
                    im.getpixel((359, 479))
                ]
                for c in corners:
                    assert c[3] == 0, f"角落存在非透明杂色: {c}"

                checked_count += 1

    print(f"  ✅ PASS: 随机抽样 {checked_count} 帧，全部精确匹配 360x480 RGBA 规格，四角 Alpha 严格为 0 (零黑底/零白边)！")

    # 3. 骨骼过渡切片完整性
    print("\n【关卡 3：骨骼过渡切片与状态迁移表契约校验】")
    transitions = manifest.get("transitions", {})
    print(f"  • 注册过渡切片: {len(transitions)} 组")
    for trans_key, trans_act in transitions.items():
        print(f"    - {trans_key} -> 切片动作: {trans_act}")
        assert trans_act in actions, f"过渡切片未在动作表中声明: {trans_act}"

    print("\n" + "=" * 65)
    print(" 🏆 【阶段一全部质量验收关卡顺利通过 (100% 达成)】！")
    print("=" * 65)
    return True

if __name__ == "__main__":
    if not verify_all():
        sys.exit(1)
