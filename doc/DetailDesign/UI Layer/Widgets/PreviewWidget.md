# PreviewWidget 詳細設計

## 1. 概要
PreviewWidgetは、オーバーレイウィンドウの位置とサイズをプレビューするためのウィジェットです。マルチモニター環境での位置関係を視覚的に表現し、ユーザーが直感的に配置を調整できる機能を提供します。

## 2. クラス定義

```python
class PreviewWidget(QWidget):
    """オーバーレイプレビューウィジェット"""

    # シグナル定義
    positionChanged = Signal(QPoint)        # 位置変更通知
    sizeChanged = Signal(QSize)             # サイズ変更通知
    monitorChanged = Signal(str)            # モニター変更通知

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitor_info = None
        self._current_monitor = "primary"
        self._overlay_rect = QRect()
        self._scale_factor = 1.0
        self._dragging = False
        self._resizing = False
        self._drag_start = QPoint()
        self._original_rect = QRect()
        
        self.setMinimumSize(200, 150)
        self.setMouseTracking(True)

    async def initialize(self, monitor_info: MonitorInfo) -> Result[None]:
        """初期化
        Args:
            monitor_info: モニター情報
        Returns:
            Result[None]: 初期化結果
        """
        try:
            self._monitor_info = monitor_info
            await self._calculate_scale_factor()
            await self._setup_ui()
            return Result(success=True, data=None)

        except Exception as e:
            error_msg = f"プレビューウィジェットの初期化に失敗: {e}"
            logger.error(error_msg)
            return Result(
                success=False,
                error=error_msg,
                error_code="PREVIEW_INIT_ERROR"
            )

    async def set_overlay_geometry(self, geometry: QRect) -> Result[None]:
        """オーバーレイジオメトリの設定
        Args:
            geometry: 設定するジオメトリ
        Returns:
            Result[None]: 設定結果
        """
        try:
            conversion_result = await self._scale_rect_to_preview(geometry)
            if not conversion_result.success:
                return conversion_result

            self._overlay_rect = conversion_result.data
            self.update()
            return Result(success=True, data=None)

        except Exception as e:
            error_msg = f"オーバーレイジオメトリの設定に失敗: {e}"
            logger.error(error_msg)
            return Result(
                success=False,
                error=error_msg,
                error_code="OVERLAY_GEOMETRY_ERROR"
            )

    def set_current_monitor(self, monitor_id: str) -> None:
        """現在のモニターの設定"""
        try:
            if monitor_id != self._current_monitor:
                self._current_monitor = monitor_id
                self._calculate_scale_factor()
                self.update()
                self.monitorChanged.emit(monitor_id)
        except Exception as e:
            logger.error(f"モニター設定の変更に失敗: {e}")

    def paintEvent(self, event: QPaintEvent) -> None:
        """描画イベント"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # モニター領域の描画
            self._draw_monitor_area(painter)
            
            # オーバーレイ領域の描画
            if self._overlay_rect.isValid():
                self._draw_overlay_area(painter)
                
            # リサイズハンドルの描画
            if self._overlay_rect.isValid():
                self._draw_resize_handles(painter)

        except Exception as e:
            logger.error(f"プレビューの描画に失敗: {e}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウスボタン押下イベント"""
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            if self._is_on_resize_handle(pos):
                self._start_resize(pos)
            elif self._overlay_rect.contains(pos):
                self._start_drag(pos)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウス移動イベント"""
        try:
            pos = event.pos()
            if self._dragging:
                self._handle_drag(pos)
            elif self._resizing:
                self._handle_resize(pos)
            else:
                self._update_cursor(pos)

        except Exception as e:
            logger.error(f"マウス移動処理に失敗: {e}")

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウスボタン解放イベント"""
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self._end_drag()
            elif self._resizing:
                self._end_resize()

    def _setup_ui(self) -> None:
        """UI構築"""
        # 背景色の設定
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        self.setPalette(palette)

    def _calculate_scale_factor(self) -> None:
        """スケール係数の計算"""
        try:
            if not self._monitor_info:
                return

            monitor_rect = self._monitor_info.get_monitor_geometry(
                self._current_monitor
            )
            if not monitor_rect.isValid():
                return

            # ウィジェットサイズに合わせてスケール係数を計算
            width_scale = self.width() / monitor_rect.width()
            height_scale = self.height() / monitor_rect.height()
            self._scale_factor = min(width_scale, height_scale) * 0.9

        except Exception as e:
            logger.error(f"スケール係数の計算に失敗: {e}")

    async def _scale_rect_to_preview(self, rect: QRect) -> Result[QRect]:
        """実座標からプレビュー座標への変換
        Args:
            rect: 変換する矩形
        Returns:
            Result[QRect]: 変換結果
        """
        try:
            if not self._monitor_info:
                return Result(
                    success=False,
                    error="モニター情報が初期化されていません",
                    error_code="NO_MONITOR_INFO"
                )

            monitor_result = await self._monitor_info.get_monitor_geometry(
                self._current_monitor
            )
            if not monitor_result.success:
                return monitor_result

            monitor_rect = monitor_result.data
            if not monitor_rect.isValid():
                return Result(
                    success=False,
                    error="無効なモニター領域です",
                    error_code="INVALID_MONITOR_RECT"
                )

            # モニター座標系からウィジェット座標系への変換
            x = (rect.x() - monitor_rect.x()) * self._scale_factor
            y = (rect.y() - monitor_rect.y()) * self._scale_factor
            width = rect.width() * self._scale_factor
            height = rect.height() * self._scale_factor

            # ウィジェット中央に配置
            offset_x = (self.width() - monitor_rect.width() * self._scale_factor) / 2
            offset_y = (self.height() - monitor_rect.height() * self._scale_factor) / 2

            return QRect(
                int(x + offset_x),
                int(y + offset_y),
                int(width),
                int(height)
            )

        except Exception as e:
            logger.error(f"座標変換に失敗: {e}")
            return QRect()

    def _scale_rect_to_real(self, rect: QRect) -> QRect:
        """プレビュー座標から実座標への変換"""
        try:
            if not self._monitor_info:
                return QRect()

            monitor_rect = self._monitor_info.get_monitor_geometry(
                self._current_monitor
            )
            if not monitor_rect.isValid():
                return QRect()

            # ウィジェット中央配置のオフセットを考慮
            offset_x = (self.width() - monitor_rect.width() * self._scale_factor) / 2
            offset_y = (self.height() - monitor_rect.height() * self._scale_factor) / 2

            # ウィジェット座標系からモニター座標系への変換
            x = (rect.x() - offset_x) / self._scale_factor + monitor_rect.x()
            y = (rect.y() - offset_y) / self._scale_factor + monitor_rect.y()
            width = rect.width() / self._scale_factor
            height = rect.height() / self._scale_factor

            return QRect(
                int(x),
                int(y),
                int(width),
                int(height)
            )

        except Exception as e:
            logger.error(f"座標変換に失敗: {e}")
            return QRect()

    def _draw_monitor_area(self, painter: QPainter) -> None:
        """モニター領域の描画"""
        try:
            if not self._monitor_info:
                return

            monitor_rect = self._monitor_info.get_monitor_geometry(
                self._current_monitor
            )
            if not monitor_rect.isValid():
                return

            # モニター領域を描画
            scaled_rect = self._scale_rect_to_preview(monitor_rect)
            painter.setPen(QPen(Qt.darkGray, 1))
            painter.setBrush(Qt.white)
            painter.drawRect(scaled_rect)

            # モニター情報を描画
            painter.setPen(Qt.black)
            painter.drawText(
                scaled_rect,
                Qt.AlignCenter,
                f"Monitor: {self._current_monitor}\n"
                f"{monitor_rect.width()}x{monitor_rect.height()}"
            )

        except Exception as e:
            logger.error(f"モニター領域の描画に失敗: {e}")

    def _draw_overlay_area(self, painter: QPainter) -> None:
        """オーバーレイ領域の描画"""
        try:
            # オーバーレイ領域を描画
            painter.setPen(QPen(Qt.blue, 2))
            painter.setBrush(QColor(0, 0, 255, 50))
            painter.drawRect(self._overlay_rect)

            # サイズ情報を描画
            real_rect = self._scale_rect_to_real(self._overlay_rect)
            size_text = f"{real_rect.width()}x{real_rect.height()}"
            painter.setPen(Qt.black)
            painter.drawText(
                self._overlay_rect,
                Qt.AlignCenter,
                size_text
            )

        except Exception as e:
            logger.error(f"オーバーレイ領域の描画に失敗: {e}")

    def _draw_resize_handles(self, painter: QPainter) -> None:
        """リサイズハンドルの描画"""
        try:
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(Qt.white)
            
            handle_size = 6
            rect = self._overlay_rect
            handles = [
                (rect.topLeft(), handle_size),
                (rect.topRight(), handle_size),
                (rect.bottomLeft(), handle_size),
                (rect.bottomRight(), handle_size),
                (QPoint(rect.left(), rect.center().y()), handle_size),
                (QPoint(rect.right(), rect.center().y()), handle_size),
                (QPoint(rect.center().x(), rect.top()), handle_size),
                (QPoint(rect.center().x(), rect.bottom()), handle_size)
            ]

            for pos, size in handles:
                painter.drawRect(
                    QRect(
                        pos.x() - size // 2,
                        pos.y() - size // 2,
                        size,
                        size
                    )
                )

        except Exception as e:
            logger.error(f"リサイズハンドルの描画に失敗: {e}")

    def _is_on_resize_handle(self, pos: QPoint) -> bool:
        """リサイズハンドル上かどうかの判定"""
        handle_size = 6
        rect = self._overlay_rect
        handles = [
            (rect.topLeft(), handle_size),
            (rect.topRight(), handle_size),
            (rect.bottomLeft(), handle_size),
            (rect.bottomRight(), handle_size),
            (QPoint(rect.left(), rect.center().y()), handle_size),
            (QPoint(rect.right(), rect.center().y()), handle_size),
            (QPoint(rect.center().x(), rect.top()), handle_size),
            (QPoint(rect.center().x(), rect.bottom()), handle_size)
        ]

        for handle_pos, size in handles:
            handle_rect = QRect(
                handle_pos.x() - size // 2,
                handle_pos.y() - size // 2,
                size,
                size
            )
            if handle_rect.contains(pos):
                return True

        return False

    def _start_drag(self, pos: QPoint) -> None:
        """ドラッグ開始"""
        self._dragging = True
        self._drag_start = pos
        self._original_rect = self._overlay_rect

    def _handle_drag(self, pos: QPoint) -> None:
        """ドラッグ処理"""
        if not self._dragging:
            return

        try:
            # 移動量を計算
            delta = pos - self._drag_start
            new_rect = self._original_rect.translated(delta)
            
            # モニター領域内に収まるように調整
            monitor_rect = self._scale_rect_to_preview(
                self._monitor_info.get_monitor_geometry(self._current_monitor)
            )
            if not monitor_rect.contains(new_rect):
                # 領域外にはみ出す場合、位置を調整
                if new_rect.left() < monitor_rect.left():
                    delta.setX(monitor_rect.left() - self._original_rect.left())
                elif new_rect.right() > monitor_rect.right():
                    delta.setX(monitor_rect.right() - self._original_rect.right())
                
                if new_rect.top() < monitor_rect.top():
                    delta.setY(monitor_rect.top() - self._original_rect.top())
                elif new_rect.bottom() > monitor_rect.bottom():
                    delta.setY(monitor_rect.bottom() - self._original_rect.bottom())
                
                new_rect = self._original_rect.translated(delta)

            # 位置を更新
            self._overlay_rect = new_rect
            self.update()
            
            # 実座標に変換して通知
            real_pos = self._scale_rect_to_real(new_rect).topLeft()
            self.positionChanged.emit(real_pos)

        except Exception as e:
            logger.error(f"ドラッグ処理に失敗: {e}")

    def _start_resize(self, pos: QPoint) -> None:
        """リサイズ開始"""
        self._resizing = True
        self._drag_start = pos
        self._original_rect = self._overlay_rect

    def _handle_resize(self, pos: QPoint) -> None:
        """リサイズ処理"""
        if not self._resizing:
            return

        try:
            # リサイズ後の矩形を計算
            delta = pos - self._drag_start
            new_rect = QRect(self._original_rect)
            
            # リサイズハンドルの位置に応じて調整
            if self._is_on_resize_handle(self._drag_start):
                if pos.x() < self._original_rect.right():
                    new_rect.setLeft(pos.x())
                else:
                    new_rect.setRight(pos.x())
                    
                if pos.y() < self._original_rect.bottom():
                    new_rect.setTop(pos.y())
                else:
                    new_rect.setBottom(pos.y())

            # 最小サイズを確保
            min_size = 20  # プレビュー上での最小サイズ
            if new_rect.width() < min_size:
                new_rect.setWidth(min_size)
            if new_rect.height() < min_size:
                new_rect.setHeight(min_size)

            # モニター領域内に収まるように調整
            monitor_rect = self._scale_rect_to_preview(
                self._monitor_info.get_monitor_geometry(self._current_monitor)
            )
            if not monitor_rect.contains(new_rect):
                if new_rect.left() < monitor_rect.left():
                    new_rect.setLeft(monitor_rect.left())
                if new_rect.top() < monitor_rect.top():
                    new_rect.setTop(monitor_rect.top())
                if new_rect.right() > monitor_rect.right():
                    new_rect.setRight(monitor_rect.right())
                if new_rect.bottom() > monitor_rect.bottom():
                    new_rect.setBottom(monitor_rect.bottom())

            # サイズを更新
            self._overlay_rect = new_rect
            self.update()
            
            # 実サイズに変換して通知
            real_size = self._scale_rect_to_real(new_rect).size()
            self.sizeChanged.emit(real_size)

        except Exception as e:
            logger.error(f"リサイズ処理に失敗: {e}")

    def _end_drag(self) -> None:
        """ドラッグ終了"""
        self._dragging = False
        self._drag_start = QPoint()
        self._original_rect = QRect()

    def _end_resize(self) -> None:
        """リサイズ終了"""
        self._resizing = False
        self._drag_start = QPoint()
        self._original_rect = QRect()

    def _update_cursor(self, pos: QPoint) -> None:
        """カーソル形状の更新"""
        if self._is_on_resize_handle(pos):
            self.setCursor(Qt.SizeAllCursor)
        elif self._overlay_rect.contains(pos):
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
```

