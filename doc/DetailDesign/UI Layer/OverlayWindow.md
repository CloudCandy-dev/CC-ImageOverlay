# OverlayWindow 詳細設計

## 1. 概要
オーバーレイウィンドウは、デスクトップ上に画像やメモを表示するためのウィンドウコンポーネントです。フレームレス、透過、最前面表示などの特殊な機能を提供します。

## 2. クラス定義

```python
class OverlayWindow(QWidget):
    """オーバーレイウィンドウクラス"""

    # シグナル定義
    geometryChanged = Signal(QRect)      # 位置・サイズ変更
    dragStarted = Signal(QPoint)         # ドラッグ開始
    dragFinished = Signal(QPoint)        # ドラッグ終了
    resizeStarted = Signal(QRect)        # リサイズ開始
    resizeFinished = Signal(QRect)       # リサイズ終了

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._view_model = None
        self._dragging = False
        self._resizing = False
        self._drag_start_pos = QPoint()
        self._original_geometry = QRect()
        self._resize_edge = None
        self._setup_ui()

    def initialize(self, view_model: OverlayViewModel) -> bool:
        """初期化"""
        try:
            self._view_model = view_model
            self._setup_connections()
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setMouseTracking(True)
            return True

        except Exception as e:
            logger.error(f"オーバーレイウィンドウの初期化に失敗: {e}")
            return False

    def set_content(self, content: dict) -> None:
        """コンテンツの設定"""
        try:
            if content.get("mode") == OverlayMode.IMAGE:
                self._set_image_content(content.get("image_path", ""))
            else:
                self._set_memo_content(
                    content.get("memo_text", ""),
                    content.get("memo_settings", {})
                )
        except Exception as e:
            logger.error(f"コンテンツの設定に失敗: {e}")

    def set_opacity(self, opacity: float) -> None:
        """透明度の設定"""
        try:
            self.setWindowOpacity(opacity)
        except Exception as e:
            logger.error(f"透明度の設定に失敗: {e}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウスボタン押下イベント"""
        if event.button() == Qt.LeftButton:
            self._handle_mouse_press(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウス移動イベント"""
        if self._dragging:
            self._handle_drag(event.globalPos())
        elif self._resizing:
            self._handle_resize(event.globalPos())
        else:
            self._update_cursor(event.pos())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウスボタン解放イベント"""
        if event.button() == Qt.LeftButton:
            self._handle_mouse_release(event.globalPos())

    def paintEvent(self, event: QPaintEvent) -> None:
        """描画イベント"""
        try:
            painter = QPainter(self)
            self._draw_content(painter)
            if self._view_model and self._view_model.is_editing:
                self._draw_resize_handles(painter)
        except Exception as e:
            logger.error(f"描画処理に失敗: {e}")

    def _setup_ui(self) -> None:
        """UI構築"""
        # ベースレイアウト
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # コンテンツ表示用ウィジェット
        self.content_widget = QLabel()
        self.content_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.content_widget)

    def _setup_connections(self) -> None:
        """シグナル接続"""
        if not self._view_model:
            return

        # ViewModelからのシグナル
        self._view_model.geometryChanged.connect(self.setGeometry)
        self._view_model.opacityChanged.connect(self.set_opacity)
        self._view_model.contentChanged.connect(self.set_content)
        self._view_model.visibilityChanged.connect(self.setVisible)

    def _set_image_content(self, image_path: str) -> None:
        """画像コンテンツの設定"""
        if not image_path:
            return

        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.content_widget.setPixmap(scaled_pixmap)

        except Exception as e:
            logger.error(f"画像コンテンツの設定に失敗: {e}")

    def _set_memo_content(self, text: str, settings: dict) -> None:
        """メモコンテンツの設定"""
        try:
            self.content_widget.setText(text)
            
            # フォント設定
            font = QFont()
            font.setPointSize(settings.get("font_size", 12))
            self.content_widget.setFont(font)
            
            # カラー設定
            self.content_widget.setStyleSheet(
                f"color: {settings.get('text_color', '#000000')};"
            )

        except Exception as e:
            logger.error(f"メモコンテンツの設定に失敗: {e}")

    def _handle_mouse_press(self, pos: QPoint) -> None:
        """マウスボタン押下処理"""
        edge = self._get_resize_edge(pos)
        if edge:
            self._start_resize(edge)
        else:
            self._start_drag(pos)

    def _handle_drag(self, global_pos: QPoint) -> None:
        """ドラッグ処理"""
        if not self._dragging:
            return

        try:
            delta = global_pos - self._drag_start_pos
            new_pos = self.pos() + delta
            self.move(new_pos)
            self._drag_start_pos = global_pos
            self.geometryChanged.emit(self.geometry())

        except Exception as e:
            logger.error(f"ドラッグ処理に失敗: {e}")

    def _handle_resize(self, global_pos: QPoint) -> None:
        """リサイズ処理"""
        if not self._resizing:
            return

        try:
            new_geometry = self._calculate_new_geometry(global_pos)
            if new_geometry.isValid():
                self.setGeometry(new_geometry)
                self.geometryChanged.emit(new_geometry)

        except Exception as e:
            logger.error(f"リサイズ処理に失敗: {e}")

    def _start_drag(self, pos: QPoint) -> None:
        """ドラッグ開始"""
        self._dragging = True
        self._drag_start_pos = self.mapToGlobal(pos)
        self.dragStarted.emit(self._drag_start_pos)

    def _start_resize(self, edge: Qt.Edge) -> None:
        """リサイズ開始"""
        self._resizing = True
        self._resize_edge = edge
        self._original_geometry = self.geometry()
        self.resizeStarted.emit(self._original_geometry)

    def _handle_mouse_release(self, global_pos: QPoint) -> None:
        """マウスボタン解放処理"""
        if self._dragging:
            self._dragging = False
            self.dragFinished.emit(global_pos)
        elif self._resizing:
            self._resizing = False
            self._resize_edge = None
            self.resizeFinished.emit(self.geometry())

    def _update_cursor(self, pos: QPoint) -> None:
        """カーソル形状の更新"""
        edge = self._get_resize_edge(pos)
        if edge in [Qt.LeftEdge, Qt.RightEdge]:
            self.setCursor(Qt.SizeHorCursor)
        elif edge in [Qt.TopEdge, Qt.BottomEdge]:
            self.setCursor(Qt.SizeVerCursor)
        elif edge in [Qt.TopLeftEdge, Qt.BottomRightEdge]:
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge in [Qt.TopRightEdge, Qt.BottomLeftEdge]:
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def _get_resize_edge(self, pos: QPoint) -> Optional[Qt.Edge]:
        """リサイズエッジの取得"""
        edge_size = 5
        x = pos.x()
        y = pos.y()
        width = self.width()
        height = self.height()

        # エッジ判定
        if x < edge_size and y < edge_size:
            return Qt.TopLeftEdge
        elif x >= width - edge_size and y < edge_size:
            return Qt.TopRightEdge
        elif x < edge_size and y >= height - edge_size:
            return Qt.BottomLeftEdge
        elif x >= width - edge_size and y >= height - edge_size:
            return Qt.BottomRightEdge
        elif x < edge_size:
            return Qt.LeftEdge
        elif x >= width - edge_size:
            return Qt.RightEdge
        elif y < edge_size:
            return Qt.TopEdge
        elif y >= height - edge_size:
            return Qt.BottomEdge
        
        return None

    def _calculate_new_geometry(self, global_pos: QPoint) -> QRect:
        """新しいジオメトリの計算"""
        if not self._resize_edge or not self._original_geometry:
            return self.geometry()

        try:
            local_pos = self.mapFromGlobal(global_pos)
            new_geometry = QRect(self._original_geometry)

            # エッジに応じてジオメトリを更新
            if self._resize_edge & Qt.LeftEdge:
                new_geometry.setLeft(local_pos.x())
            elif self._resize_edge & Qt.RightEdge:
                new_geometry.setRight(local_pos.x())
            
            if self._resize_edge & Qt.TopEdge:
                new_geometry.setTop(local_pos.y())
            elif self._resize_edge & Qt.BottomEdge:
                new_geometry.setBottom(local_pos.y())

            return new_geometry

        except Exception as e:
            logger.error(f"ジオメトリ計算に失敗: {e}")
            return self.geometry()

    def _draw_content(self, painter: QPainter) -> None:
        """コンテンツの描画"""
        try:
            if self._view_model and self._view_model.current_mode == OverlayMode.IMAGE:
                self._draw_image(painter)
            else:
                self._draw_memo(painter)

        except Exception as e:
            logger.error(f"コンテンツ描画に失敗: {e}")

    def _draw_image(self, painter: QPainter) -> None:
        """画像の描画"""
        try:
            if not self.content_widget.pixmap():
                return

            painter.drawPixmap(
                self.rect(),
                self.content_widget.pixmap(),
                self.content_widget.pixmap().rect()
            )

        except Exception as e:
            logger.error(f"画像描画に失敗: {e}")

    def _draw_memo(self, painter: QPainter) -> None:
        """メモの描画"""
        try:
            text = self.content_widget.text()
            if not text:
                return

            painter.setPen(self.content_widget.palette().text().color())
            painter.setFont(self.content_widget.font())
            painter.drawText(self.rect(), Qt.AlignCenter, text)

        except Exception as e:
            logger.error(f"メモ描画に失敗: {e}")

    def _draw_resize_handles(self, painter: QPainter) -> None:
        """リサイズハンドルの描画"""
        try:
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(Qt.white)
            
            handle_size = 6
            rect = self.rect()
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
            logger.error(f"リサイズハンドル描画に失敗: {e}")
```

