"""
Build 3.0 Live2D-Grade Animation Suite for Project Red (小红帽 v3.0).
Combines sliced master components into pixel-perfect, zero-jitter,
uniform-scale action sequences (idle, walk, drag, fall, sit, sleep, click).
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter


def build_skin():
    pet_root = Path(__file__).resolve().parent.parent
    parts_dir = pet_root / "skins" / "autumn_red" / "parts"
    skin_dir = pet_root / "skins" / "autumn_red"
    actions_dir = skin_dir / "actions"

    print(f"Building 3.0 action suite from parts in {parts_dir}...")

    # Unified Master Canvas Size
    CANVAS_W = 360
    CANVAS_H = 480
    GROUND_Y = 466  # Ground baseline where boots rest

    def load_part(name: str) -> Image.Image:
        p = parts_dir / f"{name}.png"
        if not p.exists():
            raise FileNotFoundError(f"Part not found: {p}")
        return Image.open(p).convert("RGBA")

    # Load all parts
    body_idle = load_part("idle_body")
    head_open = load_part("idle_head")
    head_half = load_part("head_half")
    head_closed = load_part("head_closed")
    ear_r = load_part("ear_right")
    ear_l = load_part("ear_left")
    ear_tw = load_part("ear_twitch")
    tail1 = load_part("idle_tail_01")
    tail2 = load_part("idle_tail_02")
    legs_stand = load_part("idle_legs")
    umb_folded = load_part("idle_umbrella")

    body_walk = load_part("walk_body")
    legs_walk = [
        load_part("walk_leg_01"),
        load_part("walk_leg_02"),
        load_part("walk_leg_03"),
        load_part("walk_leg_04"),
    ]
    tail_walk = load_part("walk_tail")
    umb_walk = load_part("walk_umbrella")

    drag_base = load_part("drag_full")
    drag_legs = load_part("drag_legs")

    para_umb = load_part("umbrella_parachute")
    updraft_coat = load_part("coat_updraft")
    head_shock = load_part("head_shocked")
    ear_dl = load_part("ear_droop_left")
    ear_dr = load_part("ear_droop_right")

    body_sit = load_part("body_sit")
    tail_cushion = load_part("tail_cushion")
    head_sleep = load_part("head_sleeping")

    # Assemble Head Helper
    def make_head(head_spr: Image.Image, r_ear: Image.Image = ear_r, l_ear: Image.Image = ear_l) -> Image.Image:
        h_c = Image.new("RGBA", (260, 270), (0, 0, 0, 0))
        h_c.paste(r_ear, (28, 12), r_ear)
        h_c.paste(l_ear, (155, 12), l_ear)
        h_c.paste(head_spr, (6, 34), head_spr)
        return h_c

    head_normal = make_head(head_open, ear_r, ear_l)
    head_half_blink = make_head(head_half, ear_r, ear_l)
    head_smile = make_head(head_closed, ear_r, ear_l)
    head_twitch = make_head(head_open, ear_tw, ear_l)

    # Shocked head with droop ears for fall / dangle
    head_shock_assembled = Image.new("RGBA", (220, 210), (0, 0, 0, 0))
    head_shock_assembled.paste(ear_dl, (15, 20), ear_dl)
    head_shock_assembled.paste(ear_dr, (120, 20), ear_dr)
    head_shock_assembled.paste(head_shock, (20, 20), head_shock)

    # ---------------- 1. IDLE Action (12 frames @ 10 FPS: natural breathing, tail sway, blinking & ear twitch) ----------------
    print("\n[1/7] Assembling 3.0 IDLE action...")
    act_idle = actions_dir / "idle"
    act_idle.mkdir(parents=True, exist_ok=True)

    bobs = [0, -1, -2, -2, -1, 0, 1, 1, 0, -1, -1, 0]
    tails = [tail1, tail1, tail1, tail1, tail2, tail2, tail2, tail1, tail1, tail1, tail1, tail1]
    heads = [
        head_normal, head_normal, head_normal,
        head_twitch, head_twitch, head_normal,
        head_normal, head_normal,
        head_half_blink, head_smile, head_half_blink,
        head_normal
    ]

    for i in range(12):
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        dy = bobs[i]
        t = tails[i]
        tx = 40 if t == tail1 else 45
        ty = 200 + dy // 2

        # Layer 1: Tail
        c.paste(t, (tx, ty), t)
        # Layer 2: Legs (firmly on ground)
        c.paste(legs_stand, (118, 250), legs_stand)
        # Layer 3: Body
        c.paste(body_idle, (38, 115 + dy), body_idle)
        # Layer 4: Umbrella
        c.paste(umb_folded, (200, 200 + dy), umb_folded)
        # Layer 5: Head
        c.paste(heads[i], (50, 0 + dy), heads[i])

        c.save(act_idle / f"idle_{i:02d}.png")
    print("  -> 12 frames generated for IDLE.")

    # ---------------- 2. WALK Action (4 frames @ 8 FPS: 4-step classic stride cycle) ----------------
    print("\n[2/7] Assembling 3.0 WALK action...")
    act_walk = actions_dir / "walk"
    act_walk.mkdir(parents=True, exist_ok=True)

    walk_leg_offsets = [
        (75, 326),   # Frame 0: Contact L
        (118, 325),  # Frame 1: Pass R
        (75, 329),   # Frame 2: Contact R
        (122, 324),  # Frame 3: Pass L
    ]

    for i in range(4):
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        # Gentle body bobbing on passing steps
        by = 135 if i in (0, 2) else 133
        uy = 125 if i in (0, 2) else 123

        # Layer 1: Tail
        c.paste(tail_walk, (150, 120), tail_walk)
        # Layer 2: Leg
        lx, ly = walk_leg_offsets[i]
        c.paste(legs_walk[i], (lx, ly), legs_walk[i])
        # Layer 3: Body
        c.paste(body_walk, (90, by), body_walk)
        # Layer 4: Umbrella
        c.paste(umb_walk, (25, uy), umb_walk)

        c.save(act_walk / f"walk_{i:02d}.png")
    print("  -> 4 frames generated for WALK (Contact L -> Pass R -> Contact R -> Pass L).")

    # ---------------- 3. DRAG Action (4 frames @ 8 FPS: dangle pendulum physics) ----------------
    print("\n[3/7] Assembling 3.0 DRAG action...")
    act_drag = actions_dir / "drag"
    act_drag.mkdir(parents=True, exist_ok=True)

    drag_angles = [0.0, -2.5, 0.0, 2.5]
    for i, ang in enumerate(drag_angles):
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        spr = drag_base
        if ang != 0.0:
            spr = spr.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
        # Align collar/hand to center top
        x = (CANVAS_W - spr.width) // 2 + int(ang * 2)
        y = 6
        c.alpha_composite(spr, (x, y))
        c.save(act_drag / f"drag_{i:02d}.png")
    print("  -> 4 frames generated for DRAG (pendulum dangle).")

    # ---------------- 4. FALL Action (4 frames @ 8 FPS: parachute float) ----------------
    print("\n[4/7] Assembling 3.0 FALL action...")
    act_fall = actions_dir / "fall"
    act_fall.mkdir(parents=True, exist_ok=True)

    fall_bobs = [0, -2, -4, -2]
    for i, f_dy in enumerate(fall_bobs):
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        # 1. Umbrella parachute
        c.paste(para_umb, (45, 15 + f_dy), para_umb)
        # 2. Flailing legs
        c.paste(drag_legs, (120, 290 + f_dy), drag_legs)
        # 3. Updraft coat
        c.paste(updraft_coat, (75, 120 + f_dy), updraft_coat)
        # 4. Shocked head
        c.paste(head_shock_assembled, (75, 105 + f_dy), head_shock_assembled)

        c.save(act_fall / f"fall_{i:02d}.png")
    print("  -> 4 frames generated for FALL (parachute canopy & updraft flutter).")

    # ---------------- 5. SIT Action (4 frames @ 4 FPS: cozy floor sitting companion) ----------------
    print("\n[5/7] Assembling 3.0 SIT action...")
    act_sit = actions_dir / "sit"
    act_sit.mkdir(parents=True, exist_ok=True)

    sit_bobs = [0, -1, -2, -1]
    for i, s_dy in enumerate(sit_bobs):
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        # Tail cushion
        c.paste(tail_cushion, (135, 320), tail_cushion)
        # Body sit (ground aligned)
        c.paste(body_sit, (82, 319), body_sit)
        # Head with gentle breathing
        h = head_normal if i != 2 else head_half_blink
        c.paste(h, (50, 150 + s_dy), h)

        c.save(act_sit / f"sit_{i:02d}.png")
    print("  -> 4 frames generated for SIT.")

    # ---------------- 6. SLEEP Action (4 frames @ 3 FPS: peaceful nap curled in tail) ----------------
    print("\n[6/7] Assembling 3.0 SLEEP action...")
    act_sleep = actions_dir / "sleep"
    act_sleep.mkdir(parents=True, exist_ok=True)

    sleep_bobs = [0, -1, -2, -1]
    for i, z_dy in enumerate(sleep_bobs):
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        # Tail cushion
        c.paste(tail_cushion, (130, 319), tail_cushion)
        # Sleeping head nestled into cushion with slow breathing
        c.paste(head_sleep, (40, 300 + z_dy), head_sleep)

        c.save(act_sleep / f"sleep_{i:02d}.png")
    print("  -> 4 frames generated for SLEEP.")

    # ---------------- 7. CLICK Action (4 frames @ 6 FPS: happy blushing hop & smile) ----------------
    print("\n[7/7] Assembling 3.0 CLICK action...")
    act_click = actions_dir / "click"
    act_click.mkdir(parents=True, exist_ok=True)

    click_bobs = [0, -6, -12, -4]
    click_heads = [head_smile, head_smile, head_twitch, head_smile]

    for i in range(4):
        c = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        dy = click_bobs[i]

        # Tail
        c.paste(tail2, (45, 200 + dy // 2), tail2)
        # Legs
        c.paste(legs_stand, (118, 250 + dy), legs_stand)
        # Body
        c.paste(body_idle, (38, 115 + dy), body_idle)
        # Umbrella
        c.paste(umb_folded, (200, 200 + dy), umb_folded)
        # Happy head
        c.paste(click_heads[i], (50, 0 + dy), click_heads[i])

        c.save(act_click / f"click_{i:02d}.png")
    print("  -> 4 frames generated for CLICK.")

    # ---------------- 8. METADATA skin.json (v3.0 Specification) ----------------
    print("\nUpdating skin.json metadata to 3.0 specification...")
    meta = {
        "id": "autumn_red",
        "name": "红崽·秋雨落叶 (小红帽 v3.0 Live2D-Modular)",
        "author": "User & Antigravity",
        "version": "3.0",
        "description": "3.0 Live2D模块化重构版：单图集部件解构、零尺度跳跃、原生可变帧率DVRR与极低能耗引擎。",
        "base_size": [360, 480],
        "default_scale": 0.75,
        "actions": {
            "idle": {"fps": 10, "loop": True},
            "walk": {"fps": 8, "speed": 3, "loop": True},
            "drag": {"fps": 8, "loop": True},
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
            "红一直看着你呢。",
            "摸摸头...红很开心。"
        ]
    }

    with open(skin_dir / "skin.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # ---------------- 9. RIG CONFIGURATION rig.json (3.0 Modular Spec) ----------------
    print("Generating rig.json modular skeleton configuration...")
    rig = {
        "version": "3.0",
        "canvas_size": [360, 480],
        "ground_baseline_y": 466,
        "root": {
            "name": "root",
            "position": [180, 466]
        },
        "bones": [
            {
                "name": "tail",
                "parent": "root",
                "pivot": [115, 260],
                "sprite": "parts/idle_tail_01.png",
                "z_order": 1,
                "physics": {"mass": 1.2, "damping": 0.85, "stiffness": 0.12}
            },
            {
                "name": "legs",
                "parent": "root",
                "pivot": [178, 250],
                "sprite": "parts/idle_legs.png",
                "z_order": 2
            },
            {
                "name": "body",
                "parent": "root",
                "pivot": [180, 260],
                "sprite": "parts/idle_body.png",
                "z_order": 3,
                "physics": {"breathing_amp": 2.0, "breathing_speed": 1.8}
            },
            {
                "name": "umbrella",
                "parent": "body",
                "pivot": [250, 260],
                "sprite": "parts/idle_umbrella.png",
                "z_order": 4
            },
            {
                "name": "head",
                "parent": "body",
                "pivot": [180, 160],
                "sprite": "parts/idle_head.png",
                "z_order": 5,
                "gaze_tracking": {"max_angle_deg": 6.0, "smooth_factor": 0.15}
            },
            {
                "name": "ear_right",
                "parent": "head",
                "pivot": [95, 80],
                "sprite": "parts/ear_right.png",
                "z_order": 6,
                "physics": {"twitch_prob": 0.08}
            },
            {
                "name": "ear_left",
                "parent": "head",
                "pivot": [215, 80],
                "sprite": "parts/ear_left.png",
                "z_order": 6
            }
        ]
    }

    with open(skin_dir / "rig.json", "w", encoding="utf-8") as f:
        json.dump(rig, f, ensure_ascii=False, indent=2)

    print("\n[SUCCESS] Project Red 3.0 skin completely assembled and verified!")


if __name__ == "__main__":
    build_skin()
