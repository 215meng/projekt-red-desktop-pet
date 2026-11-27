"""
Menu and context actions builder for Desktop Pet.
Supports rich right-click context menu and system tray menu with
dynamic action discovery, action lock/persistence, ultra-compact scaling (0.35x ~ 2.0x),
skin hot-reloading, and click-through control.
"""

from typing import TYPE_CHECKING
from PySide6.QtCore import QPoint
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import QMenu, QApplication

if TYPE_CHECKING:
    from pet.window import PetWindow

MENU_STYLE = """
QMenu {
    background-color: #1e2024;
    color: #e8eaed;
    border: 1px solid #343840;
    border-radius: 8px;
    padding: 6px;
    font-family: 'Microsoft YaHei UI', 'Microsoft YaHei';
    font-size: 13px;
}
QMenu::item {
    padding: 6px 26px 6px 14px;
    border-radius: 4px;
    margin: 1px 2px;
}
QMenu::item:selected {
    background-color: #2f333c;
    color: #ffffff;
}
QMenu::item:disabled {
    color: #70757e;
}
QMenu::separator {
    height: 1px;
    background: #2e323a;
    margin: 5px 10px;
}
QMenu::right-arrow {
    margin: 2px 6px 2px 0px;
}
QMenu::indicator {
    width: 14px;
    height: 14px;
    margin-left: 6px;
}
"""

ACTION_LABEL_MAP = {
    "idle": "待机",
    "walk": "漫步",
    "sit": "乖坐",
    "sleep": "熟睡",
    "headpat": "摸头",
    "dizzy": "戳晕",
    "click": "摸头反应",
    "greet": "问候",
    "drag": "提溜悬空",
    "fall": "半空飘落",
    "land": "触地缓冲",
    "trans_sit": "站姿转坐",
    "trans_sleep": "坐姿转睡",
    "cuddle_tail": "抱尾蹭脸",
    "sharpen_knife": "磨刀拭刃",
    "alert_scout": "警惕耸耳",
    "yawn_stretch": "伸懒腰打哈欠",
    "edge_peek": "边缘探头",
    "doze_off": "深夜打瞌睡",
}


def _add_skin_submenu(menu: QMenu, window: "PetWindow"):
    skin_menu = menu.addMenu("皮肤切换")
    skin_group = QActionGroup(window)
    available_skins = window.skin_manager.get_available_skins()

    for skin in available_skins:
        action = skin_menu.addAction(skin.name)
        action.setCheckable(True)
        if window.current_skin and window.current_skin.skin_id == skin.skin_id:
            action.setChecked(True)
        action.triggered.connect(lambda checked=False, sid=skin.skin_id: window.set_skin(sid))
        skin_group.addAction(action)

    skin_menu.addSeparator()
    reload_action = skin_menu.addAction("刷新皮肤列表")
    reload_action.triggered.connect(window.reload_skins)
    return skin_menu


def _add_scale_submenu(menu: QMenu, window: "PetWindow"):
    scale_menu = menu.addMenu("缩放大小")
    scale_group = QActionGroup(window)
    scales = [
        ("35%", 0.35),
        ("50%", 0.50),
        ("65%", 0.65),
        ("75%", 0.75),
        ("100%（默认）", 1.00),
        ("125%", 1.25),
        ("150%", 1.50),
        ("200%", 2.00),
    ]
    for name, factor in scales:
        act = scale_menu.addAction(name)
        act.setCheckable(True)
        if abs(window.scale_factor - factor) < 0.04:
            act.setChecked(True)
        act.triggered.connect(lambda checked=False, f=factor: window.set_scale(f))
        scale_group.addAction(act)
    return scale_menu


def _add_pace_submenu(menu: QMenu, window: "PetWindow"):
    pace_menu = menu.addMenu("陪伴节律")
    pace_group = QActionGroup(window)
    paces = [
        ("静谧守候（推荐）", "quiet"),
        ("温柔从容", "gentle"),
        ("活泼巡逻", "active"),
    ]
    for label, level in paces:
        act = pace_menu.addAction(label)
        act.setCheckable(True)
        if getattr(window, "activity_level", "quiet") == level:
            act.setChecked(True)
        act.triggered.connect(lambda checked=False, lvl=level: window.set_activity_level(lvl))
        pace_group.addAction(act)
    return pace_menu


