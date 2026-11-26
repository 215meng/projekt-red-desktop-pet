"""
skin_manager.py - 顶层导出
保持向前兼容，内部已完全重构为 pet.skin 纯净架构。
"""

from pet.skin.models import PetSkin, SkinAction, LazyFrameList
from pet.skin.skin_manager import SkinManager

__all__ = [
    "PetSkin",
    "SkinAction",
    "LazyFrameList",
    "SkinManager",
]
