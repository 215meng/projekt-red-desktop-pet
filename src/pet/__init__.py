"""
Projekt Red Desktop Pet 4.1.0 Clean Architecture.
"""

__version__ = "4.1.0"

from .config import ConfigManager
from .skin import SkinManager, PetSkin, SkinAction
from .window import PetWindow
from .app import main

__all__ = [
    "__version__",
    "ConfigManager",
    "SkinManager",
    "PetSkin",
    "SkinAction",
    "PetWindow",
    "main",
]