## 3. 主要機能

### 3.1 表示機能
- モニターレイアウトの表示
- オーバーレイ位置のプレビュー
- サイズ情報の表示
- リサイズハンドルの表示

### 3.2 操作機能
- ドラッグによる位置調整
- リサイズハンドルによるサイズ調整
- モニター選択
- スケーリング処理

### 3.3 座標変換
- 実座標 ⟷ プレビュー座標の変換
- スケール係数の管理
- モニター境界の考慮
- アスペクト比の維持

## 4. イベント処理

### 4.1 マウスイベント
- ドラッグ開始/終了
- リサイズ開始/終了
- カーソル形状の変更
- 境界チェック

### 4.2 描画イベント
- モニター領域の描画
- オーバーレイ領域の描画
- リサイズハンドルの描画
- 情報テキストの描画

## 5. エラー処理

### 5.1 エラー型定義
```python
class PreviewWidgetError:
    """プレビューウィジェットのエラー情報"""
    code: str
    message: str
    details: Optional[Dict]
    recoverable: bool
```

### 5.2 エラーコード
```python
PREVIEW_ERROR_CODES = {
    # 初期化エラー
    "PREVIEW_INIT_ERROR": {
        "message": "プレビューウィジェットの初期化に失敗しました",
        "recoverable": False
    },
    # ジオメトリエラー
    "OVERLAY_GEOMETRY_ERROR": {
        "message": "オーバーレイジオメトリの設定に失敗しました",
        "recoverable": True
    },
    # モニター関連エラー
    "NO_MONITOR_INFO": {
        "message": "モニター情報が初期化されていません",
        "recoverable": True
    },
    "INVALID_MONITOR_RECT": {
        "message": "無効なモニター領域です",
        "recoverable": True
    },
    # 座標変換エラー
    "COORDINATE_CONVERSION_ERROR": {
        "message": "座標変換に失敗しました",
        "recoverable": True
    }
}
```

