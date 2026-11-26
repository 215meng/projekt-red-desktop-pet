"""
dialogue_manager.py - 语境对话与台词管理中枢
支持：
  - 默认皮肤台词池
  - 语境专属台词 (摸头、提溜悬空、触地受力、闲置悠闲)
  - 为未来接入 LLM 大模型智能对话预留扩展契约与钩子
"""

import random
from typing import Dict, List, Optional


class DialogueManager:
    """台词与语境对话管理器"""

    # 语境专属台词表
    CONTEXT_DIALOGUES: Dict[str, List[str]] = {
        "drag": [
            "后、后颈皮被抓住了……！",
            "哇……！要掉下去了，博士！",
            "短腿在半空中扑腾……抓紧红！",
            "博士……红不是小狼崽，不要拎后颈皮啦……",
        ],
        "land": [
            "呼……安全着地！",
            "红的小刀，稳稳收好了。",
            "双膝受力缓冲……红很擅长着陆。",
            "博士，没有摔疼红哦。",
        ],
        "headpat": [
            "摸摸……红也想摸博士的头。",
            "呼噜噜……红的狼耳很软吗？",
            "红很乖的，尾巴也给你摸摸。",
            "博士的手掌……很暖和。",
        ],
        "idle": [
            "红的尾巴……给博士摸摸。",
            "尾巴……毛茸茸的大尾巴，红也想摸……",
            "红会一直在这里，守着博士。",
            "狼的气味……红抓到你了。",
            "红很听话的，不会咬人。",
            "呼呼……大尾巴很暖和。",
            "红在看着你呢，博士。",
            "红的小刀很锋利，不会弄伤博士的。",
            "博士……累了吗？红给你捏捏肩？",
            "下雪了……红的围巾分你一半。",
            "耳朵抖了抖……博士刚才在叫红吗？",
        ]
    }

    def __init__(self, custom_dialogues: Optional[List[str]] = None):
        self.skin_dialogues: List[str] = list(custom_dialogues) if custom_dialogues else []
        self.enabled: bool = True

    def set_skin_dialogues(self, dialogues: List[str]):
        self.skin_dialogues = list(dialogues)

    def get_context_dialogue(self, context: str) -> str:
        """根据语境上下文获取台词"""
        if not self.enabled:
            return ""

        candidates = self.CONTEXT_DIALOGUES.get(context, [])
        if not candidates:
            candidates = self.skin_dialogues or self.CONTEXT_DIALOGUES["idle"]

        return random.choice(candidates)

    def get_random_dialogue(self) -> str:
        """获取闲置随机台词"""
        if not self.enabled:
            return ""

        pool = self.skin_dialogues if self.skin_dialogues else self.CONTEXT_DIALOGUES["idle"]
        return random.choice(pool)

    # ---------------- 预留未来扩展大模型接口 ----------------
    def generate_llm_reply(self, prompt: str) -> Optional[str]:
        """
        预留 LLM 大语言模型智能对话扩展钩子。
        未来可在此处接入 OpenAI / Gemini / Ollama 本地模型 API。
        """
        return None
