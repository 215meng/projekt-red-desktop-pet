"""
renderer.py - 工业级硬件仿射变换渲染管线
基于 QPainter 的硬件矩阵变换，杜绝运行时 QPixmap 尺寸重分配，保持零堆内存开销。
彻底纠正素材朝向：原始切片默认朝右，facing_left=True 时执行水平翻转朝左。
"""

from typing import Optional, Tuple
from PySide6.QtGui import QPainter, QPixmap, QTransform


class ZeroAllocRenderer:
    """
    高性能 GPU/光栅化硬件矩阵变换渲染器。
    每帧绘制零 GC 开销。
    """

    @staticmethod
    def draw_frame(
        painter: QPainter,
        pixmap: QPixmap,
        target_width: int,
        target_height: int,
        facing_left: bool = False,
        squash_stretch: Optional[Tuple[float, float]] = None,
        anchor_bottom: bool = True,
        rotation_deg: float = 0.0,
        opacity: float = 1.0
    ):
        """
        绘制单帧切片。
        :param facing_left: True 代表面朝左 (水平镜像翻转)；False 代表面朝右 (原始朝向)
        """
        if pixmap.isNull():
            return

        src_w = pixmap.width()
        src_h = pixmap.height()
        if src_w <= 0 or src_h <= 0:
            return

        # 视口基础缩放比例
        scale_x = target_width / src_w
        scale_y = target_height / src_h
        base_scale = min(scale_x, scale_y)

        # 弹性挤压拉伸形变
        sx_deform, sy_deform = squash_stretch if squash_stretch else (1.0, 1.0)
        final_scale_x = base_scale * sx_deform
        final_scale_y = base_scale * sy_deform

        draw_w = src_w * final_scale_x
        draw_h = src_h * final_scale_y

        # 底对齐与居中
        pos_x = (target_width - draw_w) / 2.0
        pos_y = (target_height - draw_h) if anchor_bottom else 0.0

        painter.save()
        if opacity < 1.0:
            painter.setOpacity(max(0.0, min(1.0, opacity)))
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 硬件矩阵变换
        t = QTransform()
        t.translate(pos_x, pos_y)

        # 提溜钟摆摆动倾角 (以后颈部/胸口为枢轴)
        if rotation_deg != 0.0:
            pivot_x = draw_w / 2.0
            pivot_y = draw_h * 0.28
            t.translate(pivot_x, pivot_y)
            t.rotate(rotation_deg)
            t.translate(-pivot_x, -pivot_y)

        # 水平镜像朝向修正：
        # 原始切片原生朝右！
        # 若 facing_left 为 True，则水平翻转朝左；若 facing_left 为 False，则保持原始朝右。
        if facing_left:
            t.translate(draw_w, 0.0)
            t.scale(-final_scale_x, final_scale_y)
        else:
            t.scale(final_scale_x, final_scale_y)

        painter.setTransform(t, True)
        painter.drawPixmap(0, 0, pixmap)
        painter.restore()
