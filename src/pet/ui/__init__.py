"""
pet.ui - 交互界面模块
包含上下文菜单、系统托盘、气泡组件。
"""

from pet.ui.menu import build_pet_context_menu
from pet.ui.tray import PetTrayManager
from pet.ui.bubble import SpeechBubble

__all__ = [
    "build_pet_context_menu",
    "PetTrayManager",
    "SpeechBubble",
]
