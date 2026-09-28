import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QLineEdit, QListWidget, QListWidgetItem,
    QSplitter, QGroupBox, QScrollArea, QSizePolicy, QShortcut,
    QDialog, QDialogButtonBox, QAbstractItemView
)
from PyQt5.QtGui import QPixmap, QKeySequence, QWheelEvent
from PyQt5.QtCore import Qt, QPoint, QTimer


class ImageViewer(QLabel):
    """放在 QScrollArea 内的图片控件：
       - 滚轮以鼠标位置为焦点缩放（精确、无偏移）
       - 按住鼠标左键拖动平移（顺滑、无累积误差）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #f5f5f5;")
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self._pixmap = None
        self._scale = 1.0

        self._dragging = False
        self._drag_start_global = QPoint(0, 0)
        self._drag_start_h = 0
        self._drag_start_v = 0

        self.setCursor(Qt.OpenHandCursor)

    # ---------- 外部接口 ----------
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
        self.clear()
        self.resize(1, 1)

    # ---------- 工具方法 ----------
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

    # ---------- 渲染 ----------
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

    # ---------- 滚轮：以鼠标为焦点缩放 ----------
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

    # ---------- 鼠标拖拽平移 ----------
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


class ImagePreviewDialog(QDialog):
    """双击图片后弹出的预览对话框，支持滚轮缩放和拖拽平移"""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"查看图片 - {os.path.basename(image_path)}")
        self.resize(900, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.image_path = image_path

        # 图片显示区
        self.viewer = ImageViewer()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.viewer)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet(
            "QScrollArea { border: 1px solid #aaa; background: #f5f5f5; }"
        )

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.viewer.set_pixmap(pixmap)

        # 底部按钮
        self.reset_btn = QPushButton("重置缩放 (0)")
        self.reset_btn.clicked.connect(self.viewer.reset_view)

        self.close_btn = QPushButton("关闭 (Esc)")
        self.close_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.close_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area, stretch=1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # 滚轮事件转发
        self.scroll_area.viewport().installEventFilter(self)

        # 快捷键
        QShortcut(QKeySequence(Qt.Key_0), self, activated=self.viewer.reset_view)
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.close)

    def eventFilter(self, obj, event):
        if obj is self.scroll_area.viewport() and event.type() == event.Wheel:
            new_event = QWheelEvent(
                self.viewer.mapFromGlobal(event.globalPos()),
                event.globalPos(),
                event.pixelDelta(),
                event.angleDelta(),
                event.buttons(),
                event.modifiers(),
                event.phase(),
                event.inverted()
            )
            self.viewer.wheelEvent(new_event)
            return True
        return super().eventFilter(obj, event)


class ImagePicker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片挑选工具")
        self.resize(1200, 750)

        self.img_exts = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")

        self.src_dir = ""
        self.dst_dir = ""
        self.image_list = []
        self.current_index = -1

        self.init_ui()
        self.setup_shortcuts()

    def init_ui(self):
        # ---------- 顶部：文件夹选择 ----------
        src_layout = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText("待处理图片文件夹路径")
        self.src_edit.setReadOnly(True)
        src_btn = QPushButton("选择待处理文件夹")
        src_btn.clicked.connect(self.choose_src_dir)
        src_layout.addWidget(self.src_edit)
        src_layout.addWidget(src_btn)

        dst_layout = QHBoxLayout()
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText("剪切保存文件夹路径")
        self.dst_edit.setReadOnly(True)
        dst_btn = QPushButton("选择保存文件夹")
        dst_btn.clicked.connect(self.choose_dst_dir)
        dst_layout.addWidget(self.dst_edit)
        dst_layout.addWidget(dst_btn)

        top_layout = QVBoxLayout()
        top_layout.addLayout(src_layout)
        top_layout.addLayout(dst_layout)

        # ---------- 左侧：待处理图片列表 ----------
        self.pending_list = QListWidget()
        self.pending_list.itemClicked.connect(self.on_pending_item_clicked)

        self.pending_group = QGroupBox("待处理图片列表")
        pending_layout = QVBoxLayout()
        pending_layout.addWidget(self.pending_list)
        self.pending_group.setLayout(pending_layout)

        # ---------- 右侧：已保存图片列表 ----------
        self.saved_list = QListWidget()
        # 支持多选（批量处理）
        self.saved_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # 双击右侧项：弹出大图查看对话框
        self.saved_list.itemDoubleClicked.connect(self.on_saved_item_double_clicked)

        saved_layout = QVBoxLayout()
        saved_layout.addWidget(self.saved_list)

        # 右侧底部按钮
        self.restore_btn = QPushButton("剪切回待处理文件夹 (R)")
        self.restore_btn.clicked.connect(self.restore_selected_images)

        self.batch_restore_btn = QPushButton("批量剪切回待处理")
        self.batch_restore_btn.clicked.connect(self.restore_selected_images)

        self.batch_delete_btn = QPushButton("批量删除选中图片")
        self.batch_delete_btn.clicked.connect(self.batch_delete_images)

        saved_layout.addWidget(self.restore_btn)
        saved_layout.addWidget(self.batch_restore_btn)
        saved_layout.addWidget(self.batch_delete_btn)

        self.saved_group = QGroupBox("已保存图片列表")
        self.saved_group.setLayout(saved_layout)

        # ---------- 中间：QScrollArea 包裹图片 ----------
        self.image_viewer = ImageViewer()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_viewer)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #aaa; background: #f5f5f5; }")
        self.scroll_area.setMinimumSize(500, 400)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)

        self.prev_btn = QPushButton("上一张 (←)")
        self.cut_btn = QPushButton("剪切到目标文件夹 (空格)")
        self.next_btn = QPushButton("下一张 (→)")
        self.reset_btn = QPushButton("重置缩放 (0)")
        self.prev_btn.clicked.connect(self.prev_image)
        self.cut_btn.clicked.connect(self.cut_image)
        self.next_btn.clicked.connect(self.next_image)
        self.reset_btn.clicked.connect(self.image_viewer.reset_view)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.cut_btn)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.reset_btn)

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.scroll_area, stretch=1)
        center_layout.addWidget(self.info_label)
        center_layout.addLayout(btn_layout)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # ---------- 主体：左列表 | 中间显示 | 右列表 ----------
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.pending_group)
        splitter.addWidget(center_widget)
        splitter.addWidget(self.saved_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)

        # ---------- 总布局 ----------
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(splitter, stretch=1)
        self.setLayout(layout)

        # 滚轮事件转发
        self.scroll_area.viewport().installEventFilter(self)

        # 按钮焦点策略
        for btn in (self.prev_btn, self.cut_btn, self.next_btn, self.reset_btn,
                    self.restore_btn, self.batch_restore_btn, self.batch_delete_btn):
            btn.setFocusPolicy(Qt.NoFocus)

        self.update_buttons()
        self.update_counts()

    # ================= 全局快捷键 =================
    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self, activated=self.cut_image)
        QShortcut(QKeySequence(Qt.Key_Left), self, activated=self.prev_image)
        QShortcut(QKeySequence(Qt.Key_Right), self, activated=self.next_image)
        QShortcut(QKeySequence(Qt.Key_0), self, activated=self.image_viewer.reset_view)
        QShortcut(QKeySequence(Qt.Key_R), self, activated=self.restore_selected_images)
        QShortcut(QKeySequence(Qt.Key_Delete), self, activated=self.batch_delete_images)

    # ================= 数量统计 =================
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

    # ================= 事件过滤器：转发滚轮事件 =================
    def eventFilter(self, obj, event):
        if obj is self.scroll_area.viewport() and event.type() == event.Wheel:
            new_event = QWheelEvent(
                self.image_viewer.mapFromGlobal(event.globalPos()),
                event.globalPos(),
                event.pixelDelta(),
                event.angleDelta(),
                event.buttons(),
                event.modifiers(),
                event.phase(),
                event.inverted()
            )
            self.image_viewer.wheelEvent(new_event)
            return True
        return super().eventFilter(obj, event)

    # ================= 文件夹选择 =================
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

    # ================= 加载待处理图片 =================
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
            self.info_label.setText("该文件夹中没有图片")
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

    # ================= 加载已保存图片列表 =================
    def load_saved_images(self):
        self.saved_list.clear()
        if self.dst_dir and os.path.isdir(self.dst_dir):
            for name in sorted(os.listdir(self.dst_dir)):
                if name.lower().endswith(self.img_exts):
                    self.saved_list.addItem(name)
        self.update_counts()

    # ================= 点击左侧列表跳转 =================
    def on_pending_item_clicked(self, item):
        row = self.pending_list.row(item)
        if 0 <= row < len(self.image_list):
            self.current_index = row
            self.show_image()

    # ================= 双击右侧项：弹出预览对话框 =================
    def on_saved_item_double_clicked(self, item):
        if not self.dst_dir:
            return
        image_path = os.path.join(self.dst_dir, item.text())
        if not os.path.exists(image_path):
            QMessageBox.warning(self, "提示", f"文件不存在：\n{image_path}")
            self.load_saved_images()
            return

        dlg = ImagePreviewDialog(image_path, self)
        dlg.exec_()

    # ================= 批量剪切回待处理文件夹 =================
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

            # 避免同名覆盖
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

        # 排序待处理列表
        self.image_list.sort()

        self.refresh_pending_list()
        self.load_saved_images()

        # 如果当前没有显示图片，显示第一张
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

        # 结果提示
        msg = f"成功移回 {success} 张图片。"
        if failed:
            msg += f"\n\n失败 {len(failed)} 张：\n" + "\n".join(failed[:10])
            if len(failed) > 10:
                msg += f"\n...（共 {len(failed)} 张失败）"
        QMessageBox.information(self, "完成", msg)

    # ================= 批量删除右侧选中图片 =================
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

    # ================= 显示当前图片 =================
    def show_image(self):
        if not (0 <= self.current_index < len(self.image_list)):
            return
        path = self.image_list[self.current_index]
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_viewer.clear_image()
            self.info_label.setText("无法加载该图片")
        else:
            self.image_viewer.set_pixmap(pixmap)
            self.scroll_area.verticalScrollBar().setValue(0)
            self.scroll_area.horizontalScrollBar().setValue(0)

        self.info_label.setText(
            f"[{self.current_index + 1} / {len(self.image_list)}]  {os.path.basename(path)}"
        )

        self.pending_list.blockSignals(True)
        self.pending_list.setCurrentRow(self.current_index)
        self.pending_list.blockSignals(False)

        self.update_buttons()

    # ================= 上一张 / 下一张 =================
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.show_image()

    # ================= 剪切图片（待处理 → 保存） =================
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
            self.info_label.setText("所有图片已处理完毕")
            self.pending_list.clear()
            self.update_buttons()
            self.update_counts()

    # ================= 按钮状态更新 =================
    def update_buttons(self):
        has_img = len(self.image_list) > 0 and self.current_index >= 0
        self.prev_btn.setEnabled(has_img and self.current_index > 0)
        self.next_btn.setEnabled(has_img and self.current_index < len(self.image_list) - 1)
        self.cut_btn.setEnabled(has_img and bool(self.dst_dir))

    # ================= 窗口大小变化时重新适配图片 =================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_viewer._pixmap is not None and abs(self.image_viewer._scale - 1.0) < 1e-6:
            self.image_viewer.update_display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImagePicker()
    window.show()
    sys.exit(app.exec_())