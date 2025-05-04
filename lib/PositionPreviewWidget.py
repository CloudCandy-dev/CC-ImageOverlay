# lib/PositionPreviewWidget.py
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent, QPaintEvent, QCursor
from PySide6.QtCore import Qt, Slot, Signal, QPoint, QRect, QSize, QMargins, QLineF

# --- 定数 ---
# ハンドル（四隅の□や移動領域）の種類を示す定数
HANDLE_NONE = 0         # ハンドル外
HANDLE_TOP_LEFT = 1     # 左上ハンドル
HANDLE_TOP_RIGHT = 2    # 右上ハンドル
HANDLE_BOTTOM_LEFT = 3  # 左下ハンドル
HANDLE_BOTTOM_RIGHT = 4 # 右下ハンドル
HANDLE_MOVE = 5         # 移動ハンドル (オーバーレイ領域内)

class PositionPreviewWidget(QWidget):
    """
    オーバーレイ表示される画像の位置とサイズを、
    モニターのプレビュー上で視覚的に操作するためのカスタムウィジェット。
    """
    # シグナル: オーバーレイのジオメトリ（位置またはサイズ）が変更されたときに発行される
    overlayGeometryChanged = Signal()
    # ハンドルのサイズ (ピクセル)
    HANDLE_SIZE = 8

    def __init__(self, parent=None):
        """コンストラクタ"""
        super().__init__(parent)
        # --- 内部状態変数 ---
        self._monitor_aspect_ratio = 16 / 9   # モニターのアスペクト比 (デフォルト)
        self._monitor_rect = QRect()          # ウィジェット内に描画されるモニター領域の矩形
        self._overlay_rect = QRect()          # ウィジェット内に描画されるオーバーレイ領域の矩形
        self._overlay_relative_pos = QPoint(0, 0) # オーバーレイの実際の相対位置 (モニター左上基準, px)
        self._overlay_actual_width = 50       # オーバーレイの実際の幅 (px)
        self._overlay_actual_height = 50      # オーバーレイの実際の高さ (px)
        self._overlay_aspect_ratio = 1.0      # オーバーレイ画像のアスペクト比
        self._monitor_width_px = 1920         # 対象モニターの実際の幅 (px)
        self._monitor_height_px = 1080        # 対象モニターの実際の高さ (px)
        self._dragging_mode = HANDLE_NONE     # 現在のドラッグ操作の種類
        self._drag_start_pos = QPoint()       # ドラッグ開始時のマウスカーソル位置 (グローバル座標)
        self._drag_start_rect = QRect()       # ドラッグ開始時のオーバーレイ矩形 (ウィジェット内座標)

        # --- ウィジェット設定 ---
        # 以前の修正で導入したが、元のコードにはなかったためコメントアウト（必要なら有効化）
        # self.setMinimumSize(150, 100)
        # 元のコードにあった設定
        self.setMinimumSize(100, 50)
        self.setMouseTracking(True)   # マウスボタンが押されていなくてもmousemoveイベントを補足する

    def setMonitorGeometry(self, width: int, height: int):
        """
        プレビュー対象のモニターの実際の解像度を設定する。

        Args:
            width (int): モニターの幅 (ピクセル)
            height (int): モニターの高さ (ピクセル)
        """
        if width > 0 and height > 0:
            # 値が実際に変更されたか確認
            changed = (self._monitor_width_px != width or self._monitor_height_px != height)
            if changed:
                self._monitor_width_px = width
                self._monitor_height_px = height
                self._monitor_aspect_ratio = width / height
                self._calculate_rects() # ウィジェット内の描画矩形を再計算
                self.update()           # ウィジェットを再描画

    def setOverlayInfo(self, rel_x: int, rel_y: int, overlay_actual_w: int, overlay_actual_h: int):
        """
        オーバーレイの現在の情報（相対位置と実際のサイズ）を設定する。
        主にMainWindow側からスライダー等の変更を反映するために呼び出される。

        Args:
            rel_x (int): オーバーレイのモニター左上からの相対X座標 (px)
            rel_y (int): オーバーレイのモニター左上からの相対Y座標 (px)
            overlay_actual_w (int): オーバーレイの実際の幅 (px)
            overlay_actual_h (int): オーバーレイの実際の高さ (px)
        """
        new_pos = QPoint(rel_x, rel_y)
        # サイズは最低1pxとする
        new_w = max(1, overlay_actual_w)
        new_h = max(1, overlay_actual_h)

        # 位置またはサイズが変更されたか確認
        pos_changed = (self._overlay_relative_pos != new_pos)
        size_changed = (self._overlay_actual_width != new_w or self._overlay_actual_height != new_h)

        if pos_changed:
            self._overlay_relative_pos = new_pos
        if size_changed:
            self._overlay_actual_width = new_w
            self._overlay_actual_height = new_h
            # アスペクト比を更新 (ゼロ除算回避)
            if self._overlay_actual_height > 0:
                self._overlay_aspect_ratio = self._overlay_actual_width / self._overlay_actual_height
            else:
                self._overlay_aspect_ratio = 1.0 # 高さが0の場合は1.0とする

        # 変更があれば描画矩形を再計算して再描画
        if pos_changed or size_changed:
            self._calculate_rects()
            self.update()

    def getOverlayRelativePos(self) -> QPoint:
        """現在のオーバーレイの相対位置 (モニター左上基準, px) を取得する。"""
        return self._overlay_relative_pos

    def getOverlayActualSize(self) -> QSize:
        """現在のオーバーレイの実際のサイズ (px) を取得する。"""
        return QSize(self._overlay_actual_width, self._overlay_actual_height)

    def _calculate_rects(self):
        """ウィジェット内に描画するモニターとオーバーレイの矩形を計算する。"""
        # ウィジェットの描画可能領域を取得 (枠線分考慮)
        widget_rect = self.rect().adjusted(1, 1, -1, -1)
        if widget_rect.width() <= 0 or widget_rect.height() <= 0: return # 描画領域がなければ何もしない

        # ウィジェットのアスペクト比を計算
        widget_aspect_ratio = widget_rect.width() / widget_rect.height()

        # ウィジェットのアスペクト比とモニターのアスペクト比を比較し、
        # モニターがウィジェット内に最大サイズで収まるように描画領域 (_monitor_rect) を計算する
        if widget_aspect_ratio > self._monitor_aspect_ratio:
            # ウィジェットが横長の場合、高さを基準にする
            h = widget_rect.height()
            w = int(round(h * self._monitor_aspect_ratio)) # roundで丸める
            x = widget_rect.x() + (widget_rect.width() - w) // 2 # 水平中央に配置
            y = widget_rect.y()
        else:
            # ウィジェットが縦長または同じ比率の場合、幅を基準にする
            w = widget_rect.width()
            h = int(round(w / self._monitor_aspect_ratio)) # roundで丸める
            x = widget_rect.x()
            y = widget_rect.y() + (widget_rect.height() - h) // 2 # 垂直中央に配置
        self._monitor_rect = QRect(x, y, w, h)

        # モニターとオーバーレイの実際のサイズに基づいて、
        # ウィジェット内に描画するオーバーレイの矩形 (_overlay_rect) を計算する
        if self._monitor_width_px > 0 and self._monitor_height_px > 0 and w > 0 and h > 0:
            # オーバーレイの実際のサイズとモニターの実際のサイズの比率を計算
            rel_w_ratio = self._overlay_actual_width / self._monitor_width_px
            rel_h_ratio = self._overlay_actual_height / self._monitor_height_px
            # ウィジェット内のモニター矩形に対するオーバーレイのプレビューサイズを計算
            preview_w = int(round(w * rel_w_ratio))
            preview_h = int(round(h * rel_h_ratio))
            # プレビューサイズが小さすぎると操作できないため、最小サイズを保証
            min_preview_size = self.HANDLE_SIZE * 2 + 2
            preview_w = max(min_preview_size, preview_w)
            preview_h = max(min_preview_size, preview_h)

            # オーバーレイの実際の相対位置とモニターの実際のサイズの比率を計算
            rel_x_ratio = self._overlay_relative_pos.x() / self._monitor_width_px
            rel_y_ratio = self._overlay_relative_pos.y() / self._monitor_height_px
            # ウィジェット内のモニター矩形に対するオーバーレイのプレビュー位置を計算
            preview_x = self._monitor_rect.x() + int(round(w * rel_x_ratio))
            preview_y = self._monitor_rect.y() + int(round(h * rel_y_ratio))

            # プレビュー位置がモニター矩形からはみ出ないように調整
            # 右端チェック
            if preview_x + preview_w > self._monitor_rect.right() + 1: # +1は丸め誤差考慮
                 preview_x = self._monitor_rect.right() + 1 - preview_w
            # 下端チェック
            if preview_y + preview_h > self._monitor_rect.bottom() + 1: # +1は丸め誤差考慮
                 preview_y = self._monitor_rect.bottom() + 1 - preview_h
            # 左端チェック
            preview_x = max(self._monitor_rect.left(), preview_x)
            # 上端チェック
            preview_y = max(self._monitor_rect.top(), preview_y)


            self._overlay_rect = QRect(preview_x, preview_y, preview_w, preview_h)
        else:
            # 計算に必要な情報が不足している場合は空の矩形にする
            self._overlay_rect = QRect()

    def _get_handle_rects(self) -> dict[int, QRect]:
        """
        オーバーレイの四隅のリサイズハンドルの矩形を取得する。

        Returns:
            dict[int, QRect]: ハンドルの種類(int)をキー、矩形(QRect)を値とする辞書。
                               オーバーレイ矩形が無効な場合は空の辞書。
        """
        if self._overlay_rect.isNull(): return {} # オーバーレイ矩形が無効なら空
        hs = self.HANDLE_SIZE
        hs_half = hs // 2 # ハンドル中心を角に合わせるためのオフセット
        r = self._overlay_rect
        # 各ハンドルの矩形を計算
        return {
            HANDLE_TOP_LEFT: QRect(r.left() - hs_half, r.top() - hs_half, hs, hs),
            HANDLE_TOP_RIGHT: QRect(r.right() - hs_half, r.top() - hs_half, hs, hs),
            HANDLE_BOTTOM_LEFT: QRect(r.left() - hs_half, r.bottom() - hs_half, hs, hs),
            HANDLE_BOTTOM_RIGHT: QRect(r.right() - hs_half, r.bottom() - hs_half, hs, hs),
        }

    def _get_handle_at(self, pos: QPoint) -> int:
        """
        指定されたウィジェット内座標にあるハンドルの種類を返す。

        Args:
            pos (QPoint): マウスカーソルのウィジェット内座標。

        Returns:
            int: ハンドルの種類を示す定数 (HANDLE_NONE, HANDLE_MOVE など)。
        """
        # 各リサイズハンドルの矩形に含まれるかチェック
        for handle_type, rect in self._get_handle_rects().items():
            if rect.contains(pos):
                return handle_type
        # オーバーレイの矩形（リサイズハンドルを除く）に含まれるかチェック
        if self._overlay_rect.contains(pos):
            return HANDLE_MOVE
        # どのハンドルにも含まれない場合
        return HANDLE_NONE

    def paintEvent(self, event: QPaintEvent):
        """ウィジェットの描画イベントハンドラ。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # アンチエイリアス有効

        # 1. 背景を描画
        painter.fillRect(self.rect(), QColor(Qt.GlobalColor.lightGray))

        # 2. モニター矩形を描画 (計算済みの場合)
        if not self._monitor_rect.isNull():
            painter.setPen(QColor(Qt.GlobalColor.darkGray))  # 枠線の色
            painter.setBrush(QColor(Qt.GlobalColor.white)) # 塗りつぶしの色
            painter.drawRect(self._monitor_rect)

            # 3. オーバーレイ矩形を描画 (計算済みの場合)
            if not self._overlay_rect.isNull():
                painter.setPen(QColor(Qt.GlobalColor.blue)) # 枠線の色
                # 塗りつぶしの色 (マウスカーソル位置やドラッグ状態で透明度を変える)
                fill_color = QColor(0, 0, 255, 100) # 半透明の青
                current_handle = self._get_handle_at(self.mapFromGlobal(QCursor.pos())) # 現在のマウスカーソル下のハンドル
                if self._dragging_mode == HANDLE_MOVE:
                    fill_color.setAlpha(150) # 移動中は少し濃く
                elif current_handle == HANDLE_MOVE and self._dragging_mode == HANDLE_NONE:
                    fill_color.setAlpha(120) # 移動可能な場所にホバー中
                painter.setBrush(QBrush(fill_color))
                painter.drawRect(self._overlay_rect)

                # 4. リサイズハンドルを描画
                painter.setPen(Qt.PenStyle.NoPen)           # ハンドルに枠線は不要
                painter.setBrush(QColor(Qt.GlobalColor.blue)) # ハンドルの色
                for rect in self._get_handle_rects().values():
                    painter.drawRect(rect) # 四隅のハンドルを描画

        painter.end() # ペインター終了

    def resizeEvent(self, event):
        """ウィジェットのリサイズイベントハンドラ。"""
        self._calculate_rects() # ウィジェットサイズが変わったら内部の矩形を再計算
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """マウスボタン押下イベントハンドラ。"""
        # 左クリックで、かつモニター矩形内でのクリックの場合
        if event.button() == Qt.MouseButton.LeftButton and self._monitor_rect.contains(event.pos()):
            # クリック位置にあるハンドルの種類を特定
            self._dragging_mode = self._get_handle_at(event.pos())
            # ハンドルがクリックされた場合（移動またはリサイズ開始）
            if self._dragging_mode != HANDLE_NONE:
                self._drag_start_pos = event.globalPosition().toPoint() # ドラッグ開始座標を記録 (グローバル)
                self._drag_start_rect = QRect(self._overlay_rect)      # ドラッグ開始時の矩形を記録
                self.update() # ドラッグ開始状態を描画に反映させるため再描画

    def mouseMoveEvent(self, event: QMouseEvent):
        """マウス移動イベントハンドラ。"""
        current_global_pos = event.globalPosition().toPoint()

        # --- 1. カーソル形状の更新 ---
        # ドラッグ中でない場合のみ、マウス位置に応じてカーソル形状を変更
        if self._dragging_mode == HANDLE_NONE:
            handle_under_cursor = self._get_handle_at(event.pos())
            if handle_under_cursor in (HANDLE_TOP_LEFT, HANDLE_BOTTOM_RIGHT):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor) # 斜めリサイズカーソル (＼)
            elif handle_under_cursor in (HANDLE_TOP_RIGHT, HANDLE_BOTTOM_LEFT):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor) # 斜めリサイズカーソル (／)
            elif handle_under_cursor == HANDLE_MOVE:
                self.setCursor(Qt.CursorShape.SizeAllCursor)  # 移動カーソル (十字)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)   # 通常カーソル

        # --- 2. ドラッグ/リサイズ処理 ---
        # 左ボタンが押されたまま、かつハンドルをドラッグ中の場合
        if self._dragging_mode != HANDLE_NONE and (event.buttons() & Qt.MouseButton.LeftButton):
            delta = current_global_pos - self._drag_start_pos # ドラッグ開始位置からの移動量
            new_rect = QRect(self._drag_start_rect)           # 開始時の矩形をコピーして変更を加える

            # --- 2a. 位置移動 ---
            if self._dragging_mode == HANDLE_MOVE:
                new_rect.translate(delta) # 移動量をそのまま適用
                # プレビュー矩形がモニター矩形からはみ出ないように制限
                new_rect.moveLeft(max(self._monitor_rect.left(), min(new_rect.left(), self._monitor_rect.right() + 1 - new_rect.width())))
                new_rect.moveTop(max(self._monitor_rect.top(), min(new_rect.top(), self._monitor_rect.bottom() + 1 - new_rect.height())))

            # --- 2b. サイズ変更 ---
            else:
                # プレビュー上の最小幅/高さを計算 (ハンドルサイズ依存)
                min_w_preview = self.HANDLE_SIZE * 2 + 2
                # アスペクト比を考慮した最小高さを計算
                if self._overlay_aspect_ratio > 0:
                    min_h_preview = int(round(min_w_preview / self._overlay_aspect_ratio))
                else:
                    min_h_preview = min_w_preview # アスペクト比が無効なら幅と同じ
                min_h_preview = max(self.HANDLE_SIZE * 2 + 2, min_h_preview) # ハンドルサイズ以下にはしない

                # 各ハンドルに応じたリサイズ計算 (アスペクト比維持)
                # round() を使って整数に丸める
                if self._dragging_mode == HANDLE_BOTTOM_RIGHT: # 右下ハンドル
                    temp_w = max(min_w_preview, self._drag_start_rect.width() + delta.x())
                    temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                    final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                    final_h = temp_h
                    new_right = min(self._monitor_rect.right() + 1, new_rect.left() + final_w)
                    new_bottom = min(self._monitor_rect.bottom() + 1, new_rect.top() + final_h)
                    final_w = new_right - new_rect.left()
                    final_h = new_bottom - new_rect.top()
                    if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h:
                             final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else:
                             final_w = int(round(final_h * self._overlay_aspect_ratio))
                    new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))

                elif self._dragging_mode == HANDLE_TOP_LEFT: # 左上ハンドル
                    temp_w = max(min_w_preview, self._drag_start_rect.width() - delta.x())
                    temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                    final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                    final_h = temp_h
                    new_left = max(self._monitor_rect.left(), self._drag_start_rect.right() + 1 - final_w)
                    new_top = max(self._monitor_rect.top(), self._drag_start_rect.bottom() + 1 - final_h)
                    final_w = self._drag_start_rect.right() + 1 - new_left
                    final_h = self._drag_start_rect.bottom() + 1 - new_top
                    if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h:
                            final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else:
                            final_w = int(round(final_h * self._overlay_aspect_ratio))
                    new_rect.setTopLeft(QPoint(new_left, new_top))
                    new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))

                elif self._dragging_mode == HANDLE_BOTTOM_LEFT: # 左下ハンドル
                     temp_w = max(min_w_preview, self._drag_start_rect.width() - delta.x())
                     temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                     final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                     final_h = temp_h
                     new_left = max(self._monitor_rect.left(), self._drag_start_rect.right() + 1 - final_w)
                     new_bottom = min(self._monitor_rect.bottom() + 1, self._drag_start_rect.top() + final_h)
                     final_w = self._drag_start_rect.right() + 1 - new_left
                     final_h = new_bottom - self._drag_start_rect.top()
                     if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h:
                            final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else:
                            final_w = int(round(final_h * self._overlay_aspect_ratio))
                     new_rect.setBottomLeft(QPoint(new_left, new_bottom))
                     new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))


                elif self._dragging_mode == HANDLE_TOP_RIGHT: # 右上ハンドル
                     temp_w = max(min_w_preview, self._drag_start_rect.width() + delta.x())
                     temp_h = max(min_h_preview, int(round(temp_w / self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_w)
                     final_w = int(round(temp_h * self._overlay_aspect_ratio)) if self._overlay_aspect_ratio > 0 else temp_h
                     final_h = temp_h
                     new_right = min(self._monitor_rect.right() + 1, self._drag_start_rect.left() + final_w)
                     new_top = max(self._monitor_rect.top(), self._drag_start_rect.bottom() + 1 - final_h)
                     final_w = new_right - self._drag_start_rect.left()
                     final_h = self._drag_start_rect.bottom() + 1 - new_top
                     if self._overlay_aspect_ratio > 0:
                        if final_w / self._overlay_aspect_ratio < final_h:
                            final_h = int(round(final_w / self._overlay_aspect_ratio))
                        else:
                            final_w = int(round(final_h * self._overlay_aspect_ratio))
                     new_rect.setTopRight(QPoint(new_right, new_top))
                     new_rect.setSize(QSize(max(min_w_preview, final_w), max(min_h_preview, final_h)))


            # --- 3. 変更の適用と通知 ---
            if self._overlay_rect != new_rect and self._monitor_rect.width() > 0 and self._monitor_rect.height() > 0:
                rel_x_ratio = (new_rect.left() - self._monitor_rect.left()) / self._monitor_rect.width()
                rel_y_ratio = (new_rect.top() - self._monitor_rect.top()) / self._monitor_rect.height()
                new_actual_rel_x = max(0, int(round(rel_x_ratio * self._monitor_width_px)))
                new_actual_rel_y = max(0, int(round(rel_y_ratio * self._monitor_height_px)))

                new_actual_w = max(1, int(round((new_rect.width() / self._monitor_rect.width()) * self._monitor_width_px)))
                new_actual_h = max(1, int(round((new_rect.height() / self._monitor_rect.height()) * self._monitor_height_px)))

                position_changed = (self._overlay_relative_pos != QPoint(new_actual_rel_x, new_actual_rel_y))
                size_changed = (self._overlay_actual_width != new_actual_w or self._overlay_actual_height != new_actual_h)

                if position_changed: self._overlay_relative_pos = QPoint(new_actual_rel_x, new_actual_rel_y)
                if size_changed:
                    self._overlay_actual_width = new_actual_w
                    self._overlay_actual_height = new_actual_h
                    if self._overlay_actual_height > 0:
                        self._overlay_aspect_ratio = self._overlay_actual_width / self._overlay_actual_height

                self._overlay_rect = new_rect

                if position_changed or size_changed:
                    self.overlayGeometryChanged.emit()

                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウスボタン解放イベントハンドラ。"""
        if event.button() == Qt.MouseButton.LeftButton and self._dragging_mode != HANDLE_NONE:
            self._dragging_mode = HANDLE_NONE
            self.mouseMoveEvent(event) # カーソル形状更新のため
            self.update()