"""
skin_manager.py - 纯净 4.0 皮肤管理器
负责皮肤的发现、扫描加载、热重载与查询。
"""

from pathlib import Path
from typing import Dict, List, Optional
from pet.skin.models import PetSkin, SkinAction, LazyFrameList


class SkinManager:
    """
    4.0 纯净皮肤管理器。
    负责管理 skins/ 目录下所有合规的 Spine 工业级骨骼切片皮肤。
    """

    def __init__(self, skins_root: Path):
        self.skins_root = skins_root
        self.skins: Dict[str, PetSkin] = {}
        self.reload_skins()

    def reload_skins(self) -> List[str]:
        """扫描皮肤目录并重载所有合规皮肤"""
        self.skins.clear()
        if not self.skins_root.exists():
            return []

        for item in sorted(self.skins_root.iterdir()):
            if item.is_dir():
                has_frames = (item / "frames").exists() or (item / "actions").exists()
                has_skin_json = (item / "skin.json").exists()
                if has_frames or has_skin_json:
                    skin = PetSkin(item.name, item)
                    if skin.actions:
                        self.skins[skin.skin_id] = skin
                        print(f"[SkinManager 4.0] 成功加载皮肤: {skin.name} ({skin.skin_id})，动作数: {len(skin.actions)}")

        return list(self.skins.keys())

    def get_skin(self, skin_id: str) -> Optional[PetSkin]:
        return self.skins.get(skin_id)

    def get_available_skins(self) -> List[PetSkin]:
        return list(self.skins.values())
