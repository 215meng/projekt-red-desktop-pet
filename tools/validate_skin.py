# -*- coding: utf-8 -*-
"""
validate_skin.py - 桌宠通用皮肤质量检验门禁工具 (Skin Spec v4.6)

支持校验任意皮肤包的：
  1. skin.json 元数据结构、fps 合法性 (6~60) 与 native_facing 契约
  2. Tier-1 / Tier-2 / Tier-3 动作覆盖度分析
  3. 全帧分辨率一致性与四边界零裁切
  4. 接地线一致性 (以 ground_line_y 或 idle[0] 底边为基准)
  5. 竖直姿态主体零水平透明断裂（防止头身分离）

用法：
  python tools/validate_skin.py <skin_id_or_path>
  python tools/validate_skin.py --all
"""

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKINS_ROOT = PROJECT_ROOT / "skins"

TIER_1_ACTIONS = ("idle", "walk", "drag", "fall", "land", "headpat")
TIER_2_ACTIONS = ("sit", "sleep", "trans_sit", "trans_sleep")
TIER_3_ACTIONS = (
    "cuddle_tail",
    "sharpen_knife",
    "alert_scout",
    "yawn_stretch",
    "edge_peek",
    "doze_off",
    "dizzy",
)

UPRIGHT_ACTIONS = {
    "idle", "walk", "drag", "sit", "headpat", "dizzy", "trans_sit",
    "fall", "land", "cuddle_tail", "sharpen_knife", "alert_scout",
    "yawn_stretch", "edge_peek", "doze_off",
}


def _collect_frame_files(skin_dir: Path, action_name: str) -> List[Path]:
    for folder in ("frames", "actions"):
        act_dir = skin_dir / folder / action_name
        if act_dir.is_dir():
            files = []
            for ext in ("*.png", "*.webp", "*.jpg"):
                files.extend(Path(p) for p in glob.glob(str(act_dir / ext)))
            return sorted(files)
    return []


