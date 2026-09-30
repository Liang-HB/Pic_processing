import sys
import os
import shutil
import traceback
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QLineEdit, QListWidget, QListWidgetItem,
    QSplitter, QGroupBox, QScrollArea, QSizePolicy, QShortcut,
    QDialog, QAbstractItemView
)
from PyQt5.QtGui import (
    QPixmap, QKeySequence, QPainter, QIcon, QDesktopServices,
    QColor, QPen, QBrush, QFont, QWheelEvent
)
from PyQt5.QtCore import (
    Qt, QPoint, QTimer, QUrl, QRectF, QPointF, QSize
)


# ============================================================
# 图标工厂
# ============================================================
class IconFactory:
    @staticmethod
    def _make_icon(painter_func, size=24, color=QColor("#333333")):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter_func(painter, size)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def folder(color=QColor("#f0a020")):
        def draw(p, s):
            p.setBrush(QBrush(color))
            p.drawRoundedRect(QRectF(3, 7, s - 6, s - 11), 2, 2)
            p.drawRect(QRectF(3, 5, 9, 4))
        return IconFactory._make_icon(draw, 24)

    @staticmethod
    def prev(color=QColor("#1976d2")):
        def draw(p, s):
            p.drawLine(15, 6, 9, 12)
            p.drawLine(9, 12, 15, 18)
        return IconFactory._make_icon(draw, 24, color)

    @staticmethod
    def next(color=QColor("#1976d2")):
        def draw(p, s):
            p.drawLine(9, 6, 15, 12)
            p.drawLine(15, 12, 9, 18)
        return IconFactory._make_icon(draw, 24, color)

    @staticmethod
    def cut(color=QColor("#d32f2f")):
        def draw(p, s):
            p.drawEllipse(QPointF(8, 18), 3, 3)
            p.drawEllipse(QPointF(16, 18), 3, 3)
            p.drawLine(9, 15, 15, 5)
            p.drawLine(15, 15, 9, 5)
        return IconFactory._make_icon(draw, 24, color)

    @staticmethod
    def restore(color=QColor("#388e3c")):
        def draw(p, s):
            p.drawArc(QRectF(5, 5, 14, 14), 30 * 16, 300 * 16)
            p.drawLine(17, 6, 17, 11)
            p.drawLine(17, 6, 12, 6)
        return IconFactory._make_icon(draw, 24, color)

    @staticmethod
    def delete(color=QColor("#d32f2f")):
        def draw(p, s):
            p.drawLine(6, 8, 18, 8)
            p.drawLine(10, 8, 10, 5)
            p.drawLine(14, 8, 14, 5)
            p.drawRect(QRectF(8, 8, 8, 12))
            p.drawLine(11, 11, 11, 17)
            p.drawLine(13, 11, 13, 17)
        return IconFactory._make_icon(draw, 24, color)

    @staticmethod
    def reset(color=QColor("#7b1fa2")):
        def draw(p, s):
            p.drawEllipse(QRectF(5, 5, 11, 11))
            p.drawLine(14, 14, 19, 19)
            p.drawLine(8, 10, 13, 10)
            p.drawLine(10, 8, 10, 13)
        return IconFactory._make_icon(draw, 24, color)

    @staticmethod
    def open_folder(color=QColor("#f0a020")):
        def draw(p, s):
            p.setBrush(QBrush(color))
            p.drawRoundedRect(QRectF(3, 8, s - 6, s - 12), 2, 2)
            p.setBrush(Qt.NoBrush)
            p.drawLine(3, 9, 10, 9)
            p.drawLine(10, 9, 12, 11)
            p.drawLine(12, 11, 20, 11)
        return IconFactory._make_icon(draw, 24, color)

    @staticmethod
    def app_icon():
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setBrush(QBrush(QColor("#1976d2")))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(4, 4, 56, 56), 12, 12)
        p.setPen(QPen(QColor("#ffffff"), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(14, 16, 36, 28), 3, 3)
        p.drawLine(18, 38, 26, 28)
        p.drawLine(26, 28, 32, 34)
        p.drawLine(32, 34, 40, 24)
        p.drawLine(40, 24, 46, 38)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(42, 23), 3, 3)
        p.setPen(QPen(QColor("#4caf50"), 6))
        p.drawLine(36, 46, 42, 52)
        p.drawLine(42, 52, 54, 40)
        p.end()
        return QIcon(pixmap)


