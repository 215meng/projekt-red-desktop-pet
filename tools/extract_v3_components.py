"""
Extract 3.0 Character Components from Master Sprite Sheets.
Uses smart connected component analysis, anti-aliased edge smoothing,
and precise bounding box registration.
"""

import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import label, find_objects


def extract_smooth_cutout(img_crop: Image.Image, threshold: int = 242) -> Image.Image:
    """Extract transparent cutout with smoothed anti-aliased alpha boundary."""
    rgb = img_crop.convert("RGB")
    arr = np.array(rgb)
    h, w = arr.shape[:2]

    # Detect white background
    is_white = np.all(arr >= threshold, axis=2)
    labeled, num_features = label(is_white)

    # Border connected labels are background
    border_labels = (
        set(labeled[0, :])
        .union(labeled[h - 1, :])
        .union(labeled[:, 0])
        .union(labeled[:, w - 1])
        - {0}
    )
    is_bg = np.isin(labeled, list(border_labels))
    fg_mask = np.where(is_bg, 0, 255).astype(np.uint8)

    # Anti-alias mask
    mask_img = Image.fromarray(fg_mask, mode="L").filter(ImageFilter.GaussianBlur(radius=0.7))
    rgba = np.dstack([arr, np.array(mask_img)])
    cutout = Image.fromarray(rgba, "RGBA")
    bbox = cutout.getbbox()
    return cutout.crop(bbox) if bbox else cutout


def extract_largest_component(img_crop: Image.Image, threshold: int = 240) -> Image.Image:
    """Isolates the single largest connected foreground component within crop."""
    rgb = img_crop.convert("RGB")
    arr = np.array(rgb)
    is_fg = np.any(arr < threshold, axis=2)
    lbl, num = label(is_fg)
    if num == 0:
        return extract_smooth_cutout(img_crop, threshold)

    sizes = [np.sum(lbl == i) for i in range(1, num + 1)]
    largest_lbl = np.argmax(sizes) + 1
    fg_mask = (lbl == largest_lbl).astype(np.uint8) * 255

    mask_img = Image.fromarray(fg_mask, mode="L").filter(ImageFilter.GaussianBlur(radius=0.7))
    rgba = np.dstack([arr, np.array(mask_img)])
    cutout = Image.fromarray(rgba, "RGBA")
    bbox = cutout.getbbox()
    return cutout.crop(bbox) if bbox else cutout


