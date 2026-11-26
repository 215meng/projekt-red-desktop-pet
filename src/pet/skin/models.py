"""
models.py - 皮肤与动作数据契约模型
定义 LazyFrameList (滑动窗口帧代理)、SkinAction (动作规格与下一跳)、PetSkin (皮肤实体)。
彻底移除旧版纸娃娃与 rig.json 依赖。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from PySide6.QtGui import QPixmap


class LazyFrameList:
    """
    LRU / 滑动窗口序列帧代理。
    模拟 List[QPixmap]，限制常驻内存最大帧数 (默认 35 帧)，按需加载并动态逐出。
    """

    def __init__(self, file_paths: List[Path], max_cache_size: int = 35):
        self.file_paths = file_paths
        self.max_cache_size = max_cache_size
        self._cache: Dict[int, QPixmap] = {}
        self._access_order: List[int] = []

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(len(self.file_paths)))]

        n = len(self.file_paths)
        if n == 0:
            return QPixmap()
        norm_idx = idx % n
        if norm_idx in self._cache:
            return self._cache[norm_idx]

        pix = QPixmap(str(self.file_paths[norm_idx]))
        self._cache[norm_idx] = pix
        self._access_order.append(norm_idx)

        while len(self._cache) > self.max_cache_size:
            evict = self._access_order.pop(0)
            self._cache.pop(evict, None)

        return pix

    def __iter__(self):
        for i in range(len(self.file_paths)):
            yield self[i]

    def clear_cache(self):
        self._cache.clear()
        self._access_order.clear()


class SkinAction:
    """
    单个动作实体。
    包含帧序列、采样帧率、帧延迟、循环规则、动作类型 (loop/once/transition) 与自动下一跳。
    """

    def __init__(
        self,
        name: str,
        frames: Any,
        fps: int = 30,
        speed: int = 2,
        loop: bool = True,
        next_action: Optional[str] = None,
        action_type: str = "loop",
        duration: float = 0.0
    ):
        self.name = name
        self.frames = frames
        self.fps = fps
        self.speed = speed
        self.frame_delay_ms = max(10, int(1000 / fps)) if fps > 0 else 33
        self.loop = loop
        self.next_action = next_action
        self.action_type = action_type
        self.duration = duration

    @property
    def frame_count(self) -> int:
        return len(self.frames)


class PetSkin:
    """
    4.0 纯净皮肤实体。
    完全由 skin.json 与 transition_matrix.json 元数据及 frames/ 目录驱动。
    """

    def __init__(self, skin_id: str, skin_path: Path):
        self.skin_id = skin_id
        self.skin_path = skin_path
        self.name = skin_id
        self.author = "Unknown"
        self.version = "4.1"
        self.description = ""
        self.base_size: Tuple[int, int] = (360, 480)
        self.anchor_y: int = 466
        self.default_scale: float = 1.0
        self.fps: int = 30
        self.dialogues: List[str] = []
        self.actions: Dict[str, SkinAction] = {}
        self.transitions: Dict[str, str] = {}
        self._load()

    def _load(self):
        json_path = self.skin_path / "skin.json"
        actions_cfg = {}
        global_fps = 30

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    self.name = meta.get("title", meta.get("name", self.skin_id))
                    self.author = meta.get("author", self.author)
                    self.version = meta.get("version", self.version)
                    self.description = meta.get("description", "")
                    
                    w = meta.get("width", 360)
                    h = meta.get("height", 480)
                    self.base_size = (w, h)
                    self.anchor_y = meta.get("anchor_y", 466)
                    self.default_scale = float(meta.get("default_scale", 1.0))
                    self.dialogues = meta.get("dialogues", [])
                    global_fps = meta.get("fps", 30)
                    self.fps = global_fps
                    actions_cfg = meta.get("actions", {})
                    self.transitions = meta.get("transitions", {})
            except Exception as e:
                print(f"[SkinModel] Error parsing skin.json for {self.skin_id}: {e}")

        # 读取状态迁移表 transition_matrix.json
        matrix_path = self.skin_path / "transition_matrix.json"
        if matrix_path.exists():
            try:
                with open(matrix_path, "r", encoding="utf-8") as f:
                    m_data = json.load(f)
                    self.transitions.update(m_data.get("transitions", {}))
            except Exception as e:
                print(f"[SkinModel] Error reading transition_matrix.json: {e}")

        # 扫描帧切片目录 (frames/ 或 actions/)
        frames_dir = self.skin_path / "frames"
        if not frames_dir.exists():
            frames_dir = self.skin_path / "actions"

        if frames_dir.exists():
            for action_dir in sorted(frames_dir.iterdir()):
                if action_dir.is_dir():
                    act_name = action_dir.name
                    frame_files = sorted(
                        [p for p in action_dir.iterdir() if p.suffix.lower() in (".png", ".webp", ".jpg")]
                    )
                    if frame_files:
                        lazy_frames = LazyFrameList(frame_files, max_cache_size=35)
                        cfg = actions_cfg.get(act_name, {})
                        fps = cfg.get("fps", global_fps)
                        speed = cfg.get("speed", 2)
                        
                        act_type = cfg.get("type", "loop")
                        loop = cfg.get("loop", (act_type == "loop"))
                        duration = cfg.get("duration", len(frame_files) / fps if fps > 0 else 1.0)
                        
                        next_act = cfg.get("next", None)
                        if act_type == "transition" and not next_act:
                            if act_name.startswith("trans_"):
                                next_act = act_name.replace("trans_", "")
                        elif act_type == "once" and not next_act:
                            next_act = "idle"

                        self.actions[act_name] = SkinAction(
                            act_name,
                            lazy_frames,
                            fps=fps,
                            speed=speed,
                            loop=loop,
                            next_action=next_act,
                            action_type=act_type,
                            duration=duration
                        )

    def has_action(self, action_name: str) -> bool:
        return action_name in self.actions and self.actions[action_name].frame_count > 0

    def get_action(self, action_name: str) -> Optional[SkinAction]:
        return self.actions.get(action_name) or self.actions.get("idle")
