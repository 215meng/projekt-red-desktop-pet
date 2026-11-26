"""
Build Autumn Rain Skin (红崽·秋雨落叶 v2.2) from user-generated AIGC action pack.
Handles intelligent alpha extraction, edge anti-aliasing, anchor alignment,
4-frame walk cycle assembly, natural blink integration, and companion poses (sit & sleep).
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import label


def extract_smooth_cutout(img: Image.Image, threshold: int = 242) -> Image.Image:
    """
    Extracts transparent cutout from white background with soft anti-aliased edges.
    Preserves fine wolf hair tips, coat fur collar, and yellow umbrella outlines.
    """
    rgb = img.convert("RGB")
    arr = np.array(rgb, dtype=np.uint8)
    h, w, _ = arr.shape

    # Identify white background connected to borders
    is_white = np.all(arr >= threshold, axis=2)
    labeled, num_features = label(is_white)

    border_labels = (
        set(labeled[0, :])
        .union(labeled[h - 1, :])
        .union(labeled[:, 0])
        .union(labeled[:, w - 1])
        - {0}
    )
    is_bg = np.isin(labeled, list(border_labels))

    # Binary mask: 255 for foreground, 0 for background
    fg_mask = np.where(is_bg, 0, 255).astype(np.uint8)

    # Soften mask boundary slightly for anti-aliasing (prevents white pixel halos)
    mask_img = Image.fromarray(fg_mask, mode="L")
    mask_blurred = mask_img.filter(ImageFilter.GaussianBlur(radius=0.7))

    rgba = np.dstack([arr, np.array(mask_blurred)])
    cutout = Image.fromarray(rgba, "RGBA")

    bbox = cutout.getbbox()
    return cutout.crop(bbox) if bbox else cutout


def extract_smooth_cutout_full(img: Image.Image, threshold: int = 242) -> Image.Image:
    """Extracts cutout preserving original image coordinate system (1920x1920)."""
    rgb = img.convert("RGB")
    arr = np.array(rgb, dtype=np.uint8)
    h, w, _ = arr.shape

    is_white = np.all(arr >= threshold, axis=2)
    labeled, _ = label(is_white)

    border_labels = (
        set(labeled[0, :])
        .union(labeled[h - 1, :])
        .union(labeled[:, 0])
        .union(labeled[:, w - 1])
        - {0}
    )
    is_bg = np.isin(labeled, list(border_labels))
    fg_mask = np.where(is_bg, 0, 255).astype(np.uint8)

    mask_img = Image.fromarray(fg_mask, mode="L")
    mask_blurred = mask_img.filter(ImageFilter.GaussianBlur(radius=0.7))

    rgba = np.dstack([arr, np.array(mask_blurred)])
    return Image.fromarray(rgba, "RGBA")


def paste_on_canvas(canvas: Image.Image, sprite: Image.Image, dx: int = 0, dy: int = 0, angle: float = 0.0) -> Image.Image:
    """Pastes sprite onto canvas with optional offsets and rotation."""
    out = canvas.copy()
    w_c, h_c = canvas.size

    transformed = sprite
    if angle != 0.0:
        transformed = transformed.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)

    w_s, h_s = transformed.size
    left = (w_c - w_s) // 2 + dx
    top = dy

    out.alpha_composite(transformed, (left, top))
    return out


def build_autumn_skin(raw_assets_dir: Path, output_skin_dir: Optional[Path] = None):
    pet_root = Path(__file__).resolve().parent.parent
    if output_skin_dir is None:
        output_skin_dir = pet_root / "skins" / "autumn_red"

    actions_dir = output_skin_dir / "actions"
    actions_dir.mkdir(parents=True, exist_ok=True)

    # 2x Retina Resolution Canvas: (440, 480)
    CANVAS_W = 440
    CANVAS_H = 480
    GROUND_Y = 460  # Ground baseline where character's boots rest
    TARGET_H = 410  # Standard standing height

    canvas_template = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    print(f"Loading raw assets from {raw_assets_dir}...")
    
    # Stand base for scale and anchor calculation
    img_stand = Image.open(raw_assets_dir / "idle_stand.png")
    cut_stand = extract_smooth_cutout(img_stand)
    scale = TARGET_H / cut_stand.height
    print(f"Computed uniform scaling factor: {scale:.4f} (Base height: {cut_stand.height}px -> {TARGET_H}px)")

    def scale_sprite(spr: Image.Image) -> Image.Image:
        w = max(1, int(spr.width * scale))
        h = max(1, int(spr.height * scale))
        return spr.resize((w, h), Image.Resampling.LANCZOS)

    # Common anchor in 1920x1920 for rock-solid idle alignment
    ANCHOR_X = 980
    ANCHOR_Y = 1770
    CANVAS_ANCHOR_X = 220
    CANVAS_ANCHOR_Y = 460

    def place_anchored(img_path: Path) -> Image.Image:
        img = Image.open(img_path)
        cut_full = extract_smooth_cutout_full(img)
        scaled_w = int(img.width * scale)
        scaled_h = int(img.height * scale)
        scaled = cut_full.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
        dest_x = int(CANVAS_ANCHOR_X - ANCHOR_X * scale)
        dest_y = int(CANVAS_ANCHOR_Y - ANCHOR_Y * scale)
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        c.alpha_composite(scaled, (dest_x, dest_y))
        return c

    # ---------------- 1. IDLE (12 frames @ 8 FPS: natural breathing, tail sway & cute blink) ----------------
    print("\n[1/7] Building IDLE action...")
    act_idle_dir = actions_dir / "idle"
    act_idle_dir.mkdir(parents=True, exist_ok=True)

    frame_stand = place_anchored(raw_assets_dir / "idle_stand.png")
    frame_sway = place_anchored(raw_assets_dir / "idle_sway.png")
    frame_blink = place_anchored(raw_assets_dir / "idle_blink.png")

    # Frame arrangement: 4 stand -> 3 sway -> 3 stand -> 1 blink -> 1 stand
    idle_frames = [
        frame_stand, frame_stand, frame_stand, frame_stand,
        frame_sway, frame_sway, frame_sway,
        frame_stand, frame_stand, frame_stand,
        frame_blink,
        frame_stand
    ]
    for i, frame in enumerate(idle_frames):
        frame.save(act_idle_dir / f"idle_{i:02d}.png")
    print(f"Created idle action ({len(idle_frames)} frames @ 8 FPS, seamless blink and sway).")

    # ---------------- 2. WALK (4 frames @ 8 FPS: 4-step walk cycle) ----------------
    print("\n[2/7] Building WALK action...")
    act_walk_dir = actions_dir / "walk"
    act_walk_dir.mkdir(parents=True, exist_ok=True)

    walk_sources = [
        raw_assets_dir / "walk_01.png",
        raw_assets_dir / "walk_pass_01.png",
        raw_assets_dir / "walk_02.png",
        raw_assets_dir / "walk_pass_02.png",
    ]

    for i, p in enumerate(walk_sources):
        cut = extract_smooth_cutout(Image.open(p))
        spr = scale_sprite(cut)
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        left = (CANVAS_W - spr.width) // 2
        top = GROUND_Y - spr.height
        c.alpha_composite(spr, (left, top))
        c.save(act_walk_dir / f"walk_{i:02d}.png")
    print("Created walk action (4-step classic stride cycle: Contact L -> Pass R -> Contact R -> Pass L).")

    # ---------------- 3. DRAG (4 frames @ 6 FPS: dangling with physics sway) ----------------
    print("\n[3/7] Building DRAG action...")
    act_drag_dir = actions_dir / "drag"
    act_drag_dir.mkdir(parents=True, exist_ok=True)

    drag_src = raw_assets_dir / "drag_new.png"
    if not drag_src.exists():
        drag_src = raw_assets_dir / "drag.png"
    cut_drag = scale_sprite(extract_smooth_cutout(Image.open(drag_src)))
    drag_top = 15
    drag_sways = [
        (0.0, 0),
        (-2.5, -2),
        (0.0, 0),
        (2.5, 2),
    ]
    for i, (ang, dx) in enumerate(drag_sways):
        frame = paste_on_canvas(canvas_template, cut_drag, dx=dx, dy=drag_top, angle=ang)
        frame.save(act_drag_dir / f"drag_{i:02d}.png")
    print("Created drag action (4 frames with pendulum damping).")

    # ---------------- 4. FALL (4 frames @ 8 FPS: parachute descent flutter) ----------------
    print("\n[4/7] Building FALL action...")
    act_fall_dir = actions_dir / "fall"
    act_fall_dir.mkdir(parents=True, exist_ok=True)

    fall_src = raw_assets_dir / "fall.png"
    cut_fall = scale_sprite(extract_smooth_cutout(Image.open(fall_src)))
    fall_top = 30
    fall_sways = [
        (0.0, 0),
        (-1.5, -2),
        (0.0, -1),
        (1.5, 2),
    ]
    for i, (ang, dy) in enumerate(fall_sways):
        frame = paste_on_canvas(canvas_template, cut_fall, dy=fall_top + dy, angle=ang)
        frame.save(act_fall_dir / f"fall_{i:02d}.png")
    print("Created fall action (4 frames parachute float).")

    # ---------------- 5. CLICK (4 frames @ 6 FPS: joyful leaf catch hop & blush) ----------------
    print("\n[5/7] Building CLICK action...")
    act_click_dir = actions_dir / "click"
    act_click_dir.mkdir(parents=True, exist_ok=True)

    headpat_src = raw_assets_dir / "headpat.png"
    click_src = raw_assets_dir / "click_new.png"
    if not click_src.exists():
        click_src = raw_assets_dir / "click.png"

    cut_headpat = scale_sprite(extract_smooth_cutout(Image.open(headpat_src)))
    cut_click = scale_sprite(extract_smooth_cutout(Image.open(click_src)))

    click_frames_def = [
        (cut_headpat, GROUND_Y - cut_headpat.height, 0),    # 0: blush ground
        (cut_click, GROUND_Y - cut_click.height, -10),      # 1: hop up
        (cut_click, GROUND_Y - cut_click.height, -16),      # 2: apex reach
        (cut_headpat, GROUND_Y - cut_headpat.height, -4),   # 3: landing smile
    ]
    for i, (spr, base_top, dy) in enumerate(click_frames_def):
        frame = paste_on_canvas(canvas_template, spr, dy=base_top + dy)
        frame.save(act_click_dir / f"click_{i:02d}.png")
    print("Created click action (4 frames: headpat blush -> leaf hop -> happy landing).")

    # ---------------- 6. SIT (4 frames @ 4 FPS: cozy floor sitting companion) ----------------
    print("\n[6/7] Building SIT action...")
    act_sit_dir = actions_dir / "sit"
    act_sit_dir.mkdir(parents=True, exist_ok=True)

    cut_sit = scale_sprite(extract_smooth_cutout(Image.open(raw_assets_dir / "sit.png")))
    sit_base_top = GROUND_Y - cut_sit.height
    sit_bobs = [0, -1, -2, -1]
    for i, dy in enumerate(sit_bobs):
        frame = paste_on_canvas(canvas_template, cut_sit, dy=sit_base_top + dy)
        frame.save(act_sit_dir / f"sit_{i:02d}.png")
    print("Created sit action (4 frames gentle breathing).")

    # ---------------- 7. SLEEP (4 frames @ 3 FPS: curled up nap hugging tail) ----------------
    print("\n[7/7] Building SLEEP action...")
    act_sleep_dir = actions_dir / "sleep"
    act_sleep_dir.mkdir(parents=True, exist_ok=True)

    cut_sleep = scale_sprite(extract_smooth_cutout(Image.open(raw_assets_dir / "sleep.png")))
    sleep_base_top = GROUND_Y - cut_sleep.height
    sleep_bobs = [0, -1, -1, 0]
    for i, dy in enumerate(sleep_bobs):
        frame = paste_on_canvas(canvas_template, cut_sleep, dy=sleep_base_top + dy)
        frame.save(act_sleep_dir / f"sleep_{i:02d}.png")
    print("Created sleep action (4 frames peaceful nap).")

    # ---------------- 8. METADATA skin.json ----------------
    print("\nUpdating skin.json metadata...")
    meta = {
        "id": "autumn_red",
        "name": "红崽·秋雨落叶 (小红帽 v2.2)",
        "author": "User & Antigravity",
        "version": "2.2",
        "description": "第二版全新动态皮肤：撑黄色雨伞、活体大尾巴自然晃动、四帧经典步态巡逻的红崽小天使。",
        "base_size": [220, 240],
        "default_scale": 1.0,
        "actions": {
            "idle": {"fps": 8, "loop": True},
            "walk": {"fps": 8, "speed": 3, "loop": True},
            "drag": {"fps": 6, "loop": True},
            "fall": {"fps": 8, "loop": True},
            "click": {"fps": 6, "loop": False, "next": "idle"},
            "sit": {"fps": 4, "loop": True},
            "sleep": {"fps": 3, "loop": True}
        },
        "dialogues": [
            "大衣很暖和，尾巴也是...",
            "下雨了吗？红给你撑伞。",
            "落叶飘下来了...红抓到了！",
            "这把黄色的小伞，是博士送给红的吗？",
            "踩水洼...啪嗒啪嗒。",
            "呼呼...闻到了秋天的气味。",
            "红坐在这里，静静陪着你。",
            "尾巴软软的...呼噜呼噜...Zzz...",
            "红一直看着你呢。"
        ]
    }

    with open(output_skin_dir / "skin.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Skin 'autumn_red' successfully rebuilt at {output_skin_dir}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process autumn skin AIGC assets")
    parser.add_argument(
        "--input-dir",
        default=str(Path(__file__).resolve().parent.parent / "raw_assets" / "autumn_red"),
        help="Folder containing raw action images"
    )
    args = parser.parse_args()
    build_autumn_skin(Path(args.input_dir))
