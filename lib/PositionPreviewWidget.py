# lib/PositionPreviewWidget.py
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent, QPaintEvent, QCursor
from PySide6.QtCore import Qt, Slot, Signal, QPoint, QRect, QSize, QMargins, QLineF

# ハンドルの種類
HANDLE_NONE = 0
HANDLE_TOP_LEFT = 1
HANDLE_TOP_RIGHT = 2
HANDLE_BOTTOM_LEFT = 3
HANDLE_BOTTOM_RIGHT = 4
HANDLE_MOVE = 5

class PositionPreviewWidget(QWidget):
    """オーバーレイ位置とサイズを視覚的に操作するためのプレビューウィジェット"""
    overlayGeometryChanged = Signal() # 位置またはサイズが変わったことを通知
    HANDLE_SIZE = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitor_aspect_ratio = 16 / 9
        self._monitor_rect = QRect()
        self._overlay_rect = QRect()
        self._overlay_relative_pos = QPoint(0, 0)
        self._overlay_actual_width = 50
        self._overlay_actual_height = 50
        self._overlay_aspect_ratio = 1.0
        self._monitor_width_px = 1920
        self._monitor_height_px = 1080
        self._dragging_mode = HANDLE_NONE
        self._drag_start_pos = QPoint()
        self._drag_start_rect = QRect()
        self.setMinimumSize(100, 50)
        self.setMouseTracking(True)

    def setMonitorGeometry(self, width: int, height: int):
        if width > 0 and height > 0:
            # 内部状態が実際に変わったかチェック
            changed = (self._monitor_width_px != width or self._monitor_height_px != height)
            if changed:
                self._monitor_width_px = width
                self._monitor_height_px = height
                self._monitor_aspect_ratio = width / height
                self._calculate_rects()
                self.update()

    def setOverlayInfo(self, rel_x: int, rel_y: int, overlay_actual_w: int, overlay_actual_h: int):
        new_pos = QPoint(rel_x, rel_y)
        new_w = max(1, overlay_actual_w)
        new_h = max(1, overlay_actual_h)
        pos_changed = (self._overlay_relative_pos != new_pos)
        size_changed = (self._overlay_actual_width != new_w or self._overlay_actual_height != new_h)

        if pos_changed: self._overlay_relative_pos = new_pos
        if size_changed:
            self._overlay_actual_width = new_w
            self._overlay_actual_height = new_h
            if self._overlay_actual_height > 0:
                self._overlay_aspect_ratio = self._overlay_actual_width / self._overlay_actual_height
            else:
                self._overlay_aspect_ratio = 1.0

        if pos_changed or size_changed:
            self._calculate_rects()
            self.update()

    def getOverlayRelativePos(self) -> QPoint:
        return self._overlay_relative_pos

    def getOverlayActualSize(self) -> QSize:
        return QSize(self._overlay_actual_width, self._overlay_actual_height)

    def _calculate_rects(self):
        widget_rect = self.rect().adjusted(1, 1, -1, -1)
        if widget_rect.width() <= 0 or widget_rect.height() <= 0: return

        widget_aspect_ratio = widget_rect.width() / widget_rect.height()

        if widget_aspect_ratio > self._monitor_aspect_ratio:
            h = widget_rect.height()
            w = int(round(h * self._monitor_aspect_ratio)) # round使用
            x = widget_rect.x() + (widget_rect.width() - w) // 2
            y = widget_rect.y()
        else:
            w = widget_rect.width()
            h = int(round(w / self._monitor_aspect_ratio)) # round使用
            x = widget_rect.x()
            y = widget_rect.y() + (widget_rect.height() - h) // 2
        self._monitor_rect = QRect(x, y, w, h)

        if self._monitor_width_px > 0 and self._monitor_height_px > 0 and w > 0 and h > 0:
            # round を使って丸め誤差を軽減
            rel_w_ratio = self._overlay_actual_width / self._monitor_width_px
            rel_h_ratio = self._overlay_actual_height / self._monitor_height_px
            preview_w = int(round(w * rel_w_ratio))
            preview_h = int(round(h * rel_h_ratio))
            preview_w = max(self.HANDLE_SIZE * 2 + 2, preview_w)
            preview_h = max(self.HANDLE_SIZE * 2 + 2, preview_h)

            rel_x_ratio = self._overlay_relative_pos.x() / self._monitor_width_px
            rel_y_ratio = self._overlay_relative_pos.y() / self._monitor_height_px
            preview_x = self._monitor_rect.x() + int(round(w * rel_x_ratio))
            preview_y = self._monitor_rect.y() + int(round(h * rel_y_ratio))

            # 位置調整を厳密に (右端、下端)
            if preview_x + preview_w > self._monitor_rect.right():
                 preview_x = self._monitor_rect.right() - preview_w
            if preview_y + preview_h > self._monitor_rect.bottom():
                 preview_y = self._monitor_rect.bottom() - preview_h
            preview_x = max(self._monitor_rect.left(), preview_x)
            preview_y = max(self._monitor_rect.top(), preview_y)


            self._overlay_rect = QRect(preview_x, preview_y, preview_w, preview_h)
        else:
            self._overlay_rect = QRect()

    def _get_handle_rects(self) -> dict[int, QRect]:
        if self._overlay_rect.isNull(): return {}
        hs = self.HANDLE_SIZE
        hs_half = hs // 2
        r = self._overlay_rect
        return {
            HANDLE_TOP_LEFT: QRect(r.left() - hs_half, r.top() - hs_half, hs, hs),
            HANDLE_TOP_RIGHT: QRect(r.right() - hs_half, r.top() - hs_half, hs, hs),
            HANDLE_BOTTOM_LEFT: QRect(r.left() - hs_half, r.bottom() - hs_half, hs, hs),
            HANDLE_BOTTOM_RIGHT: QRect(r.right() - hs_half, r.bottom() - hs_half, hs, hs),
        }

    def _get_handle_at(self, pos: QPoint) -> int:
        for handle_type, rect in self._get_handle_rects().items():
            if rect.contains(pos):
                return handle_type
        if self._overlay_rect.contains(pos):
            return HANDLE_MOVE
        return HANDLE_NONE

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(Qt.GlobalColor.lightGray))

        if not self._monitor_rect.isNull():
            painter.setPen(QColor(Qt.GlobalColor.darkGray))
            painter.setBrush(QColor(Qt.GlobalColor.white))
            painter.drawRect(self._monitor_rect)

            if not self._overlay_rect.isNull():
                painter.setPen(QColor(Qt.GlobalColor.blue))
                fill_color = QColor(0, 0, 255, 100)
                current_handle = self._get_handle_at(self.mapFromGlobal(QCursor.pos()))
                if self._dragging_mode == HANDLE_MOVE: fill_color.setAlpha(150)
                elif current_handle == HANDLE_MOVE: fill_color.setAlpha(120)
                painter.setBrush(QBrush(fill_color))
                painter.drawRect(self._overlay_rect)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(Qt.GlobalColor.blue))
                for rect in self._get_handle_rects().values():
                    painter.drawRect(rect)
        painter.end()

    def resizeEvent(self, event):
        self._calculate_rects()
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._monitor_rect.contains(event.pos()):
            self._dragging_mode = self._get_handle_at(event.pos())
            if self._dragging_mode != HANDLE_NONE:
                self._drag_start_pos = event.globalPosition().toPoint()
                self._drag_start_rect = QRect(self._overlay_rect)
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        current_pos = event.globalPosition().toPoint()
        # カーソル形状更新
        if self._dragging_mode == HANDLE_NONE:
            handle_under_cursor = self._get_handle_at(event.pos())
            if handle_under_cursor in (HANDLE_TOP_LEFT, HANDLE_BOTTOM_RIGHT):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif handle_under_cursor in (HANDLE_TOP_RIGHT, HANDLE_BOTTOM_LEFT):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif handle_under_cursor == HANDLE_MOVE:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        # ドラッグ/リサイズ処理
        if self._dragging_mode != HANDLE_NONE and (event.buttons() & Qt.MouseButton.LeftButton):
            delta = current_pos - self._drag_start_pos
            new_rect = QRect(self._drag_start_rect) # 開始時の矩形から毎回計算

            # --- 位置移動 ---
            if self._dragging_mode == HANDLE_MOVE:
                new_rect.translate(delta)
                # 範囲制限（プレビュー矩形内）
                new_rect.moveLeft(max(self._monitor_rect.left(), min(new_rect.left(), self._monitor_rect.right() - new_rect.width())))
                new_rect.moveTop(max(self._monitor_rect.top(), min(new_rect.top(), self._monitor_rect.bottom() - new_rect.height())))

            # --- サイズ変更 ---
            else:
                min_w_preview = self.HANDLE_SIZE * 2 + 2
                min_h_preview = int(round(min_w_preview / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else min_w_preview
                min_h_preview = max(self.HANDLE_SIZE * 2 + 2, min_h_preview)

                # アスペクト比を維持してサイズ計算
                if self._dragging_mode == HANDLE_BOTTOM_RIGHT:
                    new_w = max(min_w_preview, self._drag_start_rect.width() + delta.x())
                    new_h = max(min_h_preview, int(round(new_w / self._overlay_aspect_ratio)))
                    new_w = int(round(new_h * self._overlay_aspect_ratio))
                    # 範囲チェック (右下基準)
                    new_right = min(self._monitor_rect.right(), new_rect.left() + new_w)
                    new_bottom = min(self._monitor_rect.bottom(), new_rect.top() + new_h)
                    new_w = new_right - new_rect.left()
                    new_h = new_bottom - new_rect.top()
                    # アスペクト比を再適用（小さい方に合わせる）
                    if new_w / self._overlay_aspect_ratio < new_h:
                         new_h = int(round(new_w / self._overlay_aspect_ratio))
                    else:
                         new_w = int(round(new_h * self._overlay_aspect_ratio))
                    new_rect.setSize(QSize(new_w, new_h))

                elif self._dragging_mode == HANDLE_TOP_LEFT:
                    new_w = max(min_w_preview, self._drag_start_rect.width() - delta.x())
                    new_h = max(min_h_preview, int(round(new_w / self._overlay_aspect_ratio)))
                    new_w = int(round(new_h * self._overlay_aspect_ratio))
                    # 範囲チェック (左上基準)
                    new_left = max(self._monitor_rect.left(), self._drag_start_rect.right() - new_w)
                    new_top = max(self._monitor_rect.top(), self._drag_start_rect.bottom() - new_h)
                    new_w = self._drag_start_rect.right() - new_left
                    new_h = self._drag_start_rect.bottom() - new_top
                    if new_w / self._overlay_aspect_ratio < new_h:
                        new_h = int(round(new_w / self._overlay_aspect_ratio))
                    else:
                        new_w = int(round(new_h * self._overlay_aspect_ratio))
                    new_rect.setTopLeft(self._drag_start_rect.bottomRight() - QPoint(new_w, new_h))
                    new_rect.setSize(QSize(new_w, new_h))

                # (HANDLE_BOTTOM_LEFT, HANDLE_TOP_RIGHTも同様に修正)
                elif self._dragging_mode == HANDLE_BOTTOM_LEFT:
                     new_w = max(min_w_preview, self._drag_start_rect.width() - delta.x())
                     new_h = max(min_h_preview, int(round(new_w / self._overlay_aspect_ratio)))
                     new_w = int(round(new_h * self._overlay_aspect_ratio))
                     new_left = max(self._monitor_rect.left(), self._drag_start_rect.right() - new_w)
                     new_bottom = min(self._monitor_rect.bottom(), self._drag_start_rect.top() + new_h)
                     new_w = self._drag_start_rect.right() - new_left
                     new_h = new_bottom - self._drag_start_rect.top()
                     if new_w / self._overlay_aspect_ratio < new_h:
                         new_h = int(round(new_w / self._overlay_aspect_ratio))
                     else:
                         new_w = int(round(new_h * self._overlay_aspect_ratio))
                     new_rect.setBottomLeft(QPoint(new_left, self._drag_start_rect.top() + new_h))
                     new_rect.setSize(QSize(new_w, new_h))


                elif self._dragging_mode == HANDLE_TOP_RIGHT:
                     new_w = max(min_w_preview, self._drag_start_rect.width() + delta.x())
                     new_h = max(min_h_preview, int(round(new_w / self._overlay_aspect_ratio)))
                     new_w = int(round(new_h * self._overlay_aspect_ratio))
                     new_right = min(self._monitor_rect.right(), self._drag_start_rect.left() + new_w)
                     new_top = max(self._monitor_rect.top(), self._drag_start_rect.bottom() - new_h)
                     new_w = new_right - self._drag_start_rect.left()
                     new_h = self._drag_start_rect.bottom() - new_top
                     if new_w / self._overlay_aspect_ratio < new_h:
                         new_h = int(round(new_w / self._overlay_aspect_ratio))
                     else:
                         new_w = int(round(new_h * self._overlay_aspect_ratio))
                     new_rect.setTopRight(QPoint(self._drag_start_rect.left() + new_w, new_top))
                     new_rect.setSize(QSize(new_w, new_h))


            # 変更があればシグナル発行と内部状態更新
            if self._overlay_rect != new_rect and self._monitor_rect.width() > 0 and self._monitor_rect.height() > 0:
                # 1. 新しい実際の相対座標(px)に変換
                rel_x_ratio = (new_rect.left() - self._monitor_rect.left()) / self._monitor_rect.width()
                rel_y_ratio = (new_rect.top() - self._monitor_rect.top()) / self._monitor_rect.height()
                new_actual_rel_x = max(0, int(round(rel_x_ratio * self._monitor_width_px))) # round追加
                new_actual_rel_y = max(0, int(round(rel_y_ratio * self._monitor_height_px))) # round追加

                # 2. 新しい実際のサイズ(px)に変換
                new_actual_w = max(1, int(round((new_rect.width() / self._monitor_rect.width()) * self._monitor_width_px))) # round追加
                new_actual_h = max(1, int(round((new_rect.height() / self._monitor_rect.height()) * self._monitor_height_px))) # round追加

                # 3. 内部状態との比較
                position_changed = (self._overlay_relative_pos != QPoint(new_actual_rel_x, new_actual_rel_y))
                size_changed = (self._overlay_actual_width != new_actual_w or self._overlay_actual_height != new_actual_h)

                # 4. 内部状態更新
                if position_changed: self._overlay_relative_pos = QPoint(new_actual_rel_x, new_actual_rel_y)
                if size_changed:
                    self._overlay_actual_width = new_actual_w
                    self._overlay_actual_height = new_actual_h
                    if self._overlay_actual_height > 0:
                        self._overlay_aspect_ratio = self._overlay_actual_width / self._overlay_actual_height

                # 5. プレビュー矩形更新
                self._overlay_rect = new_rect # 計算結果のプレビュー矩形を適用

                # 6. シグナル発行
                if position_changed or size_changed:
                    self.overlayGeometryChanged.emit()

                self.update() # 再描画

    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウスボタン解放：ドラッグ/リサイズ終了"""
        if event.button() == Qt.MouseButton.LeftButton and self._dragging_mode != HANDLE_NONE:
            self._dragging_mode = HANDLE_NONE
            self.mouseMoveEvent(event) # カーソル形状更新のため
            self.update()