"""
state_machine.py - 状态机与过渡调度器
管理桌宠 10 大核心姿态流转，自动插入跨姿态平滑过渡切片 (如 trans_sit, trans_sleep, land)。
"""

from typing import Dict, Optional, Tuple, Any, List


class TransitionScheduler:
    """
    姿态过渡调度器：
    维护状态迁移矩阵，调度平滑骨骼融合过渡切片。
    """

    DEFAULT_TRANSITIONS: Dict[str, str] = {
        "idle->sit": "trans_sit",
        "sit->sleep": "trans_sleep",
        "Relax->Sit": "trans_sit",
        "Sit->Sleep": "trans_sleep",
        "drag->fall": "fall",
        "fall->idle": "land",
        "fall->land": "land",
    }

    def __init__(self, custom_transitions: Optional[Dict[str, str]] = None):
        self.transitions: Dict[str, str] = dict(self.DEFAULT_TRANSITIONS)
        if custom_transitions:
            self.transitions.update(custom_transitions)

    def register_transition(self, from_state: str, to_state: str, transition_action: str):
        key = f"{from_state}->{to_state}"
        self.transitions[key] = transition_action

    def get_transition(self, current_state: str, target_state: str) -> Optional[str]:
        if not current_state or not target_state or current_state == target_state:
            return None
        return self.transitions.get(f"{current_state}->{target_state}")

    def plan_transition(
        self,
        current_state: str,
        target_state: str,
        available_actions: Dict[str, Any]
    ) -> Tuple[str, Optional[str]]:
        """
        计算完整的迁移路径：
        返回 (immediate_action_to_play, next_action_to_follow)
        """
        trans_action = self.get_transition(current_state, target_state)
        if trans_action and trans_action in available_actions:
            return trans_action, target_state
        return target_state, None


class PetStateMachine:
    """
    桌宠全局状态机。
    跟踪当前状态、锁定状态、支持的状态列表，保证状态迁移的合法性与平滑性。
    """

    VALID_STATES = {
        "idle", "walk", "drag", "fall", "land",
        "sit", "sleep", "headpat", "dizzy", "trans_sit", "trans_sleep",
        "cuddle_tail", "sharpen_knife", "alert_scout", "yawn_stretch",
        "edge_peek", "doze_off"
    }

    def __init__(self, initial_state: str = "idle"):
        self.current_state: str = initial_state
        self.locked_state: Optional[str] = None
        self.scheduler = TransitionScheduler()

    def set_locked_state(self, state: Optional[str]):
        """用户通过菜单强制点播并保持某个动作姿态"""
        self.locked_state = state

    def is_locked(self) -> bool:
        return self.locked_state is not None

    def can_transition_to(self, new_state: str) -> bool:
        if self.locked_state and new_state != self.locked_state and new_state in ("idle", "walk", "sit", "sleep"):
            # 锁定状态下禁止自主行为切换
            return False
        return True

    def transition(self, new_state: str):
        self.current_state = new_state