# ============================================================
# 兼容不同 PyQt5 版本的 QWheelEvent 构造
# ============================================================
def make_wheel_event(pos, global_pos, pixel_delta, angle_delta,
                     buttons, modifiers, phase, inverted):
    """不同 PyQt5 版本 QWheelEvent 构造参数略有差异，这里做兼容"""
    try:
        return QWheelEvent(
            pos, global_pos, pixel_delta, angle_delta,
            buttons, modifiers, phase, inverted
        )
    except TypeError:
        # 老版本 PyQt5 没有 phase / inverted
        try:
            return QWheelEvent(
                pos, global_pos, pixel_delta, angle_delta,
                buttons, modifiers, Qt.NoScrollPhase, False
            )
        except TypeError:
            # 更老的版本
            return QWheelEvent(pos, global_pos, pixel_delta, angle_delta,
                               buttons, modifiers)


# ============================================================
# 图片显示控件
# ============================================================
class ImageViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setStyleSheet("background: #fafafa;")

        self._pixmap = None
        self._scale = 1.0

        self._dragging = False
        self._drag_start_global = QPoint(0, 0)
        self._drag_start_h = 0
        self._drag_start_v = 0

        self._placeholder_text = "请先选择待处理图片文件夹"
        self.setCursor(Qt.OpenHandCursor)

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self._scale = 1.0
        self.update_display()

    def reset_view(self):
        self._scale = 1.0
        self.update_display()

    def clear_image(self):
        self._pixmap = None
        self._scale = 1.0
        self.resize(1, 1)
        self.update()

    def set_placeholder(self, text):
        self._placeholder_text = text
        if self._pixmap is None:
            self.update()

    def paintEvent(self, event):
        if self._pixmap is None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            cell = 20
            c1 = QColor("#f0f0f0")
            c2 = QColor("#e4e4e4")
            w = self.width()
            h = self.height()
            for y in range(0, h, cell):
                for x in range(0, w, cell):
                    color = c1 if ((x // cell) + (y // cell)) % 2 == 0 else c2
                    painter.fillRect(x, y, cell, cell, color)
            painter.setPen(QColor("#888888"))
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, self._placeholder_text)
            painter.end()
            return
        super().paintEvent(event)

    def _scroll_area(self):
        p = self.parentWidget()
        while p is not None:
            if isinstance(p, QScrollArea):
                return p
            p = p.parentWidget()
        return None

    def _base_size(self):
        sa = self._scroll_area()
        if sa is not None:
            vp = sa.viewport()
            base_w = max(vp.width(), 1)
            base_h = max(vp.height(), 1)
        else:
            base_w = max(self.width(), 1)
            base_h = max(self.height(), 1)
        return self._pixmap.scaled(
            base_w, base_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    def update_display(self):
        if self._pixmap is None or self._pixmap.isNull():
            return
        base = self._base_size()
        w = max(int(base.width() * self._scale), 1)
        h = max(int(base.height() * self._scale), 1)
        scaled = self._pixmap.scaled(
            w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(scaled)
        self.resize(scaled.size())
        self.update()

    def wheelEvent(self, event):
        if self._pixmap is None or self._pixmap.isNull():
            return
        sa = self._scroll_area()
        if sa is None:
            return
        viewport = sa.viewport()
        pos_in_viewport = viewport.mapFromGlobal(event.globalPos())
        viewer_pos_in_viewport = self.mapTo(viewport, QPoint(0, 0))
        mouse_in_viewer_x = pos_in_viewport.x() - viewer_pos_in_viewport.x()
        mouse_in_viewer_y = pos_in_viewport.y() - viewer_pos_in_viewport.y()
        old_w = max(self.width(), 1)
        old_h = max(self.height(), 1)
        ratio_x = mouse_in_viewer_x / old_w
        ratio_y = mouse_in_viewer_y / old_h
        delta = event.angleDelta().y()
        old_scale = self._scale
        if delta > 0:
            self._scale *= 1.15
        else:
            self._scale /= 1.15
        self._scale = max(0.1, min(self._scale, 20.0))
        if abs(self._scale - old_scale) < 1e-9:
            return
        base = self._base_size()
        new_w = max(int(base.width() * self._scale), 1)
        new_h = max(int(base.height() * self._scale), 1)
        scaled = self._pixmap.scaled(
            new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(scaled)
        self.resize(scaled.size())
        new_point_x = ratio_x * new_w
        new_point_y = ratio_y * new_h
        vp_w = viewport.width()
        vp_h = viewport.height()
        pad_x = max(0, (vp_w - new_w) // 2)
        pad_y = max(0, (vp_h - new_h) // 2)
        target_h = int(new_point_x + pad_x - pos_in_viewport.x())
        target_v = int(new_point_y + pad_y - pos_in_viewport.y())
        QTimer.singleShot(0, lambda: self._apply_scroll(target_h, target_v))
        event.accept()

    def _apply_scroll(self, h, v):
        sa = self._scroll_area()
        if sa is None:
            return
        sa.horizontalScrollBar().setValue(h)
        sa.verticalScrollBar().setValue(v)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._pixmap is not None:
            sa = self._scroll_area()
            if sa is None:
                return
            self._dragging = True
            self._drag_start_global = event.globalPos()
            self._drag_start_h = sa.horizontalScrollBar().value()
            self._drag_start_v = sa.verticalScrollBar().value()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return
        sa = self._scroll_area()
        if sa is None:
            return
        delta = event.globalPos() - self._drag_start_global
        sa.horizontalScrollBar().setValue(self._drag_start_h - delta.x())
        sa.verticalScrollBar().setValue(self._drag_start_v - delta.y())
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.OpenHandCursor)
            event.accept()


# ============================================================
# 图片预览对话框（支持上一张/下一张切换）
# ============================================================
class ImagePreviewDialog(QDialog):
    def __init__(self, image_paths, current_index, parent=None):
        super().__init__(parent)
        self.setWindowIcon(IconFactory.app_icon())
        self.resize(1000, 720)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.image_paths = list(image_paths)
        self.current_index = current_index
        self._thumb_built = False   # 标记缩略图是否已构建

        self._build_ui()
        self._setup_shortcuts()
        self.load_current_image()

    def _build_ui(self):
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "color: #333333; font-size: 14px; font-weight: bold; padding: 6px;"
        )

        self.viewer = ImageViewer()
        self.viewer.set_placeholder("无法加载该图片")
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.viewer)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet(
            "QScrollArea { border: 1px solid #d0d0d0; background: #fafafa; border-radius: 4px; }"
        )

        # 缩略图导航条
        self.thumb_list = QListWidget()
        self.thumb_list.setFlow(QListWidget.LeftToRight)
        self.thumb_list.setWrapping(False)
        self.thumb_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.thumb_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.thumb_list.setFixedHeight(86)
        self.thumb_list.setIconSize(QSize(64, 64))
        self.thumb_list.setSpacing(4)
        self.thumb_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: #ffffff;
                padding: 2px;
            }
            QListWidget::item {
                border-radius: 4px;
                padding: 2px;
            }
            QListWidget::item:selected {
                background: #1976d2;
            }
        """)
        self.thumb_list.itemClicked.connect(self.on_thumb_clicked)

        self.prev_btn = QPushButton("上一张 (←)")
        self.prev_btn.setIcon(IconFactory.prev())
        self.prev_btn.clicked.connect(self.prev_image)

        self.next_btn = QPushButton("下一张 (→)")
        self.next_btn.setIcon(IconFactory.next())
        self.next_btn.clicked.connect(self.next_image)

        self.reset_btn = QPushButton("重置缩放 (0)")
        self.reset_btn.setIcon(IconFactory.reset())
        self.reset_btn.clicked.connect(self.viewer.reset_view)

        self.open_folder_btn = QPushButton("打开所在文件夹")
        self.open_folder_btn.setIcon(IconFactory.open_folder())
        self.open_folder_btn.clicked.connect(self.open_in_folder)

        self.close_btn = QPushButton("关闭 (Esc)")
        self.close_btn.clicked.connect(self.close)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666666; padding: 4px;")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.open_folder_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.close_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.scroll_area, stretch=1)
        layout.addWidget(self.info_label)
        layout.addWidget(self.thumb_list)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.scroll_area.viewport().installEventFilter(self)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Left), self, activated=self.prev_image)
        QShortcut(QKeySequence(Qt.Key_Right), self, activated=self.next_image)
        QShortcut(QKeySequence(Qt.Key_0), self, activated=self.viewer.reset_view)
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_in_folder)

    def _build_thumbnails(self):
        """构建缩略图，注意：不传空字符串给 QListWidgetItem"""
        self.thumb_list.blockSignals(True)
        self.thumb_list.clear()
        for path in self.image_paths:
            try:
                pixmap = QPixmap(path)
                item = QListWidgetItem()          # 先构造，不带参数
                if not pixmap.isNull():
                    thumb = pixmap.scaled(
                        QSize(64, 64), Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    item.setIcon(QIcon(thumb))
                item.setToolTip(os.path.basename(path))
                self.thumb_list.addItem(item)
            except Exception:
                # 单张缩略图失败不影响整体
                item = QListWidgetItem()
                item.setToolTip(os.path.basename(path))
                self.thumb_list.addItem(item)
        self.thumb_list.blockSignals(False)
        self._thumb_built = True

    def load_current_image(self):
        if not (0 <= self.current_index < len(self.image_paths)):
            return

        path = self.image_paths[self.current_index]

        # 首次构建缩略图
        if not self._thumb_built or self.thumb_list.count() != len(self.image_paths):
            self._build_thumbnails()

        # 同步缩略图高亮（加保护，避免越界）
        if 0 <= self.current_index < self.thumb_list.count():
            self.thumb_list.blockSignals(True)
            self.thumb_list.setCurrentRow(self.current_index)
            item = self.thumb_list.item(self.current_index)
            if item is not None:
                self.thumb_list.scrollToItem(item, QListWidget.PositionAtCenter)
            self.thumb_list.blockSignals(False)

        # 加载图片
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.viewer.clear_image()
            self.viewer.set_placeholder("无法加载该图片")
            self.info_label.setText("")
        else:
            self.viewer.set_pixmap(pixmap)
            self.scroll_area.verticalScrollBar().setValue(0)
            self.scroll_area.horizontalScrollBar().setValue(0)

            try:
                size_str = self._format_size(os.path.getsize(path))
            except OSError:
                size_str = "未知大小"

            self.info_label.setText(
                f"{os.path.basename(path)}  |  "
                f"{pixmap.width()} × {pixmap.height()}  |  {size_str}"
            )

        self.setWindowTitle(f"查看图片 - {os.path.basename(path)}")
        self.title_label.setText(
            f"[{self.current_index + 1} / {len(self.image_paths)}]  "
            f"{os.path.basename(path)}"
        )

        self._update_nav_buttons()

    def _update_nav_buttons(self):
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_paths) - 1)

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_current_image()

    def on_thumb_clicked(self, item):
        if item is None:
            return
        row = self.thumb_list.row(item)
        if 0 <= row < len(self.image_paths) and row != self.current_index:
            self.current_index = row
            self.load_current_image()

    def _format_size(self, size):
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def open_in_folder(self):
        if not (0 <= self.current_index < len(self.image_paths)):
            return
        path = self.image_paths[self.current_index]
        folder = os.path.dirname(os.path.abspath(path))
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def eventFilter(self, obj, event):
        if obj is self.scroll_area.viewport() and event.type() == event.Wheel:
            new_event = make_wheel_event(
                self.viewer.mapFromGlobal(event.globalPos()),
                event.globalPos(),
                event.pixelDelta(),
                event.angleDelta(),
                event.buttons(),
                event.modifiers(),
                event.phase() if hasattr(event, "phase") else Qt.NoScrollPhase,
                event.inverted() if hasattr(event, "inverted") else False
            )
            self.viewer.wheelEvent(new_event)
            return True
        return super().eventFilter(obj, event)


# ============================================================
# 主窗口
# ============================================================
class ImagePicker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片挑选工具")
        self.setWindowIcon(IconFactory.app_icon())
        self.resize(1280, 800)

        self.img_exts = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")

        self.src_dir = ""
        self.dst_dir = ""
        self.image_list = []
        self.current_index = -1

        self.init_ui()
        self.setup_shortcuts()
        self.apply_style()

    def init_ui(self):
        top_group = self._build_top_bar()

        # ---------- 左侧 ----------
        self.pending_list = QListWidget()
        self.pending_list.itemClicked.connect(self.on_pending_item_clicked)

        self.pending_group = QGroupBox("待处理图片列表")
        pending_layout = QVBoxLayout()
        pending_layout.setContentsMargins(6, 6, 6, 6)
        pending_layout.addWidget(self.pending_list)

        self.open_src_btn = QPushButton("打开待处理文件夹")
        self.open_src_btn.setIcon(IconFactory.open_folder())
        self.open_src_btn.clicked.connect(lambda: self.open_folder(self.src_dir))
        pending_layout.addWidget(self.open_src_btn)

        self.pending_group.setLayout(pending_layout)

        # ---------- 右侧 ----------
        self.saved_list = QListWidget()
        self.saved_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.saved_list.itemDoubleClicked.connect(self.on_saved_item_double_clicked)
        self.saved_list.itemSelectionChanged.connect(self.update_counts)

        saved_layout = QVBoxLayout()
        saved_layout.setContentsMargins(6, 6, 6, 6)
        saved_layout.addWidget(self.saved_list)

        self.restore_btn = QPushButton("剪切回待处理文件夹 (R)")
        self.restore_btn.setIcon(IconFactory.restore())
        self.restore_btn.clicked.connect(self.restore_selected_images)

        self.batch_delete_btn = QPushButton("批量删除选中图片 (Del)")
        self.batch_delete_btn.setIcon(IconFactory.delete())
        self.batch_delete_btn.clicked.connect(self.batch_delete_images)

        self.open_dst_btn = QPushButton("打开保存文件夹")
        self.open_dst_btn.setIcon(IconFactory.open_folder())
        self.open_dst_btn.clicked.connect(lambda: self.open_folder(self.dst_dir))

        saved_layout.addWidget(self.restore_btn)
        saved_layout.addWidget(self.batch_delete_btn)
        saved_layout.addWidget(self.open_dst_btn)

        self.saved_group = QGroupBox("已保存图片列表")
        self.saved_group.setLayout(saved_layout)

        # ---------- 中间 ----------
        self.image_viewer = ImageViewer()
        self.image_viewer.set_placeholder(
            "请先选择待处理图片文件夹\n\n"
            "滚轮缩放 · 按住左键拖动 · 空格剪切 · ← → 切换"
        )

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_viewer)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet(
            "QScrollArea { border: 1px solid #d0d0d0; background: #fafafa; border-radius: 4px; }"
        )
        self.scroll_area.setMinimumSize(500, 400)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #555555; padding: 4px; font-size: 13px;")

        self.prev_btn = QPushButton("上一张")
        self.prev_btn.setIcon(IconFactory.prev())
        self.prev_btn.clicked.connect(self.prev_image)

        self.cut_btn = QPushButton("剪切到目标文件夹")
        self.cut_btn.setIcon(IconFactory.cut())
        self.cut_btn.clicked.connect(self.cut_image)

        self.next_btn = QPushButton("下一张")
        self.next_btn.setIcon(IconFactory.next())
        self.next_btn.clicked.connect(self.next_image)

        self.reset_btn = QPushButton("重置缩放")
        self.reset_btn.setIcon(IconFactory.reset())
        self.reset_btn.clicked.connect(self.image_viewer.reset_view)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.cut_btn)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.reset_btn)

        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(6, 6, 6, 6)
        center_layout.addWidget(self.scroll_area, stretch=1)
        center_layout.addWidget(self.info_label)
        center_layout.addLayout(btn_layout)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.pending_group)
        splitter.addWidget(center_widget)
        splitter.addWidget(self.saved_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        splitter.setChildrenCollapsible(False)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(top_group)
        layout.addWidget(splitter, stretch=1)
        self.setLayout(layout)

        self.scroll_area.viewport().installEventFilter(self)

        for btn in (self.prev_btn, self.cut_btn, self.next_btn, self.reset_btn,
                    self.restore_btn, self.batch_delete_btn,
                    self.open_src_btn, self.open_dst_btn):
            btn.setFocusPolicy(Qt.NoFocus)

        self.update_buttons()
        self.update_counts()

    def _build_top_bar(self):
        group = QGroupBox("文件夹设置")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        src_layout = QHBoxLayout()
        src_icon = QLabel()
        src_icon.setPixmap(IconFactory.folder().pixmap(20, 20))
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText("待处理图片文件夹路径")
        self.src_edit.setReadOnly(True)
        src_btn = QPushButton("选择待处理文件夹")
        src_btn.setIcon(IconFactory.folder())
        src_btn.clicked.connect(self.choose_src_dir)
        src_layout.addWidget(src_icon)
        src_layout.addWidget(self.src_edit, stretch=1)
        src_layout.addWidget(src_btn)

        dst_layout = QHBoxLayout()
        dst_icon = QLabel()
        dst_icon.setPixmap(IconFactory.folder(QColor("#4caf50")).pixmap(20, 20))
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText("剪切保存文件夹路径")
        self.dst_edit.setReadOnly(True)
        dst_btn = QPushButton("选择保存文件夹")
        dst_btn.setIcon(IconFactory.folder(QColor("#4caf50")))
        dst_btn.clicked.connect(self.choose_dst_dir)
        dst_layout.addWidget(dst_icon)
        dst_layout.addWidget(self.dst_edit, stretch=1)
        dst_layout.addWidget(dst_btn)

        layout.addLayout(src_layout)
        layout.addLayout(dst_layout)
        group.setLayout(layout)
        return group

    def apply_style(self):
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
                font-size: 13px;
                color: #333333;
            }
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background: #ffffff;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #1976d2;
            }
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: #e8f0fe;
                border-color: #1976d2;
            }
            QPushButton:pressed {
                background: #d0e1f9;
            }
            QPushButton:disabled {
                background: #f0f0f0;
                color: #aaaaaa;
                border-color: #e0e0e0;
            }
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 5px 8px;
                background: #fafafa;
                color: #555555;
            }
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: #ffffff;
                padding: 2px;
            }
            QListWidget::item {
                padding: 5px 8px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background: #e8f0fe;
            }
            QListWidget::item:selected {
                background: #1976d2;
                color: #ffffff;
            }
            QScrollBar:vertical {
                background: #f5f5f5;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #f5f5f5;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                border-radius: 5px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self, activated=self.cut_image)
        QShortcut(QKeySequence(Qt.Key_Left), self, activated=self.prev_image)
        QShortcut(QKeySequence(Qt.Key_Right), self, activated=self.next_image)
        QShortcut(QKeySequence(Qt.Key_0), self, activated=self.image_viewer.reset_view)
        QShortcut(QKeySequence(Qt.Key_R), self, activated=self.restore_selected_images)
        QShortcut(QKeySequence(Qt.Key_Delete), self, activated=self.batch_delete_images)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_current_folder)

    def open_folder(self, folder):
        if not folder or not os.path.isdir(folder):
            QMessageBox.information(self, "提示", "文件夹尚未选择或不存在")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def open_current_folder(self):
        self.open_folder(self.src_dir)

    def update_counts(self):
        pending_count = len(self.image_list)
        self.pending_group.setTitle(f"待处理图片列表（共 {pending_count} 张）")

        saved_count = self.saved_list.count()
        selected_count = len(self.saved_list.selectedItems())
        if selected_count > 0:
            self.saved_group.setTitle(
                f"已保存图片列表（共 {saved_count} 张，已选 {selected_count} 张）"
            )
        else:
            self.saved_group.setTitle(f"已保存图片列表（共 {saved_count} 张）")

    def eventFilter(self, obj, event):
        if obj is self.scroll_area.viewport() and event.type() == event.Wheel:
            new_event = make_wheel_event(
                self.image_viewer.mapFromGlobal(event.globalPos()),
                event.globalPos(),
                event.pixelDelta(),
                event.angleDelta(),
                event.buttons(),
                event.modifiers(),
                event.phase() if hasattr(event, "phase") else Qt.NoScrollPhase,
                event.inverted() if hasattr(event, "inverted") else False
            )
            self.image_viewer.wheelEvent(new_event)
            return True
        return super().eventFilter(obj, event)

    def choose_src_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择待处理图片文件夹")
        if folder:
            self.src_dir = folder
            self.src_edit.setText(folder)
            self.load_images()

    def choose_dst_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择剪切保存文件夹")
        if folder:
            self.dst_dir = folder
            self.dst_edit.setText(folder)
            self.load_saved_images()
            self.update_buttons()

    def load_images(self):
        self.image_list = []
        for name in sorted(os.listdir(self.src_dir)):
            if name.lower().endswith(self.img_exts):
                self.image_list.append(os.path.join(self.src_dir, name))

        self.refresh_pending_list()

        if self.image_list:
            self.current_index = 0
            self.show_image()
        else:
            self.current_index = -1
            self.image_viewer.clear_image()
            self.image_viewer.set_placeholder("该文件夹中没有图片")
            self.info_label.setText("")
        self.update_buttons()
        self.update_counts()

    def refresh_pending_list(self):
        self.pending_list.blockSignals(True)
        self.pending_list.clear()
        for path in self.image_list:
            self.pending_list.addItem(os.path.basename(path))
        self.pending_list.blockSignals(False)

        if 0 <= self.current_index < self.pending_list.count():
            self.pending_list.setCurrentRow(self.current_index)

        self.update_counts()

    def load_saved_images(self):
        self.saved_list.clear()
        if self.dst_dir and os.path.isdir(self.dst_dir):
            for name in sorted(os.listdir(self.dst_dir)):
                if name.lower().endswith(self.img_exts):
                    self.saved_list.addItem(name)
        self.update_counts()

    def _get_saved_paths(self):
        paths = []
        if self.dst_dir and os.path.isdir(self.dst_dir):
            for i in range(self.saved_list.count()):
                name = self.saved_list.item(i).text()
                paths.append(os.path.join(self.dst_dir, name))
        return paths

    def on_pending_item_clicked(self, item):
        row = self.pending_list.row(item)
        if 0 <= row < len(self.image_list):
            self.current_index = row
            self.show_image()

    def on_saved_item_double_clicked(self, item):
        """双击右侧列表：打开预览对话框，出错时不闪退"""
        try:
            if not self.dst_dir:
                return

            paths = self._get_saved_paths()
            if not paths:
                return

            clicked_name = item.text()
            clicked_path = os.path.join(self.dst_dir, clicked_name)

            try:
                start_index = paths.index(clicked_path)
            except ValueError:
                QMessageBox.warning(self, "提示", f"文件不存在：\n{clicked_path}")
                self.load_saved_images()
                return

            dlg = ImagePreviewDialog(paths, start_index, self)
            dlg.exec_()

            self.load_saved_images()

        except Exception as e:
            # 捕获所有异常，弹提示而不是让程序崩溃
            err_detail = traceback.format_exc()
            QMessageBox.critical(
                self, "错误",
                f"打开预览时出错：\n{e}\n\n详细信息：\n{err_detail[:1500]}"
            )

    def restore_selected_images(self):
        selected_items = self.saved_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先在右侧列表选中要移回的图片")
            return
        if not self.src_dir:
            QMessageBox.warning(self, "提示", "请先选择待处理图片文件夹")
            return
        if not self.dst_dir:
            QMessageBox.warning(self, "提示", "请先选择剪切保存文件夹")
            return

        file_names = [item.text() for item in selected_items]

        reply = QMessageBox.question(
            self, "确认",
            f"确定把选中的 {len(file_names)} 张图片剪切回待处理文件夹吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        success = 0
        failed = []

        for name in file_names:
            src_path = os.path.join(self.dst_dir, name)
            if not os.path.exists(src_path):
                failed.append(f"{name}（源文件不存在）")
                continue

            dst_path = os.path.join(self.src_dir, name)

            if os.path.exists(dst_path):
                base, ext = os.path.splitext(name)
                i = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(self.src_dir, f"{base}_restored{i}{ext}")
                    i += 1

            try:
                shutil.move(src_path, dst_path)
                self.image_list.append(dst_path)
                success += 1
            except Exception as e:
                failed.append(f"{name}（{e}）")

        self.image_list.sort()
        self.refresh_pending_list()
        self.load_saved_images()

        if self.current_index < 0 and self.image_list:
            self.current_index = 0
            self.show_image()
        else:
            self.pending_list.blockSignals(True)
            if 0 <= self.current_index < self.pending_list.count():
                self.pending_list.setCurrentRow(self.current_index)
            self.pending_list.blockSignals(False)
            self.update_buttons()

        self.update_counts()

        msg = f"成功移回 {success} 张图片。"
        if failed:
            msg += f"\n\n失败 {len(failed)} 张：\n" + "\n".join(failed[:10])
            if len(failed) > 10:
                msg += f"\n...（共 {len(failed)} 张失败）"
        QMessageBox.information(self, "完成", msg)

    def batch_delete_images(self):
        selected_items = self.saved_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先在右侧列表选中要删除的图片")
            return

        file_names = [item.text() for item in selected_items]

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要永久删除选中的 {len(file_names)} 张图片吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        success = 0
        failed = []

        for name in file_names:
            path = os.path.join(self.dst_dir, name)
            if not os.path.exists(path):
                failed.append(f"{name}（文件不存在）")
                continue
            try:
                os.remove(path)
                success += 1
            except Exception as e:
                failed.append(f"{name}（{e}）")

        self.load_saved_images()

        msg = f"成功删除 {success} 张图片。"
        if failed:
            msg += f"\n\n失败 {len(failed)} 张：\n" + "\n".join(failed[:10])
            if len(failed) > 10:
                msg += f"\n...（共 {len(failed)} 张失败）"
        QMessageBox.information(self, "完成", msg)

    def show_image(self):
        if not (0 <= self.current_index < len(self.image_list)):
            return
        path = self.image_list[self.current_index]
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_viewer.clear_image()
            self.image_viewer.set_placeholder("无法加载该图片")
            self.info_label.setText("")
        else:
            self.image_viewer.set_pixmap(pixmap)
            self.scroll_area.verticalScrollBar().setValue(0)
            self.scroll_area.horizontalScrollBar().setValue(0)

            size_str = self._format_size(os.path.getsize(path))
            self.info_label.setText(
                f"[{self.current_index + 1} / {len(self.image_list)}]  "
                f"{os.path.basename(path)}  |  "
                f"{pixmap.width()} × {pixmap.height()}  |  {size_str}"
            )

        self.pending_list.blockSignals(True)
        self.pending_list.setCurrentRow(self.current_index)
        self.pending_list.blockSignals(False)

        self.update_buttons()

    def _format_size(self, size):
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.show_image()

    def cut_image(self):
        if self.current_index < 0:
            QMessageBox.warning(self, "提示", "没有可处理的图片")
            return
        if not self.dst_dir:
            QMessageBox.warning(self, "提示", "请先选择剪切保存文件夹")
            return

        src_path = self.image_list[self.current_index]
        file_name = os.path.basename(src_path)
        dst_path = os.path.join(self.dst_dir, file_name)

        if os.path.exists(dst_path):
            base, ext = os.path.splitext(file_name)
            i = 1
            while os.path.exists(dst_path):
                dst_path = os.path.join(self.dst_dir, f"{base}_{i}{ext}")
                i += 1

        try:
            shutil.move(src_path, dst_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"剪切失败：\n{e}")
            return

        self.image_list.pop(self.current_index)

        if self.current_index >= len(self.image_list):
            self.current_index = len(self.image_list) - 1

        self.refresh_pending_list()
        self.load_saved_images()

        if self.image_list:
            self.show_image()
        else:
            self.current_index = -1
            self.image_viewer.clear_image()
            self.image_viewer.set_placeholder("所有图片已处理完毕")
            self.info_label.setText("")
            self.pending_list.clear()
            self.update_buttons()
            self.update_counts()

    def update_buttons(self):
        has_img = len(self.image_list) > 0 and self.current_index >= 0
        self.prev_btn.setEnabled(has_img and self.current_index > 0)
        self.next_btn.setEnabled(has_img and self.current_index < len(self.image_list) - 1)
        self.cut_btn.setEnabled(has_img and bool(self.dst_dir))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_viewer._pixmap is not None and abs(self.image_viewer._scale - 1.0) < 1e-6:
            self.image_viewer.update_display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(IconFactory.app_icon())
    window = ImagePicker()
    window.show()
    sys.exit(app.exec_())