### 5.3 エラーハンドリング
```python
class PreviewWidgetErrorHandler:
    """プレビューウィジェットのエラーハンドラー"""
    
    @staticmethod
    def handle_error(error: Exception, context: Dict) -> Result:
        """エラー処理
        Args:
            error: 発生した例外
            context: エラーコンテキスト
        Returns:
            Result: エラー処理結果
        """
        error_code = context.get("error_code", "UNKNOWN_ERROR")
        error_info = PREVIEW_ERROR_CODES.get(error_code, {
            "message": "不明なエラーが発生しました",
            "recoverable": False
        })
        
        # エラーログの記録
        logger.error(
            f"{error_info['message']}: {str(error)}",
            extra={
                "error_code": error_code,
                "context": context
            }
        )
        
        return Result(
            success=False,
            error=error_info["message"],
            error_code=error_code
        )
```

### 5.4 リカバリー処理
```python
class PreviewWidgetRecovery:
    """プレビューウィジェットのリカバリー処理"""
    
    @staticmethod
    async def recover_from_error(error_code: str, widget: 'PreviewWidget') -> Result:
        """エラーからの復旧
        Args:
            error_code: エラーコード
            widget: プレビューウィジェットインスタンス
        Returns:
            Result: 復旧結果
        """
        try:
            if error_code == "NO_MONITOR_INFO":
                return await widget.initialize(MonitorInfo())
            elif error_code == "OVERLAY_GEOMETRY_ERROR":
                return await widget.set_overlay_geometry(QRect())
            # その他のリカバリー処理...
            
            return Result(success=True, data=None)
            
        except Exception as e:
            return Result(
                success=False,
                error=f"リカバリー処理に失敗: {e}",
                error_code="RECOVERY_FAILED"
            )
```

## 6. 最適化

### 6.1 描画最適化
- クリッピング領域の設定
- ダブルバッファリング
- アンチエイリアス
- 再描画の最小化

### 6.2 パフォーマンス
- 座標変換のキャッシュ
- イベントフィルタリング
- メモリ使用の最適化
- 更新頻度の制御
