"""
bubble.py - 对话气泡卡片组件
半透明毛玻璃质感、圆角红色边框与阴影，支持自动定时隐去。
彻底修复开机无文字红色空框残留问题。
"""

from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QWidget, QLabel, QGraphicsDropShadowEffect


class SpeechBubble(QWidget):
    """Semi-transparent cute speech bubble above pet's head."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.SubWindow | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        
        self.label = QLabel(self)
        self.label.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        self.label.setStyleSheet(
            """
            QLabel {
                background-color: rgba(255, 255, 255, 240);
                color: #2b2b2b;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                padding: 6px 12px;
            }
            """
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.label.setGraphicsEffect(shadow)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        # 核心修复：构造初始阶段强行彻底隐藏，杜绝开机空矩形红框残留
        self.hide()

    def show_text(self, text: str, global_pos: QPoint, duration_ms: int = 3500):
        if not text or not str(text).strip():
            self.hide()
            return
        self.label.setText(str(text).strip())
        self.label.adjustSize()
        self.resize(self.label.sizeHint())
        
        # 居中对齐在头顶
        x = global_pos.x() - self.width() // 2
        y = global_pos.y() - self.height() - 8
        self.move(x, y)
        self.show()
        self.hide_timer.start(duration_ms)
