"""
pet.core - 核心引擎模块
包含高性能渲染器、状态机与过渡调度器、物理与动力学。
"""

from pet.core.renderer import ZeroAllocRenderer
from pet.core.physics import (
    DampedHarmonicOscillator,
    SquashAndStretch,
    GazeTracker,
    FallingPhysics,
)
from pet.core.state_machine import TransitionScheduler, PetStateMachine

__all__ = [
    "ZeroAllocRenderer",
    "DampedHarmonicOscillator",
    "SquashAndStretch",
    "GazeTracker",
    "FallingPhysics",
    "TransitionScheduler",
    "PetStateMachine",
]