## 3. 主要コンポーネント

### 3.1 ウィンドウ属性
- フレームレス
- 常に最前面
- 透過背景
- マウストラッキング

### 3.2 コンテンツ表示
- 画像表示
- メモテキスト表示
- 透明度制御
- サイズ自動調整

## 4. イベント処理

### 4.1 マウスイベント
- ドラッグ操作
- リサイズ操作
- カーソル形状変更
- 位置・サイズ通知

### 4.2 描画イベント
- コンテンツ描画
- リサイズハンドル描画
- 背景透過処理
- アンチエイリアス

## 5. 機能実装

### 5.1 位置制御
- ドラッグによる移動
- 座標範囲チェック
- モニター境界処理
- 位置スナップ

### 5.2 サイズ制御
- 8方向リサイズ
- アスペクト比維持
- 最小サイズ制限
- 自動調整

### 5.3 表示制御
- 表示/非表示切り替え
- フェードイン/アウト
- 透明度アニメーション
- Zオーダー管理

## 6. エラー処理

### 6.1 想定エラー
- 画像読み込みエラー
- メモリ不足
- 描画エラー
- リソース確保失敗

### 6.2 エラー対策
- 例外キャッチ
- ログ出力
- デフォルト値使用
- 状態復旧処理

## 7. 最適化

### 7.1 描画最適化
- ダブルバッファリング
- 部分更新
- キャッシュ利用
- 描画範囲制限

### 7.2 パフォーマンス
- イベントフィルタリング
- メモリ管理
- リソース解放
- 更新制御
