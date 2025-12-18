# CustomControls 詳細設計

## 1. 概要
CustomControlsは、アプリケーション固有のカスタムUIコントロールを提供するコンポーネント群です。メインウィンドウやオーバーレイウィンドウで使用される特殊な入力や表示のためのウィジェットを実装します。

## 2. コンポーネント一覧

### 2.1 OpacitySlider
```python
class OpacitySlider(QSlider):
    """透明度調整スライダー"""

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UI設定"""
        self.setRange(10, 100)  # 10%～100%
        self.setValue(80)       # デフォルト80%
        self.setFixedWidth(150)
        self.setToolTip("透明度")

    def value_as_float(self) -> float:
        """float値として取得（0.1～1.0）"""
        return self.value() / 100.0

    def set_from_float(self, value: float) -> None:
        """float値から設定（0.1～1.0）"""
        self.setValue(int(value * 100))
```

### 2.2 ColorButton
```python
class ColorButton(QPushButton):
    """カラー選択ボタン"""
    
    colorChanged = Signal(QColor)  # 色変更シグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(Qt.white)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UI設定"""
        self.setFixedSize(30, 30)
        self.clicked.connect(self._show_color_dialog)
        self.update_style()

    def get_color(self) -> QColor:
        """現在の色を取得"""
        return self._color

    def set_color(self, color: QColor) -> None:
        """色を設定"""
        if color != self._color:
            self._color = color
            self.update_style()
            self.colorChanged.emit(color)

    def update_style(self) -> None:
        """スタイルの更新"""
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self._color.name()};
                border: 2px solid #808080;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #404040;
            }}
            """
        )

    def _show_color_dialog(self) -> None:
        """カラーダイアログを表示"""
        color = QColorDialog.getColor(
            self._color,
            self,
            "色を選択",
            QColorDialog.ShowAlphaChannel
        )
        if color.isValid():
            self.set_color(color)
```

### 2.3 MonitorComboBox
```python
class MonitorComboBox(QComboBox):
    """モニター選択コンボボックス"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitor_info = None
        self._setup_ui()

    def initialize(self, monitor_info: MonitorInfo) -> bool:
        """初期化"""
        try:
            self._monitor_info = monitor_info
            self._update_monitor_list()
            return True

        except Exception as e:
            logger.error(f"モニター選択の初期化に失敗: {e}")
            return False

    def _setup_ui(self) -> None:
        """UI設定"""
        self.setFixedWidth(200)
        self.setToolTip("表示モニターを選択")

    def _update_monitor_list(self) -> None:
        """モニターリストの更新"""
        try:
            self.clear()
            if not self._monitor_info:
                return

            monitors = self._monitor_info.get_monitor_list()
            for monitor_id in monitors:
                geometry = self._monitor_info.get_monitor_geometry(monitor_id)
                self.addItem(
                    f"Monitor {monitor_id} ({geometry.width()}x{geometry.height()})",
                    monitor_id
                )

        except Exception as e:
            logger.error(f"モニターリストの更新に失敗: {e}")
```

### 2.4 ResizableLabel
```python
class ResizableLabel(QLabel):
    """リサイズ可能なラベル"""

    resized = Signal(QSize)  # サイズ変更シグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resize_active = False
        self._resize_start = QPoint()
        self._original_size = QSize()
        self.setMouseTracking(True)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウスボタン押下イベント"""
        if event.button() == Qt.LeftButton and self._is_on_corner(event.pos()):
            self._start_resize(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウス移動イベント"""
        if self._resize_active:
            self._handle_resize(event.pos())
        else:
            self._update_cursor(event.pos())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウスボタン解放イベント"""
        if event.button() == Qt.LeftButton and self._resize_active:
            self._end_resize()

    def _is_on_corner(self, pos: QPoint) -> bool:
        """コーナー判定"""
        corner_size = 10
        rect = self.rect()
        return (
            QRect(
                rect.right() - corner_size,
                rect.bottom() - corner_size,
                corner_size,
                corner_size
            ).contains(pos)
        )

    def _start_resize(self, pos: QPoint) -> None:
        """リサイズ開始"""
        self._resize_active = True
        self._resize_start = pos
        self._original_size = self.size()

    def _handle_resize(self, pos: QPoint) -> None:
        """リサイズ処理"""
        if not self._resize_active:
            return

        try:
            # サイズ変更を計算
            delta = pos - self._resize_start
            new_size = QSize(
                max(30, self._original_size.width() + delta.x()),
                max(30, self._original_size.height() + delta.y())
            )
            
            # サイズを更新
            self.resize(new_size)
            self.resized.emit(new_size)

        except Exception as e:
            logger.error(f"リサイズ処理に失敗: {e}")

    def _end_resize(self) -> None:
        """リサイズ終了"""
        self._resize_active = False
        self._resize_start = QPoint()
        self._original_size = QSize()

    def _update_cursor(self, pos: QPoint) -> None:
        """カーソル形状の更新"""
        if self._is_on_corner(pos):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
```

## 3. 共通機能

### 3.1 スタイリング
- テーマに応じた外観の変更
- ホバー状態の視覚的フィードバック
- フォーカス状態の表示
- カスタムボーダーとラウンド処理

### 3.2 イベント処理
- マウスイベントの処理
- キーボードイベントの処理
- フォーカスイベントの処理
- 状態変更の通知

### 3.3 アクセシビリティ
- ツールチップのサポート
- キーボードナビゲーション
- スクリーンリーダー対応
- ハイコントラストモード対応

## 4. エラー処理

### 4.1 入力検証
- 範囲チェック
- 型チェック
- NULL値の処理
- 不正値の防止

### 4.2 状態管理
- 不正状態の検出
- デフォルト値の使用
- 状態の復元
- エラー通知

## 5. カスタマイズ機能

### 5.1 外観のカスタマイズ
- カラースキームの変更
- サイズの調整
- フォントの設定
- ボーダースタイルの変更

### 5.2 動作のカスタマイズ
- イベントハンドリング
- アニメーション設定
- 入力制限
- 表示形式

## 6. 最適化

### 6.1 描画最適化
- 部分更新の活用
- ダブルバッファリング
- リソースのキャッシュ
- 描画範囲の最適化

### 6.2 メモリ管理
- リソースの適切な解放
- メモリ使用量の最小化
- キャッシュサイズの制御
- 循環参照の防止