def validate_skin_dir(skin_dir: Path) -> Tuple[bool, List[str], List[str]]:
    """
    校验单个皮肤目录。
    返回: (passed, errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not skin_dir.is_dir():
        return False, [f"皮肤目录不存在: {skin_dir}"], warnings

    manifest_path = skin_dir / "skin.json"
    if not manifest_path.exists():
        return False, [f"缺少必需元数据文件: {manifest_path}"], warnings

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            meta: Dict = json.load(f)
    except Exception as exc:
        return False, [f"skin.json 解析失败: {exc}"], warnings

    expected_w = int(meta.get("width", 360))
    expected_h = int(meta.get("height", 480))
    fps = int(meta.get("fps", 30))
    if not (6 <= fps <= 60):
        errors.append(f"全局 fps 超出有效区间 [6, 60]: {fps}")

    native_facing = str(meta.get("native_facing", "right")).lower()
    if native_facing not in ("right", "left"):
        errors.append(f"native_facing 仅支持 'right' 或 'left'，当前为: {native_facing!r}")

    actions_cfg: Dict = meta.get("actions", {})
    if not isinstance(actions_cfg, dict) or not actions_cfg:
        errors.append("skin.json 缺少有效的 actions 配置")
        return False, errors, warnings

    if "idle" not in actions_cfg:
        errors.append("Tier-1 核心必选动作 'idle' 缺失")

    # 检查 Tier 完备度
    missing_t1 = [a for a in TIER_1_ACTIONS if a not in actions_cfg]
    missing_t2 = [a for a in TIER_2_ACTIONS if a not in actions_cfg]
    missing_t3 = [a for a in TIER_3_ACTIONS if a not in actions_cfg]
    if missing_t1:
        warnings.append(f"Tier-1 缺少动作（将自动回退）: {', '.join(missing_t1)}")
    if missing_t2:
        warnings.append(f"Tier-2 未包含陪伴动作: {', '.join(missing_t2)}")
    if missing_t3:
        warnings.append(f"Tier-3 未包含进阶动作: {', '.join(missing_t3)}")

    # 获取基准接地底边 Y
    ground_base: Optional[int] = meta.get("ground_line_y", None)
    if ground_base is not None:
        ground_base = int(ground_base)
    else:
        idle_files = _collect_frame_files(skin_dir, "idle")
        if idle_files:
            with Image.open(idle_files[0]) as im0:
                b0 = im0.convert("RGBA").getbbox()
                if b0:
                    ground_base = b0[3]

    total_frames = 0
    for act_name, act_meta in actions_cfg.items():
        act_fps = int(act_meta.get("fps", fps))
        if not (6 <= act_fps <= 60):
            errors.append(f"动作 '{act_name}' fps={act_fps} 超出 [6, 60]")

        files = _collect_frame_files(skin_dir, act_name)
        if not files:
            errors.append(f"动作 '{act_name}' 在 frames/ 或 actions/ 下未找到任何帧图片")
            continue

        declared_count = act_meta.get("frames_count")
        if declared_count is not None and int(declared_count) != len(files):
            errors.append(
                f"动作 '{act_name}' 声明 frames_count={declared_count} 与实际帧数 {len(files)} 不一致"
            )

        bottoms: List[int] = []
        for fp in files:
            total_frames += 1
            try:
                with Image.open(fp) as im:
                    rgba = im.convert("RGBA")
                    w, h = rgba.size
                    if (w, h) != (expected_w, expected_h):
                        errors.append(
                            f"帧尺寸不匹配 {fp.name}: 期望 {(expected_w, expected_h)}, 实际 {(w, h)}"
                        )
                        continue
                    alpha = rgba.getchannel("A")
                    bbox = alpha.getbbox()
                    if bbox is None:
                        errors.append(f"发现全透明空帧: {act_name}/{fp.name}")
                        continue
                    l, t, r, b = bbox
                    if l <= 0 or t <= 0 or r >= w or b >= h:
                        errors.append(
                            f"边缘裁切 {act_name}/{fp.name}: bbox={bbox}, 画布={(w, h)}"
                        )
                    bottoms.append(b)

                    # 竖直动作防头身分离检查
                    if act_name in UPRIGHT_ACTIONS:
                        span = b - t
                        if span >= 20:
                            scan_top = int(t + span * 0.25)
                            scan_bot = int(t + span * 0.70)
                            raw = alpha.tobytes()
                            for y in range(scan_top, scan_bot + 1):
                                if max(raw[y * w : (y + 1) * w]) < 20:
                                    errors.append(
                                        f"检测到水平透明断裂带（疑似头身分离）: {act_name}/{fp.name} y={y}"
                                    )
                                    break
            except Exception as exc:
                errors.append(f"无法读取帧 {act_name}/{fp.name}: {exc}")

        # 接地线稳定性校验
        if ground_base is not None and bottoms and act_name not in ("drag", "fall"):
            if act_name == "land":
                if abs(bottoms[-1] - ground_base) > 5:
                    errors.append(
                        f"land 末帧未对齐接地基准线 {ground_base}px: 实际 {bottoms[-1]}px"
                    )
                if min(bottoms) < ground_base - 8 or max(bottoms) > ground_base + 22:
                    errors.append(
                        f"land 接地范围异常 [{min(bottoms)}, {max(bottoms)}] (基准 {ground_base}px)"
                    )
            elif act_name == "trans_sleep":
                if abs(bottoms[0] - ground_base) > 4 or abs(bottoms[-1] - ground_base) > 4:
                    errors.append(
                        f"trans_sleep 首尾偏离接地基准 {ground_base}px: 首={bottoms[0]}, 末={bottoms[-1]}"
                    )
            else:
                if min(bottoms) < ground_base - 8 or max(bottoms) > ground_base + 8:
                    errors.append(
                        f"动作 '{act_name}' 接地底边漂移过大 [{min(bottoms)}, {max(bottoms)}] (基准 {ground_base}px)"
                    )

    print(f"=== 皮肤质检报告: {skin_dir.name} ===")
    print(
        f"  标题: {meta.get('title', skin_dir.name)} | 类型: {meta.get('source_type', 'spine')} | "
        f"朝向: {native_facing} | FPS: {fps} | 动作数: {len(actions_cfg)} | 总帧数: {total_frames}"
    )
    if ground_base is not None:
        print(f"  接地基准 Y: {ground_base}px")
    for w in warnings:
        print(f"  [WARN] {w}")
    for e in errors:
        print(f"  [FAIL] {e}")
    if not errors:
        print(f"  [PASS] {skin_dir.name} 全部质检门禁通过！")
    return len(errors) == 0, errors, warnings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate desktop pet skin packs (Skin Spec v4.6)")
    parser.add_argument("target", nargs="?", default="spine_red", help="皮肤 ID（位于 skins/ 下）或皮肤目录路径")
    parser.add_argument("--all", action="store_true", help="校验 skins/ 目录下全部皮肤")
    args = parser.parse_args(argv)

    targets: List[Path] = []
    if args.all:
        if DEFAULT_SKINS_ROOT.is_dir():
            targets = [p for p in sorted(DEFAULT_SKINS_ROOT.iterdir()) if p.is_dir() and (p / "skin.json").exists()]
    else:
        p = Path(args.target)
        targets = [p if p.is_dir() else (DEFAULT_SKINS_ROOT / args.target)]

    if not targets:
        print("[FAIL] 未找到可校验的皮肤目录")
        return 1

    all_ok = True
    for t in targets:
        ok, _, _ = validate_skin_dir(t)
        if not ok:
            all_ok = False
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
