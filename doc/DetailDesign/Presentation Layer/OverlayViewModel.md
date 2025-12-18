# OverlayViewModel 詳細設計

## 1. 概要
オーバーレイウィンドウのUIロジックと状態管理を担当するビューモデルクラス。画像表示やメモ表示の制御、位置・サイズの管理、透明度の制御などを行う。

## 2. クラス定義

```python
class OverlayViewModel(QObject):
    """オーバーレイウィンドウビューモデル"""

    # シグナル定義
    geometryChanged = Signal(QRect)          # 位置・サイズ変更
    opacityChanged = Signal(float)          # 透明度変更
    contentChanged = Signal(dict)            # 表示内容変更
    visibilityChanged = Signal(bool)         # 表示状態変更
    modeChanged = Signal(OverlayMode)        # モード変更
    errorOccurred = Signal(str)              # エラー通知

    def __init__(self, overlay_manager: OverlayManager,
                 monitor_info: MonitorInfo,
                 config_manager: ConfigManager):
        super().__init__()
        self._overlay_manager = overlay_manager
        self._monitor_info = monitor_info
        self._config_manager = config_manager
        
        # 内部状態
        self._geometry = QRect()
        self._opacity = 0.8
        self._is_visible = False
        self._current_mode = OverlayMode.IMAGE
        self._current_monitor = "primary"
        self._content = {
            "image_path": "",
            "memo_text": "",
            "memo_settings": {}
        }

    def initialize(self) -> bool:
        """ビューモデルの初期化"""
        try:
            # 設定の読み込み
            settings = self._config_manager.load_overlay_settings()
            self._apply_settings(settings)
            
            # シグナル接続
            self._setup_signals()
            return True

        except Exception as e:
            logger.error(f"オーバーレイビューモデルの初期化に失敗: {e}")
            return False

    def set_visibility(self, visible: bool) -> None:
        """表示状態の設定"""
        try:
            if visible == self._is_visible:
                return

            self._is_visible = visible
            if visible:
                self._overlay_manager.show()
            else:
                self._overlay_manager.hide()
            
            self.visibilityChanged.emit(visible)

        except Exception as e:
            logger.error(f"表示状態の設定に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def set_geometry(self, x: int, y: int, width: int, height: int) -> None:
        """位置とサイズの設定"""
        try:
            new_geometry = QRect(x, y, width, height)
            if new_geometry == self._geometry:
                return

            self._geometry = new_geometry
            self._overlay_manager.set_position(x, y)
            self._overlay_manager.set_size(width, height)
            
            self.geometryChanged.emit(new_geometry)

        except Exception as e:
            logger.error(f"ジオメトリの設定に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def set_opacity(self, opacity: float) -> None:
        """透明度の設定"""
        try:
            opacity = max(0.1, min(1.0, opacity))
            if opacity == self._opacity:
                return

            self._opacity = opacity
            self._overlay_manager.set_opacity(opacity)
            self.opacityChanged.emit(opacity)

        except Exception as e:
            logger.error(f"透明度の設定に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def set_mode(self, mode: OverlayMode) -> None:
        """モードの設定"""
        try:
            if mode == self._current_mode:
                return

            self._current_mode = mode
            self._overlay_manager.switch_mode(mode)
            self.modeChanged.emit(mode)

        except Exception as e:
            logger.error(f"モードの設定に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def set_monitor(self, monitor_id: str) -> None:
        """表示モニターの設定"""
        try:
            if monitor_id == self._current_monitor:
                return

            monitor = self._monitor_info.get_monitor(monitor_id)
            if monitor:
                self._current_monitor = monitor_id
                self._overlay_manager.set_monitor(monitor)

        except Exception as e:
            logger.error(f"モニター設定に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def update_content(self, content_type: str, data: Any) -> None:
        """表示内容の更新"""
        try:
            if content_type == "image" and isinstance(data, str):
                self._content["image_path"] = data
                self._overlay_manager.set_image(data)
            elif content_type == "memo" and isinstance(data, str):
                self._content["memo_text"] = data
                self._overlay_manager.set_memo_text(data)
            elif content_type == "memo_settings" and isinstance(data, dict):
                self._content["memo_settings"].update(data)
                self._overlay_manager.update_memo_settings(data)

            self.contentChanged.emit(self._content)

        except Exception as e:
            logger.error(f"コンテンツ更新に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def _apply_settings(self, settings: OverlaySettings) -> None:
        """設定の適用"""
        self._geometry = QRect(
            settings.position.x(),
            settings.position.y(),
            settings.size,
            settings.size
        )
        self._opacity = settings.opacity
        self._is_visible = settings.is_visible
        self._current_mode = settings.mode
        self._current_monitor = settings.monitor
        self._content["memo_text"] = settings.memo_text
        self._content["memo_settings"] = settings.memo_settings

    def _setup_signals(self) -> None:
        """シグナル接続"""
        # オーバーレイマネージャからのシグナルを接続
        self._overlay_manager.visibility_changed.connect(
            lambda v: self.visibilityChanged.emit(v)
        )
        self._overlay_manager.geometry_changed.connect(
            lambda g: self.geometryChanged.emit(g)
        )
```

## 3. 主要コンポーネントの説明

### 3.1 状態管理
- `_geometry`: オーバーレイウィンドウの位置とサイズ
- `_opacity`: 透明度（0.1～1.0）
- `_is_visible`: 表示状態
- `_current_mode`: 現在のモード（画像/メモ）
- `_current_monitor`: 表示中のモニターID
- `_content`: 表示コンテンツ情報

### 3.2 シグナル
- `geometryChanged`: 位置・サイズ変更通知
- `opacityChanged`: 透明度変更通知
- `contentChanged`: コンテンツ変更通知
- `visibilityChanged`: 表示状態変更通知
- `modeChanged`: モード変更通知
- `errorOccurred`: エラー発生通知

### 3.3 主要メソッド
- `initialize()`: 初期化処理
- `set_visibility()`: 表示状態制御
- `set_geometry()`: 位置・サイズ制御
- `set_opacity()`: 透明度制御
- `set_mode()`: モード切り替え
- `set_monitor()`: 表示モニター切り替え
- `update_content()`: コンテンツ更新

## 4. エラー処理

### 4.1 エラーカテゴリ
- 初期化エラー
- 設定適用エラー
- 表示制御エラー
- コンテンツ更新エラー

### 4.2 エラーハンドリング
- すべての操作メソッドで例外をキャッチ
- エラーログを出力
- `errorOccurred`シグナルでUIに通知
- エラー発生時も一貫した状態を維持

## 5. 設定の永続化

### 5.1 保存タイミング
- ジオメトリ変更時
- 透明度変更時
- モード切り替え時
- モニター変更時
- コンテンツ更新時

### 5.2 保存データ
```json
{
    "position": {
        "x": number,
        "y": number
    },
    "size": number,
    "opacity": number,
    "is_visible": boolean,
    "mode": string,
    "monitor": string,
    "memo_text": string,
    "memo_settings": {
        "font_size": number,
        "background_color": string,
        "text_color": string
    }
}
```