def run_extraction():
    pet_root = Path(__file__).resolve().parent.parent
    raw_dir = pet_root / "raw_assets" / "v3_sheets"
    out_dir = pet_root / "skins" / "autumn_red" / "parts"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading master sheets from {raw_dir}...")
    s1 = Image.open(raw_dir / "sheet_01_walk.png")
    s2 = Image.open(raw_dir / "sheet_02_idle.png")
    s3 = Image.open(raw_dir / "sheet_03_special.png")

    parts = {}

    # ---------------- 1. Sheet 01: Walk Components ----------------
    print("Extracting Sheet 1: Walk components...")
    parts["walk_body"] = extract_smooth_cutout(s1.crop((65, 3, 267, 263)))
    parts["walk_coat_flutter"] = extract_smooth_cutout(s1.crop((352, 116, 506, 258)))
    parts["walk_tail"] = extract_smooth_cutout(s1.crop((558, 76, 749, 256)))
    parts["walk_umbrella"] = extract_smooth_cutout(s1.crop((797, 92, 964, 266)))

    parts["walk_leg_01"] = extract_smooth_cutout(s1.crop((43, 346, 235, 486)))
    parts["walk_leg_02"] = extract_smooth_cutout(s1.crop((336, 349, 440, 490)))
    parts["walk_leg_03"] = extract_smooth_cutout(s1.crop((534, 351, 733, 488)))
    parts["walk_leg_04"] = extract_smooth_cutout(s1.crop((830, 348, 928, 490)))

    # ---------------- 2. Sheet 02: Idle Components ----------------
    print("Extracting Sheet 2: Idle components...")
    parts["idle_body"] = extract_smooth_cutout(s2.crop((22, 110, 307, 445)))
    head_base = extract_smooth_cutout(s2.crop((305, 20, 553, 256)))
    parts["idle_head"] = head_base
    parts["idle_tail_01"] = extract_smooth_cutout(s2.crop((309, 283, 473, 540)))
    parts["idle_tail_02"] = extract_smooth_cutout(s2.crop((503, 287, 658, 524)))

    parts["ear_right"] = extract_smooth_cutout(s2.crop((583, 23, 650, 131)))
    parts["ear_left"] = extract_smooth_cutout(s2.crop((694, 23, 760, 131)))
    parts["ear_twitch"] = extract_smooth_cutout(s2.crop((810, 53, 892, 140)))

    parts["face_open"] = extract_smooth_cutout(s2.crop((588, 158, 702, 267)))
    parts["face_half"] = extract_smooth_cutout(s2.crop((730, 159, 844, 268)))
    parts["face_closed"] = extract_smooth_cutout(s2.crop((872, 160, 986, 269)))

    parts["idle_legs"] = extract_smooth_cutout(s2.crop((712, 318, 833, 534)))
    parts["idle_umbrella"] = extract_smooth_cutout(s2.crop((863, 283, 962, 545)))

    # Assemble smooth blinking expression heads:
    # Blend eyes & mouth features with sub-pixel alignment (dx=67, dy=84)
    Y, X = np.ogrid[:109, :114]
    eye_l = ((X - 34) ** 2 / 21 ** 2 + (Y - 67) ** 2 / 18 ** 2) <= 1.0
    eye_r = ((X - 82) ** 2 / 21 ** 2 + (Y - 67) ** 2 / 18 ** 2) <= 1.0
    mouth = ((X - 58) ** 2 / 14 ** 2 + (Y - 92) ** 2 / 10 ** 2) <= 1.0
    feature_mask = (eye_l | eye_r | mouth).astype(np.uint8) * 255
    blend_mask = Image.fromarray(feature_mask).filter(ImageFilter.GaussianBlur(radius=2.5))

    head_half = head_base.copy()
    head_half.paste(parts["face_half"], (67, 84), blend_mask)
    parts["head_half"] = head_half

    head_closed = head_base.copy()
    head_closed.paste(parts["face_closed"], (67, 84), blend_mask)
    parts["head_closed"] = head_closed

    # ---------------- 3. Sheet 03: Special Action Components ----------------
    print("Extracting Sheet 3: Special action components...")
    parts["drag_full"] = extract_smooth_cutout(s3.crop((12, 0, 200, 469)))
    parts["drag_character"] = extract_smooth_cutout(s3.crop((12, 65, 200, 469)))
    parts["drag_legs"] = extract_smooth_cutout(s3.crop((240, 175, 382, 314)))

    parts["ear_droop_left"] = extract_smooth_cutout(s3.crop((331, 57, 417, 140)))
    parts["ear_droop_right"] = extract_smooth_cutout(s3.crop((418, 61, 503, 137)))
    parts["head_shocked"] = extract_smooth_cutout(s3.crop((403, 156, 583, 335)))

    parts["umbrella_parachute"] = extract_largest_component(s3.crop((520, 25, 820, 275)))

    # Clean coat updraft without neighbor umbrella tip:
    updraft_crop = s3.crop((750, 69, 1015, 349))
    updraft_arr = np.array(updraft_crop)
    # Mask out yellow umbrella tip on upper left (x < 62, y < 140)
    updraft_arr[:140, :62, :3] = 255
    parts["coat_updraft"] = extract_smooth_cutout(Image.fromarray(updraft_arr))

    parts["body_sit"] = extract_smooth_cutout(s3.crop((229, 382, 424, 529)))
    parts["tail_cushion"] = extract_smooth_cutout(s3.crop((488, 391, 685, 538)))
    parts["head_sleeping"] = extract_smooth_cutout(s3.crop((730, 376, 950, 542)))

    # Save all parts
    print(f"\nSaving {len(parts)} processed components to {out_dir}...")
    for name, img in parts.items():
        save_path = out_dir / f"{name}.png"
        img.save(save_path)
        print(f"  Saved: {name:20s} -> {img.size}px")

    print("\n[SUCCESS] All 3.0 components cleanly extracted and saved!")


if __name__ == "__main__":
    run_extraction()
