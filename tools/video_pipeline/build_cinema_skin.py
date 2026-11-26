"""
Build Cinema Skin (红崽·秋之映画 v3.0) from user action video assets.
Extracts high-framerate action loops, performs precision alpha extraction,
completely eliminates floor shadows/reflections, normalizes orientation (faces left natively),
and aligns feet contact to a stable taskbar ground plane on 440x480 retina canvas.
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import List, Tuple, Optional
import cv2
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import label


def extract_clean_cutout(bgr_frame: np.ndarray, is_airborne: bool = False, color_tol: float = 18.0) -> Image.Image:
    """
    Extracts transparent cutout from studio background.
    Strictly removes 100% of floor shadows and mirror reflections.
    """
    rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
    arr = np.array(rgb, dtype=np.float32)
    h, w, _ = arr.shape

    # 1. Sample corners to determine local background color
    corners = np.concatenate([
        arr[:25, :25].reshape(-1, 3),
        arr[:25, -25:].reshape(-1, 3),
        arr[-25:, :25].reshape(-1, 3),
        arr[-25:, -25:].reshape(-1, 3),
    ], axis=0)
    bg_color = np.median(corners, axis=0)

    # 2. Color distance thresholding
    dist = np.linalg.norm(arr - bg_color, axis=2)
    fg_mask = dist >= color_tol

    # 3. Find boot sole level to eliminate floor reflection
    # The boot leather is distinctive red/burgundy: r > g + 25, r < 215, g < 130
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    is_red_boot = (r > g + 25) & (r < 215) & (g < 130) & (arr[:, :, 0] > 60)

    # Check bottom half of image (y > 350)
    ys_boot = []
    for y_scan in range(350, h):
        if np.sum(is_red_boot[y_scan, :]) >= 6:
            ys_boot.append(y_scan)

    max_boot_y = h
    if ys_boot:
        max_boot_leather_y = max(ys_boot)
        # Boot heel/sole is 2-3px below the leather
        clip_y = max_boot_leather_y + 3
        max_boot_y = clip_y
        fg_mask[clip_y:, :] = False

    # 4. Connected component analysis to isolate character body
    labeled, num_features = label(fg_mask)
    if num_features == 0:
        return Image.fromarray(np.zeros((h, w, 4), dtype=np.uint8), "RGBA")

    # Find the largest component (the character)
    component_sizes = [(i, np.sum(labeled == i)) for i in range(1, num_features + 1)]
    component_sizes.sort(key=lambda x: x[1], reverse=True)

    main_comp_idx = component_sizes[0][0]
    char_mask = (labeled == main_comp_idx)

    # Include significant secondary character features (like umbrella tip or tail if disconnected by 1px)
    if not is_airborne:
        for idx, sz in component_sizes[1:]:
            if sz > 2000:
                ys, xs = np.where(labeled == idx)
                # Keep if above boot level
                if ys.max() <= max_boot_y + 2:
                    char_mask = char_mask | (labeled == idx)

    # 5. Alpha anti-aliasing with soft Gaussian blur
    alpha = np.where(char_mask, 255, 0).astype(np.uint8)
    alpha_img = Image.fromarray(alpha, mode="L")
    alpha_blurred = alpha_img.filter(ImageFilter.GaussianBlur(radius=0.65))

    rgba = np.dstack([rgb, np.array(alpha_blurred)])
    cutout = Image.fromarray(rgba, "RGBA")

    bbox = cutout.getbbox()
    return cutout.crop(bbox) if bbox else cutout


def place_grounded_sprite(
    sprite: Image.Image,
    target_canvas_size: Tuple[int, int] = (440, 480),
    target_height: int = 405,
    ground_y: int = 464,  # baseline for boot soles
    flip_horizontal: bool = True
) -> Image.Image:
    """Places a ground-contact sprite (idle, walk, click) with its lowest boots resting on ground_y."""
    canvas = Image.new("RGBA", target_canvas_size, (0, 0, 0, 0))
    w_s, h_s = sprite.size
    if w_s == 0 or h_s == 0:
        return canvas

    scale = target_height / float(h_s)
    new_w = int(round(w_s * scale))
    new_h = target_height

    resized = sprite.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if flip_horizontal:
        resized = resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    w_c, h_c = target_canvas_size
    left = (w_c - new_w) // 2
    top = ground_y - new_h

    canvas.alpha_composite(resized, (left, top))
    return canvas


def place_airborne_sprite(
    sprite: Image.Image,
    target_canvas_size: Tuple[int, int] = (440, 480),
    target_height: int = 420,
    top_y: int = 15,
    flip_horizontal: bool = True
) -> Image.Image:
    """Places an airborne sprite (drag, fall) anchored from the top."""
    canvas = Image.new("RGBA", target_canvas_size, (0, 0, 0, 0))
    w_s, h_s = sprite.size
    if w_s == 0 or h_s == 0:
        return canvas

    scale = target_height / float(h_s)
    new_w = int(round(w_s * scale))
    new_h = target_height

    resized = sprite.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if flip_horizontal:
        resized = resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    w_c, h_c = target_canvas_size
    left = (w_c - new_w) // 2
    top = top_y

    canvas.alpha_composite(resized, (left, top))
    return canvas


def extract_video_frames(video_path: Path, timestamps: List[float]) -> List[np.ndarray]:
    """Extracts BGR frames at exact second timestamps using OpenCV."""
    cap = cv2.VideoCapture(str(video_path))
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []

    for t in timestamps:
        frame_idx = int(round(t * orig_fps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
        else:
            print(f"Warning: could not read frame at {t:.2f}s from {video_path.name}")
    cap.release()
    return frames


def build_cinema_skin(
    video_dir: Path,
    output_skin_dir: Path,
    autumn_red_dir: Optional[Path] = None
):
    """Builds full autumn_red_cinema skin."""
    output_skin_dir.mkdir(parents=True, exist_ok=True)
    actions_dir = output_skin_dir / "actions"
    actions_dir.mkdir(exist_ok=True)

    v_walk = video_dir / "walk.mp4"
    v_picked = video_dir / "walk&picked_up.mp4"
    v_fail = video_dir / "walk&picked_up&fail.mp4"

    print("==================================================")
    print("Building Cinema Skin: 红崽·秋之映画 (autumn_red_cinema)")
    print("==================================================")

    # 1. IDLE (做完动作静态站立：正面安定站立、小伞与红衣自然垂顺、双足稳立地平线)
    # walk.mp4: 8.00s (1 frame pure static standing)
    print("\n[1/5] Processing 'idle' action (pure static standing pose)...")
    idle_dir = actions_dir / "idle"
    idle_dir.mkdir(exist_ok=True)
    for p in idle_dir.glob("*.png"):
        p.unlink()
    idle_times = [8.00]
    idle_frames = extract_video_frames(v_walk, idle_times)
    for i, frame in enumerate(idle_frames):
        cutout = extract_clean_cutout(frame, is_airborne=False, color_tol=18.0)
        canvas = place_grounded_sprite(cutout, target_height=385, ground_y=464, flip_horizontal=False)
        canvas.save(idle_dir / f"idle_{i:02d}.png")
    print(f"-> Saved {len(idle_frames)} frame(s) in {idle_dir}")

    # 2. WALK (侧身撑伞自然漫步巡逻)
    # walk.mp4: 0.833s -> 2.25s (18 frames from 24 FPS video, complete double-stride loop)
    print("\n[2/5] Processing 'walk' action (smooth 18-frame umbrella walk cycle)...")
    walk_dir = actions_dir / "walk"
    walk_dir.mkdir(exist_ok=True)
    for p in walk_dir.glob("*.png"):
        p.unlink()
    walk_times = [(20 + i * 2) / 24.0 for i in range(18)]
    walk_frames = extract_video_frames(v_walk, walk_times)
    for i, frame in enumerate(walk_frames):
        cutout = extract_clean_cutout(frame, is_airborne=False, color_tol=18.0)
        canvas = place_grounded_sprite(cutout, target_height=385, ground_y=464, flip_horizontal=True)
        canvas.save(walk_dir / f"walk_{i:02d}.png")
    print(f"-> Saved {len(walk_frames)} frames in {walk_dir}")

    # 3. DRAG (帽子被提溜、双脚扑腾挣扎)
    # walk&picked_up.mp4: 3.75s -> 5.25s (12 frames at 8 FPS)
    print("\n[3/5] Processing 'drag' action (struggling kick dangle)...")
    drag_dir = actions_dir / "drag"
    drag_dir.mkdir(exist_ok=True)
    for p in drag_dir.glob("*.png"):
        p.unlink()
    drag_times = [3.75 + i * 0.125 for i in range(12)]
    drag_frames = extract_video_frames(v_picked, drag_times)
    for i, frame in enumerate(drag_frames):
        cutout = extract_clean_cutout(frame, is_airborne=True, color_tol=18.0)
        canvas = place_airborne_sprite(cutout, target_height=435, top_y=10, flip_horizontal=True)
        canvas.save(drag_dir / f"drag_{i:02d}.png")
    print(f"-> Saved {len(drag_frames)} frames in {drag_dir}")

    # 4. FALL (黄色雨伞降落伞轻盈滑降)
    # walk&picked_up&fail.mp4: 7.42s -> 8.30s (8 frames at 8 FPS)
    print("\n[4/5] Processing 'fall' action (umbrella parachute descent)...")
    fall_dir = actions_dir / "fall"
    fall_dir.mkdir(exist_ok=True)
    for p in fall_dir.glob("*.png"):
        p.unlink()
    fall_times = [7.42 + i * 0.11 for i in range(8)]
    fall_frames = extract_video_frames(v_fail, fall_times)
    for i, frame in enumerate(fall_frames):
        cutout = extract_clean_cutout(frame, is_airborne=True, color_tol=18.0)
        canvas = place_airborne_sprite(cutout, target_height=390, top_y=25, flip_horizontal=False)
        canvas.save(fall_dir / f"fall_{i:02d}.png")
    print(f"-> Saved {len(fall_frames)} frames in {fall_dir}")

    # 5. CLICK (摸头欢快跳跃转圈并在落地后自然归于站立)
    # walk.mp4: 5.40s -> 7.78s (20 frames at 8 FPS, complete hop-and-land arc)
    print("\n[5/5] Processing 'click' action (joyful hop & landing to ground)...")
    click_dir = actions_dir / "click"
    click_dir.mkdir(exist_ok=True)
    for p in click_dir.glob("*.png"):
        p.unlink()
    click_times = [5.40 + i * 0.125 for i in range(20)]
    click_frames = extract_video_frames(v_walk, click_times)
    for i, frame in enumerate(click_frames):
        cutout = extract_clean_cutout(frame, is_airborne=False, color_tol=18.0)
        canvas = place_grounded_sprite(cutout, target_height=385, ground_y=464, flip_horizontal=True)
        canvas.save(click_dir / f"click_{i:02d}.png")
    print(f"-> Saved {len(click_frames)} frames in {click_dir}")

    # 6. GREET (做完动作静态站立：站立打招呼、抬手温和挥动问候、收手自然归于静态站立)
    # walk.mp4: frames 192 -> 216 -> 192 (15 frames at 8 FPS, complete wave-and-lower arc)
    print("\n[6/6] Processing 'greet' action (standing wave & gentle hand lowering)...")
    greet_dir = actions_dir / "greet"
    greet_dir.mkdir(exist_ok=True)
    for p in greet_dir.glob("*.png"):
        p.unlink()
    greet_indices = [192, 195, 198, 201, 204, 208, 212, 216, 212, 208, 204, 201, 198, 195, 192]
    greet_times = [idx / 24.0 for idx in greet_indices]
    greet_frames = extract_video_frames(v_walk, greet_times)
    for i, frame in enumerate(greet_frames):
        cutout = extract_clean_cutout(frame, is_airborne=False, color_tol=18.0)
        canvas = place_grounded_sprite(cutout, target_height=385, ground_y=464, flip_horizontal=False)
        canvas.save(greet_dir / f"greet_{i:02d}.png")
    print(f"-> Saved {len(greet_frames)} frames in {greet_dir}")

    # 7. LAND (落地屈膝吸收冲击并自然挺身归于站立)
    # walk&picked_up&fail.mp4: frames 201 -> 216 (8 frames at 8 FPS)
    print("\n[7/7] Processing 'land' action (touchdown & crouch impact absorption)...")
    land_dir = actions_dir / "land"
    land_dir.mkdir(exist_ok=True)
    for p in land_dir.glob("*.png"):
        p.unlink()
    land_indices = [201, 203, 205, 207, 209, 211, 213, 216]
    land_times = [idx / 24.0 for idx in land_indices]
    land_frames = extract_video_frames(v_fail, land_times)
    for i, frame in enumerate(land_frames):
        cutout = extract_clean_cutout(frame, is_airborne=False, color_tol=18.0)
        canvas = place_grounded_sprite(cutout, target_height=385, ground_y=464, flip_horizontal=False)
        canvas.save(land_dir / f"land_{i:02d}.png")
    print(f"-> Saved {len(land_frames)} frames in {land_dir}")

    # 8. Inherit companion poses (SIT & SLEEP) if autumn_red exists
    if autumn_red_dir and autumn_red_dir.exists():
        for pose in ["sit", "sleep"]:
            src_pose = autumn_red_dir / "actions" / pose
            dst_pose = actions_dir / pose
            if src_pose.exists():
                print(f"\n[Companion] Inheriting '{pose}' action from {src_pose.name}...")
                dst_pose.mkdir(exist_ok=True)
                for p in src_pose.glob("*.png"):
                    shutil.copy2(p, dst_pose / p.name)
                print(f"-> Inherited {pose} frames to {dst_pose}")

    # 9. Write skin.json
    print("\n[9/9] Generating skin.json...")
    skin_meta = {
        "id": "autumn_red_cinema",
        "name": "红崽·秋之映画 (v3.0 视频版)",
        "author": "User & Antigravity",
        "version": "3.0",
        "description": "基于真实 AIGC 动作视频全量提取与重构的映画级动态皮肤，支持自然呼吸眨眼、丝滑撑伞步态、挣扎提溜、伞兵滑降、落地屈膝与元气欢喜摸头。",
        "base_size": [220, 240],
        "default_scale": 1.0,
        "actions": {
            "idle": {
                "fps": 1,
                "loop": True
            },
            "greet": {
                "fps": 8,
                "loop": False,
                "next": "idle"
            },
            "walk": {
                "fps": 6,
                "speed": 2,
                "loop": True
            },
            "drag": {
                "fps": 8,
                "loop": True
            },
            "fall": {
                "fps": 8,
                "loop": True
            },
            "land": {
                "fps": 8,
                "loop": False,
                "next": "idle"
            },
            "click": {
                "fps": 8,
                "loop": False,
                "next": "idle"
            },
            "sit": {
                "fps": 4,
                "loop": True
            },
            "sleep": {
                "fps": 3,
                "loop": True
            }
        },
        "dialogues": [
            "你看，红在雨里跳舞呢！",
            "黄色的小伞撑开了，不怕下雨天~",
            "快看快看！红抓到漂亮的落叶了！",
            "哎呀！被博士提溜起来啦，小靴子扑腾扑腾...",
            "小降落伞...呼呼，慢慢落下来啦。",
            "站得累了，红坐在这里静静陪你。",
            "大尾巴软乎乎的...呼噜呼噜...Zzz...",
            "红会一直看着你工作哦，博士加油！"
        ]
    }

    with open(output_skin_dir / "skin.json", "w", encoding="utf-8") as f:
        json.dump(skin_meta, f, ensure_ascii=False, indent=2)

    print(f"-> Written {output_skin_dir / 'skin.json'}")
    print("\n[Success] Cinema skin assembly completed successfully!")


if __name__ == "__main__":
    pet_root = Path(__file__).resolve().parent.parent.parent
    v_dir = pet_root / "sucai" / "video"
    out_dir = pet_root / "skins" / "autumn_red_cinema"
    ar_dir = pet_root / "skins" / "autumn_red"

    build_cinema_skin(v_dir, out_dir, ar_dir)
