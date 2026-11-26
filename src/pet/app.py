"""
Main application controller and lifecycle manager for Desktop Pet.
"""

import sys
import os
import time
import traceback
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from pet.config import ConfigManager
from pet.skin_manager import SkinManager
from pet.window import PetWindow
from pet.ui.menu import build_pet_tray_menu


def setup_crash_logging(log_path: Path):
    def log_exception(exc_type, exc_value, exc_traceback):
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- Crash at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = log_exception


def main() -> int:
    # Ensure working directory is project root
    root_dir = Path(__file__).resolve().parent.parent.parent
    os.chdir(root_dir)

    setup_crash_logging(root_dir / "pet_crash.log")

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config_mgr = ConfigManager(root_dir / "config.json")
    skins_root = root_dir / "skins"
    skin_mgr = SkinManager(skins_root)

    current_skin_id = config_mgr.get("current_skin", "spine_red")

    # Main pet window
    window = PetWindow(
        skin_mgr,
        initial_skin_id=current_skin_id,
        initial_scale=config_mgr.get("scale", 1.0),
        initial_activity_level=config_mgr.get("activity_level", "quiet")
    )
    window.dialogues_enabled = config_mgr.get("dialogues_enabled", True)
    window.show()

    # System Tray Icon
    tray = QSystemTrayIcon(app)

    def update_tray_icon(skin_id: str):
        icon_path = skins_root / skin_id / "frames" / "idle" / "frame_000.png"
        if not icon_path.exists():
            icon_path = skins_root / skin_id / "actions" / "idle" / "idle_00.png"
        if not icon_path.exists():
            icon_path = skins_root / "spine_red" / "frames" / "idle" / "frame_000.png"
        if icon_path.exists():
            tray.setIcon(QIcon(str(icon_path)))
        else:
            tray.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_DesktopIcon))

    def refresh_tray_menu():
        tray.setContextMenu(build_pet_tray_menu(window, app))
        skin_name = window.current_skin.name if window.current_skin else "Projekt Red"
        tray.setToolTip(f"红崽桌宠 4.1 - {skin_name}")

    def on_tray_activated(reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if window.isHidden():
                window.show()
                window.raise_()
                window.activateWindow()
            else:
                window.reset_position()

    tray.activated.connect(on_tray_activated)
    window.tray_manager = tray

    update_tray_icon(current_skin_id)
    refresh_tray_menu()

    # Config persistence sync
    def on_skin_changed(skin_id: str):
        config_mgr.set("current_skin", skin_id)
        update_tray_icon(skin_id)
        refresh_tray_menu()

    def on_scale_changed(scale: float):
        config_mgr.set("scale", scale)
        refresh_tray_menu()

    def on_activity_level_changed(level: str):
        config_mgr.set("activity_level", level)
        refresh_tray_menu()

    window.skin_changed.connect(on_skin_changed)
    window.scale_changed.connect(on_scale_changed)
    window.activity_level_changed.connect(on_activity_level_changed)

    tray.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