def _add_action_submenu(menu: QMenu, window: "PetWindow"):
    """Adds the dynamic action selector submenu with state lock and checkable status."""
    act_menu = menu.addMenu("动作点播")
    act_group = QActionGroup(window)

    if window.locked_action:
        unlock_act = act_menu.addAction("解除姿态锁定")
        unlock_act.triggered.connect(window.unlock_action)
        act_menu.addSeparator()

    if window.current_skin and window.current_skin.actions:
        actions_dict = window.current_skin.actions
        
        # 常用高频动作优先排列
        priority_order = [
            "idle", "cuddle_tail", "sharpen_knife", "alert_scout", "yawn_stretch",
            "edge_peek", "doze_off",
            "sit", "sleep", "walk",
            "headpat", "dizzy", "click", "greet", "drag",
            "fall", "land", "trans_sit", "trans_sleep"
        ]
        
        sorted_keys = []
        for p in priority_order:
            if p in actions_dict and p not in sorted_keys:
                sorted_keys.append(p)
        for k in sorted(actions_dict.keys()):
            if k not in sorted_keys:
                sorted_keys.append(k)

        for act_name in sorted_keys:
            label = ACTION_LABEL_MAP.get(act_name, act_name)
            act = act_menu.addAction(label)
            act.setCheckable(True)
            
            # 判断当前选中状态
            is_active = (window.state == act_name) or (getattr(window, "locked_action", None) == act_name)
            if is_active:
                act.setChecked(True)
                
            # 绑定显式点播槽函数
            act.triggered.connect(lambda checked=False, a=act_name: window.select_action(a))
            act_group.addAction(act)
    else:
        empty_act = act_menu.addAction("暂无可用动作")
        empty_act.setEnabled(False)

    return act_menu


def _add_screen_submenu(menu: QMenu, window: "PetWindow"):
    """动态多显示器切换子菜单 (支持任意主副显示器一键传送与感知)"""
    screens = QApplication.screens()
    if not screens:
        return None

    screen_menu = menu.addMenu("显示器切换")
    screen_group = QActionGroup(window)
    current_screen = window.get_current_screen()
    primary = QApplication.primaryScreen()

    for idx, scr in enumerate(screens):
        geom = scr.geometry()
        is_pri = (scr == primary)
        role = "主屏" if is_pri else f"副屏 {idx}"
        label = f"显示器 {idx + 1} · {role} ({geom.width()}×{geom.height()})"

        act = screen_menu.addAction(label)
        act.setCheckable(True)
        if scr == current_screen:
            act.setChecked(True)

        act.triggered.connect(lambda checked=False, s=scr: window.move_to_screen(s))
        screen_group.addAction(act)

    return screen_menu


def build_pet_context_menu(window: "PetWindow") -> QMenu:
    """Builds the comprehensive right-click context menu for PetWindow."""
    menu = QMenu(window)
    menu.setStyleSheet(MENU_STYLE)

    # 1. 动作点播
    _add_action_submenu(menu, window)

    # 2. 皮肤切换
    _add_skin_submenu(menu, window)

    # 3. 缩放大小
    _add_scale_submenu(menu, window)

    # 4. 陪伴节律
    _add_pace_submenu(menu, window)

    # 5. 显示器切换
    _add_screen_submenu(menu, window)

    menu.addSeparator()

    # 6. 台词气泡开关
    dialogue_act = menu.addAction("台词气泡")
    dialogue_act.setCheckable(True)
    dialogue_act.setChecked(window.dialogues_enabled)
    dialogue_act.triggered.connect(lambda checked=False: window.set_dialogues_enabled(checked))

    # 7. 摸摸红崽
    say_act = menu.addAction("摸摸红崽")
    say_act.triggered.connect(window.say_random_dialogue)

    # 8. 重置位置
    reset_act = menu.addAction("重置位置")
    reset_act.triggered.connect(window.reset_position)

    menu.addSeparator()

    # 9. 鼠标穿透开关
    ct_act = menu.addAction("鼠标穿透")
    ct_act.setCheckable(True)
    ct_act.setChecked(window.click_through)
    ct_act.triggered.connect(window.toggle_click_through)

    # 10. 退出
    exit_act = menu.addAction("退出")
    exit_act.triggered.connect(QApplication.instance().quit)

    return menu


def build_pet_tray_menu(window: "PetWindow", app: QApplication) -> QMenu:
    """Builds the system tray context menu, guaranteeing full control even in click-through mode."""
    tray_menu = QMenu()
    tray_menu.setStyleSheet(MENU_STYLE)

    show_act = tray_menu.addAction("显示/隐藏红崽")
    show_act.triggered.connect(lambda: window.setVisible(not window.isVisible()))

    reset_act = tray_menu.addAction("重置位置")
    reset_act.triggered.connect(window.reset_position)

    tray_menu.addSeparator()

    # Submenus: 托盘与右键菜单完整对齐
    _add_action_submenu(tray_menu, window)
    _add_skin_submenu(tray_menu, window)
    _add_scale_submenu(tray_menu, window)
    _add_pace_submenu(tray_menu, window)
    _add_screen_submenu(tray_menu, window)

    tray_menu.addSeparator()

    # 鼠标穿透开关（托盘为关键反向解除入口）
    ct_act = tray_menu.addAction("鼠标穿透")
    ct_act.setCheckable(True)
    ct_act.setChecked(window.click_through)
    ct_act.triggered.connect(window.toggle_click_through)

    dialogue_act = tray_menu.addAction("台词气泡")
    dialogue_act.setCheckable(True)
    dialogue_act.setChecked(window.dialogues_enabled)
    dialogue_act.triggered.connect(lambda checked=False: window.set_dialogues_enabled(checked))

    tray_menu.addSeparator()

    exit_act = tray_menu.addAction("退出")
    exit_act.triggered.connect(app.quit)

    return tray_menu
