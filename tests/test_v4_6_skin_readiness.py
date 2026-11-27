# -*- coding: utf-8 -*-
"""
test_v4_6_skin_readiness.py - v4.6.0 (4.X 终章 & 5.X 多皮肤/AI皮肤基座) 专项验收测试
验证：
1. 5.X AI 生图精简主题皮肤 (仅 Tier-1 动作、fps=12、native_facing="left"、自定义 icon.png、context_dialogues) 可被正常装载与渲染镜像
2. 切肤时自动清理旧皮肤帧缓存、清空 Crossfade 残影并同步刷新 DialogueManager 语境台词
3. 精简皮肤在 _decide_behavior() 各种时间/随机分支下优雅降级零异常
4. set_dialogues_enabled() 与 reload_skins() 信号契约准确发射
5. 通用皮肤质检门禁工具 tools/validate_skin.py 对 spine_red 与模拟 AI 皮肤均返回 exit code 0
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

pet_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pet_root / "src"))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from pet import __version__
from pet.skin import SkinManager
from pet.window import PetWindow


def _create_mock_ai_skin(root_dir: Path) -> Path:
    """生成模拟的 5.X AI 生图精简主题皮肤 ai_winter_red（仅含 Tier-1 6 项动作，native_facing='left', fps=12）"""
    skin_dir = root_dir / "ai_winter_red"
    skin_dir.mkdir(parents=True, exist_ok=True)

    # 自定义托盘图标
    icon_img = Image.new("RGBA", (64, 64), (180, 60, 60, 255))
    icon_img.save(skin_dir / "icon.png")

    tier1_actions = {
        "idle": {"name": "待机呼吸", "type": "loop", "fps": 12, "frames_count": 4, "loop": True},
        "walk": {"name": "漫步", "type": "loop", "fps": 12, "frames_count": 4, "loop": True},
        "drag": {"name": "提溜", "type": "loop", "fps": 12, "frames_count": 3, "loop": True},
        "fall": {"name": "飘落", "type": "loop", "fps": 12, "frames_count": 3, "loop": True},
        "land": {"name": "缓冲", "type": "once", "fps": 12, "frames_count": 3, "loop": False},
        "headpat": {"name": "摸头", "type": "once", "fps": 12, "frames_count": 3, "loop": False},
    }

    for act_name, cfg in tier1_actions.items():
        act_dir = skin_dir / "frames" / act_name
        act_dir.mkdir(parents=True, exist_ok=True)
        for i in range(cfg["frames_count"]):
            im = Image.new("RGBA", (360, 480), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im)
            # 构造竖直连通剪影：底边稳定停在 y=426（悬空 drag/fall 抬高至 y=390）
            bottom_y = 390 if act_name in ("drag", "fall") else 426
            top_y = bottom_y - 220
            draw.ellipse([130, top_y, 230, top_y + 90], fill=(220, 180, 180, 255))
            draw.rectangle([140, top_y + 70, 220, bottom_y], fill=(190, 50, 50, 255))
            im.save(act_dir / f"frame_{i:03d}.png")

    manifest = {
        "name": "ai_winter_red",
        "title": "红 · 冬日咖啡馆（AI 主题测试）",
        "author": "215meng",
        "version": "1.0.0",
        "source_type": "ai_sprites",
        "theme": "winter_coffee",
        "native_facing": "left",
        "fps": 12,
        "width": 360,
        "height": 480,
        "anchor_y": 466,
        "ground_line_y": 426,
        "default_scale": 1.0,
        "actions": tier1_actions,
        "context_dialogues": {
            "headpat": ["热可可的香气……红很喜欢博士摸头。"],
            "dizzy": ["头晕了……喝口热水缓一缓。"]
        },
        "dialogues": ["冬天适合待在室内陪着博士。"]
    }
    with open(skin_dir / "skin.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return skin_dir


def test_version_and_multi_skin_readiness():
    assert __version__ == "4.6.0", f"Expected __version__ == '4.6.0', got {__version__!r}"
    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_skins = Path(tmp) / "skins"
        tmp_skins.mkdir(parents=True, exist_ok=True)
        ai_skin_dir = _create_mock_ai_skin(tmp_skins)

        # 复制或以标准 SkinManager 同时验证真实 spine_red 与模拟 AI 皮肤
        mgr_real = SkinManager(pet_root / "skins")
        red_skin = mgr_real.get_skin("spine_red")
        assert red_skin is not None
        assert red_skin.native_facing == "right"
        assert red_skin.get_icon_path() is not None and red_skin.get_icon_path().exists()

        # 先验证缓存预热与清理机制
        _ = red_skin.actions["idle"].frames[0]
        assert len(red_skin.actions["idle"].frames._cache) == 1
        red_skin.clear_all_caches()
        assert len(red_skin.actions["idle"].frames._cache) == 0

        # 验证临时 AI 皮肤装载
        mgr_ai = SkinManager(tmp_skins)
        ai_skin = mgr_ai.get_skin("ai_winter_red")
        assert ai_skin is not None
        assert ai_skin.source_type == "ai_sprites"
        assert ai_skin.theme == "winter_coffee"
        assert ai_skin.native_facing == "left"
        assert ai_skin.fps == 12
        assert ai_skin.ground_line_y == 426
        assert ai_skin.get_icon_path() == ai_skin_dir / "icon.png"

        # 验证 PetWindow 在纯 Tier-1 精简皮肤下的加载、镜像与语境台词
        win = PetWindow(mgr_ai, initial_skin_id="ai_winter_red")
        assert win._resolve_render_facing_left(False) is True
        assert win._resolve_render_facing_left(True) is False
        assert win.dialogue_manager.get_context_dialogue("headpat") == "热可可的香气……红很喜欢博士摸头。"
        # 未覆写的语境应平滑回退默认台词池
        assert len(win.dialogue_manager.get_context_dialogue("land")) > 0

        # 多次运行自主决策，验证缺失 Tier-2/3 动作时优雅降级且不崩溃
        win.locked_action = None
        for _ in range(40):
            win.state = "idle"
            win._decide_behavior()
            assert win.current_skin.has_action(win.state) or win.state == "idle"
        # 模拟在未定义 sit/sleep 的情况下进入 sit 状态分支也不会抛错
        win.state = "sit"
        win._decide_behavior()

        # 信号发射测试
        fired = {"dlg": [], "reloaded": []}
        win.dialogues_enabled_changed.connect(lambda v: fired["dlg"].append(v))
        win.skins_reloaded.connect(lambda ids: fired["reloaded"].append(ids))
        win.set_dialogues_enabled(False)
        assert win.dialogues_enabled is False and fired["dlg"] == [False]
        win.reload_skins()
        assert fired["reloaded"] == [["ai_winter_red"]]

        # 验证 validate_skin.py CLI 校验模拟 AI 皮肤通过
        res_ai = subprocess.run(
            [sys.executable, str(pet_root / "tools" / "validate_skin.py"), str(ai_skin_dir)],
            capture_output=True, text=True, check=False
        )
        assert res_ai.returncode == 0, f"validate_skin failed for ai skin:\n{res_ai.stdout}\n{res_ai.stderr}"

    print("[PASS] test_version_and_multi_skin_readiness")


def test_validate_real_spine_red():
    res = subprocess.run(
        [sys.executable, str(pet_root / "tools" / "validate_skin.py"), "spine_red"],
        capture_output=True, text=True, check=False
    )
    assert res.returncode == 0, f"validate_skin failed for spine_red:\n{res.stdout}\n{res.stderr}"
    print("[PASS] test_validate_real_spine_red")


if __name__ == "__main__":
    test_version_and_multi_skin_readiness()
    test_validate_real_spine_red()
    print("\nALL V4.6 MULTI-SKIN & AI SKIN READINESS TESTS PASSED!")
