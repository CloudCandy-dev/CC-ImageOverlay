# lib/PositionPreviewWidget.py
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent, QPaintEvent, QCursor
from PySide6.QtCore import Qt, Slot, Signal, QPoint, QRect, QSize, QMargins, QLineF

# --- 定数: ハンドルの種類 ---
HANDLE_NONE = 0
HANDLE_TOP_LEFT = 1
HANDLE_TOP_RIGHT = 2
HANDLE_BOTTOM_LEFT = 3
HANDLE_BOTTOM_RIGHT = 4
HANDLE_MOVE = 5

class PositionPreviewWidget(QWidget):
    """オーバーレイ位置とサイズを視覚的に操作するためのプレビューウィジェット"""
    overlayGeometryChanged = Signal() # ジオメトリ変更通知シグナル
    HANDLE_SIZE = 8                   # ハンドルのピクセルサイズ

    def __init__(self, parent=None):
        """コンストラクタ"""
        super().__init__(parent)
        # --- 内部変数初期化 ---
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
        # --- ウィジェット設定 ---
        self.setMinimumSize(100, 50)
        self.setMouseTracking(True)

    def setMonitorGeometry(self, width: int, height: int):
        """モニターの解像度を設定"""
        if width > 0 and height > 0:
            changed = (self._monitor_width_px != width or self._monitor_height_px != height)
            if changed:
                self._monitor_width_px = width
                self._monitor_height_px = height
                self._monitor_aspect_ratio = width / height
                self._calculate_rects() # 内部矩形再計算
                self.update()           # 再描画

    def setOverlayInfo(self, rel_x: int, rel_y: int, overlay_actual_w: int, overlay_actual_h: int):
        """オーバーレイ情報(位置、サイズ)を設定"""
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
            else: self._overlay_aspect_ratio = 1.0

        if pos_changed or size_changed:
            self._calculate_rects() # 内部矩形再計算
            self.update()           # 再描画

    def getOverlayRelativePos(self) -> QPoint:
        """オーバーレイの相対位置を取得"""
        return self._overlay_relative_pos

    def getOverlayActualSize(self) -> QSize:
        """オーバーレイの実際のサイズを取得"""
        return QSize(self._overlay_actual_width, self._overlay_actual_height)

    def _calculate_rects(self):
        """ウィジェット内のモニターとオーバーレイの描画矩形を計算"""
        widget_rect = self.rect().adjusted(1, 1, -1, -1)
        if widget_rect.width() <= 0 or widget_rect.height() <= 0: return

        widget_aspect_ratio = widget_rect.width() / widget_rect.height()

        # モニター矩形計算
        if widget_aspect_ratio > self._monitor_aspect_ratio:
            h = widget_rect.height()
            w = int(round(h * self._monitor_aspect_ratio))
            x = widget_rect.x() + (widget_rect.width() - w) // 2
            y = widget_rect.y()
        else:
            w = widget_rect.width()
            h = int(round(w / self._monitor_aspect_ratio))
            x = widget_rect.x()
            y = widget_rect.y() + (widget_rect.height() - h) // 2
        self._monitor_rect = QRect(x, y, w, h)

        # オーバーレイ矩形計算
        if self._monitor_width_px > 0 and self._monitor_height_px > 0 and w > 0 and h > 0:
            rel_w_ratio = self._overlay_actual_width / self._monitor_width_px
            rel_h_ratio = self._overlay_actual_height / self._monitor_height_px
            preview_w = int(round(w * rel_w_ratio))
            preview_h = int(round(h * rel_h_ratio))
            min_preview_size = self.HANDLE_SIZE * 2 + 2
            preview_w = max(min_preview_size, preview_w)
            preview_h = max(min_preview_size, preview_h)

            rel_x_ratio = self._overlay_relative_pos.x() / self._monitor_width_px
            rel_y_ratio = self._overlay_relative_pos.y() / self._monitor_height_px
            preview_x = self._monitor_rect.x() + int(round(w * rel_x_ratio))
            preview_y = self._monitor_rect.y() + int(round(h * rel_y_ratio))

            # 画面外クリッピング
            if preview_x + preview_w > self._monitor_rect.right() + 1:
                 preview_x = self._monitor_rect.right() + 1 - preview_w
            if preview_y + preview_h > self._monitor_rect.bottom() + 1:
                 preview_y = self._monitor_rect.bottom() + 1 - preview_h
            preview_x = max(self._monitor_rect.left(), preview_x)
            preview_y = max(self._monitor_rect.top(), preview_y)

            self._overlay_rect = QRect(preview_x, preview_y, preview_w, preview_h)
        else:
            self._overlay_rect = QRect()

    def _get_handle_rects(self) -> dict[int, QRect]:
        """リサイズハンドルの矩形辞書を取得"""
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
        """指定座標にあるハンドルの種類を返す"""
        for handle_type, rect in self._get_handle_rects().items():
            if rect.contains(pos):
                return handle_type
        if self._overlay_rect.contains(pos):
            return HANDLE_MOVE
        return HANDLE_NONE

    def paintEvent(self, event: QPaintEvent):
        """描画イベント"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(Qt.GlobalColor.lightGray)) # 背景

        if not self._monitor_rect.isNull():
            painter.setPen(QColor(Qt.GlobalColor.darkGray))
            painter.setBrush(QColor(Qt.GlobalColor.white))
            painter.drawRect(self._monitor_rect) # モニター領域

            if not self._overlay_rect.isNull():
                painter.setPen(QColor(Qt.GlobalColor.blue))
                fill_color = QColor(0, 0, 255, 100) # オーバーレイ領域
                current_handle = self._get_handle_at(self.mapFromGlobal(QCursor.pos()))
                if self._dragging_mode == HANDLE_MOVE: fill_color.setAlpha(150)
                elif current_handle == HANDLE_MOVE: fill_color.setAlpha(120)
                painter.setBrush(QBrush(fill_color))
                painter.drawRect(self._overlay_rect)

                painter.setPen(Qt.PenStyle.NoPen) # ハンドル
                painter.setBrush(QColor(Qt.GlobalColor.blue))
                for rect in self._get_handle_rects().values():
                    painter.drawRect(rect)
        painter.end()

    def resizeEvent(self, event):
        """リサイズイベント"""
        self._calculate_rects()
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """マウスプレスイベント"""
        if event.button() == Qt.MouseButton.LeftButton and self._monitor_rect.contains(event.pos()):
            self._dragging_mode = self._get_handle_at(event.pos())
            if self._dragging_mode != HANDLE_NONE:
                self._drag_start_pos = event.globalPosition().toPoint()
                self._drag_start_rect = QRect(self._overlay_rect)
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """マウスムーブイベント"""
        current_global_pos = event.globalPosition().toPoint()
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
            delta = current_global_pos - self._drag_start_pos
            new_rect = QRect(self._drag_start_rect)

            # 移動処理
            if self._dragging_mode == HANDLE_MOVE:
                new_rect.translate(delta)
                new_rect.moveLeft(max(self._monitor_rect.left(), min(new_rect.left(), self._monitor_rect.right() + 1 - new_rect.width())))
                new_rect.moveTop(max(self._monitor_rect.top(), min(new_rect.top(), self._monitor_rect.bottom() + 1 - new_rect.height())))
            # リサイズ処理
            else:
                min_w_preview = self.HANDLE_SIZE * 2 + 2
                min_h_preview = int(round(min_w_preview / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else min_w_preview
                min_h_preview = max(self.HANDLE_SIZE * 2 + 2, min_h_preview)

                if self._dragging_mode == HANDLE_BOTTOM_RIGHT:
                    temp_w = max(min_w_preview, self._drag_start_rect.width() + delta.x())
                    temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                    final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                    final_h = temp_h
                    new_right = min(self._monitor_rect.right() + 1, new_rect.left() + final_w)
                    new_bottom = min(self._monitor_rect.bottom() + 1, new_rect.top() + final_h)
                    final_w = new_right - new_rect.left()
                    final_h = new_bottom - new_rect.top()
                    if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h: final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else: final_w = int(round(final_h * self._overlay_aspect_ratio))
                    new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))

                elif self._dragging_mode == HANDLE_TOP_LEFT:
                    temp_w = max(min_w_preview, self._drag_start_rect.width() - delta.x())
                    temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                    final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                    final_h = temp_h
                    new_left = max(self._monitor_rect.left(), self._drag_start_rect.right() + 1 - final_w)
                    new_top = max(self._monitor_rect.top(), self._drag_start_rect.bottom() + 1 - final_h)
                    final_w = self._drag_start_rect.right() + 1 - new_left
                    final_h = self._drag_start_rect.bottom() + 1 - new_top
                    if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h: final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else: final_w = int(round(final_h * self._overlay_aspect_ratio))
                    new_rect.setTopLeft(QPoint(new_left, new_top))
                    new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))

                elif self._dragging_mode == HANDLE_BOTTOM_LEFT:
                     temp_w = max(min_w_preview, self._drag_start_rect.width() - delta.x())
                     temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                     final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                     final_h = temp_h
                     new_left = max(self._monitor_rect.left(), self._drag_start_rect.right() + 1 - final_w)
                     new_bottom = min(self._monitor_rect.bottom() + 1, self._drag_start_rect.top() + final_h)
                     final_w = self._drag_start_rect.right() + 1 - new_left
                     final_h = new_bottom - self._drag_start_rect.top()
                     if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h: final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else: final_w = int(round(final_h * self._overlay_aspect_ratio))
                     new_rect.setBottomLeft(QPoint(new_left, new_bottom))
                     new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))

                elif self._dragging_mode == HANDLE_TOP_RIGHT:
                     temp_w = max(min_w_preview, self._drag_start_rect.width() + delta.x())
                     temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                     final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                     final_h = temp_h
                     new_right = min(self._monitor_rect.right() + 1, self._drag_start_rect.left() + final_w)
                     new_top = max(self._monitor_rect.top(), self._drag_start_rect.bottom() + 1 - final_h)
                     final_w = new_right - self._drag_start_rect.left()
                     final_h = self._drag_start_rect.bottom() + 1 - new_top
                     if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h: final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else: final_w = int(round(final_h * self._overlay_aspect_ratio))
                     new_rect.setTopRight(QPoint(new_right, new_top))
                     new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))

            # 変更適用と通知
            if self._overlay_rect != new_rect and self._monitor_rect.width() > 0 and self._monitor_rect.height() > 0:
                # プレビュー座標から実際の座標/サイズへ変換
                rel_x_ratio = (new_rect.left() - self._monitor_rect.left()) / self._monitor_rect.width()
                rel_y_ratio = (new_rect.top() - self._monitor_rect.top()) / self._monitor_rect.height()
                new_actual_rel_x = max(0, int(round(rel_x_ratio * self._monitor_width_px)))
                new_actual_rel_y = max(0, int(round(rel_y_ratio * self._monitor_height_px)))
                new_actual_w = max(1, int(round((new_rect.width() / self._monitor_rect.width()) * self._monitor_width_px)))
                new_actual_h = max(1, int(round((new_rect.height() / self._monitor_rect.height()) * self._monitor_height_px)))

                # 内部状態と比較・更新
                position_changed = (self._overlay_relative_pos != QPoint(new_actual_rel_x, new_actual_rel_y))
                size_changed = (self._overlay_actual_width != new_actual_w or self._overlay_actual_height != new_actual_h)

                if position_changed: self._overlay_relative_pos = QPoint(new_actual_rel_x, new_actual_rel_y)
                if size_changed:
                    self._overlay_actual_width = new_actual_w
                    self._overlay_actual_height = new_actual_h
                    if self._overlay_actual_height > 0:
                        self._overlay_aspect_ratio = self._overlay_actual_width / self._overlay_actual_height

                self._overlay_rect = new_rect # プレビュー矩形更新

                if position_changed or size_changed:
                    self.overlayGeometryChanged.emit() # シグナル発行

                self.update() # 再描画

    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウスリリースイベント"""
        if event.button() == Qt.MouseButton.LeftButton and self._dragging_mode != HANDLE_NONE:
            self._dragging_mode = HANDLE_NONE # ドラッグモード解除
            self.mouseMoveEvent(event)        # カーソル形状更新のため
            self.update()                     # 再描画