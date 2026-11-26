"""
tray.py - 独立托盘控制器
负责 Windows 系统任务栏托盘图标、托盘菜单、左键双击召回桌宠。
"""

from typing import TYPE_CHECKING
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QSystemTrayIcon, QApplication

if TYPE_CHECKING:
    from pet.window import PetWindow


class PetTrayManager:
    """管理桌宠在操作系统托盘中的状态与行为"""

    def __init__(self, window: "PetWindow"):
        self.window = window
        self.tray_icon = QSystemTrayIcon(window)
        self._init_tray()

    def _init_tray(self):
        # 提取当前动作首帧作为托盘图标
        icon = self._get_current_icon()
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("明日方舟·红 (Spine 纯净桌宠)")

        # 双击托盘恢复显示与重置到屏幕底端
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _get_current_icon(self) -> QIcon:
        if self.window.current_action and self.window.current_action.frame_count > 0:
            pix = self.window.current_action.frames[0]
            if not pix.isNull():
                return QIcon(pix.scaled(32, 32))
        # 默认回退红色小方块图标
        fallback = QPixmap(32, 32)
        fallback.fill("#e74c3c")
        return QIcon(fallback)

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.window.isHidden():
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()
            else:
                self.window.reset_position()

    def update_icon(self):
        icon = self._get_current_icon()
        self.tray_icon.setIcon(icon)

    def show_message(self, title: str, message: str, msecs: int = 3000):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, msecs)
