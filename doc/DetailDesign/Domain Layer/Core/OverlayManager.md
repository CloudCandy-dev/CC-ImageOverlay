# OverlayManager 詳細設計

## 1. 概要
オーバーレイウィンドウの状態管理と制御を担当する中核クラス。画像モードとメモモードの両方に対応し、表示状態、位置、サイズなどを管理する。

## 2. クラス定義

```python
class OverlayManager:
    """オーバーレイウィンドウを管理するクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        self._config_manager = config_manager
        self._overlay_window = None
        self._current_mode = OverlayMode.IMAGE
        self._is_visible = False
        self._current_monitor = None
        self._settings = OverlaySettings()

    @property
    def current_mode(self) -> OverlayMode:
        """現在のオーバーレイモード（画像/メモ）を取得"""
        return self._current_mode

    @property
    def is_visible(self) -> bool:
        """オーバーレイの表示状態を取得"""
        return self._is_visible

    def initialize(self) -> None:
        """初期化処理"""
        self._load_settings()
        self._create_overlay_window()

    def toggle_visibility(self) -> None:
        """オーバーレイの表示/非表示を切り替え"""
        if self._is_visible:
            self.hide()
        else:
            self.show()

    def show(self) -> None:
        """オーバーレイを表示"""
        if self._overlay_window:
            self._overlay_window.show()
            self._is_visible = True
            self._save_settings()

    def hide(self) -> None:
        """オーバーレイを非表示"""
        if self._overlay_window:
            self._overlay_window.hide()
            self._is_visible = False
            self._save_settings()

    def switch_mode(self, mode: OverlayMode) -> None:
        """オーバーレイモードを切り替え"""
        if self._current_mode != mode:
            self._current_mode = mode
            self._update_overlay_content()
            self._save_settings()

    def set_position(self, x: int, y: int) -> None:
        """オーバーレイの位置を設定"""
        if self._overlay_window:
            self._overlay_window.move(x, y)
            self._settings.position = (x, y)
            self._delayed_save_settings()

    def set_size(self, width: int, height: int) -> None:
        """オーバーレイのサイズを設定"""
        if self._overlay_window:
            self._overlay_window.resize(width, height)
            self._settings.size = (width, height)
            self._delayed_save_settings()

    def set_opacity(self, opacity: float) -> None:
        """オーバーレイの透明度を設定"""
        if self._overlay_window:
            self._overlay_window.setWindowOpacity(opacity)
            self._settings.opacity = opacity
            self._delayed_save_settings()

    def set_monitor(self, monitor: Monitor) -> None:
        """表示モニターを変更"""
        if self._current_monitor != monitor:
            self._current_monitor = monitor
            self._adjust_position_for_monitor()
            self._save_settings()

    def _load_settings(self) -> None:
        """設定を読み込み"""
        self._settings = self._config_manager.load_overlay_settings()

    def _save_settings(self) -> None:
        """設定を保存"""
        self._config_manager.save_overlay_settings(self._settings)

    def _delayed_save_settings(self) -> None:
        """設定の遅延保存（位置やサイズの変更時）"""
        # 3秒後に保存を実行
        QTimer.singleShot(3000, self._save_settings)

    def _create_overlay_window(self) -> None:
        """オーバーレイウィンドウを作成"""
        self._overlay_window = OverlayWindow(self._settings)

    def _update_overlay_content(self) -> None:
        """オーバーレイの内容を更新"""
        if self._overlay_window:
            self._overlay_window.update_content(self._current_mode)

    def _adjust_position_for_monitor(self) -> None:
        """モニター変更時の位置調整"""
        if self._overlay_window and self._current_monitor:
            new_pos = self._calculate_monitor_position()
            self.set_position(new_pos.x(), new_pos.y())
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from enum import Enum
from PySide6.QtCore import QTimer, QPoint
from .config_manager import ConfigManager
from .overlay_window import OverlayWindow
from ..entities.overlay_settings import OverlaySettings
from ..entities.monitor import Monitor
```

### 3.2 列挙型定義
```python
class OverlayMode(Enum):
    """オーバーレイのモード"""
    IMAGE = "image"
    MEMO = "memo"
```

## 4. 主要メソッドの処理詳細

### 4.1 初期化処理（initialize）
1. ConfigManagerから設定を読み込み
2. 設定に基づいてオーバーレイウィンドウを作成
3. 前回の状態（位置、サイズ、モード）を復元

### 4.2 モード切替処理（switch_mode）
1. モードの変更を検証
2. 現在のモードを更新
3. オーバーレイウィンドウの内容を更新
4. 設定を保存

### 4.3 モニター変更処理（set_monitor）
1. 新しいモニターの有効性を確認
2. 現在のモニターを更新
3. オーバーレイの位置をモニターに合わせて調整
4. 設定を保存

### 4.4 設定の遅延保存（_delayed_save_settings）
1. 既存の保存タイマーをキャンセル（存在する場合）
2. 新しい保存タイマーを設定（3秒）
3. タイマー満了時に設定を保存

## 5. エラー処理

### 5.1 想定されるエラー
- 設定ファイルの読み込み失敗
- オーバーレイウィンドウの作成失敗
- モニター情報の取得失敗
- 無効な座標やサイズの指定

### 5.2 エラー処理方針
- 設定読み込みエラー → デフォルト値を使用
- ウィンドウ作成エラー → エラーをログに記録し、再試行
- モニター関連エラー → プライマリモニターにフォールバック
- 無効な値 → 有効な範囲に丸める

## 6. スレッド安全性

- UI操作は必ずメインスレッドで実行
- 設定の保存は非同期で実行可能
- 複数のオーバーレイインスタンスは作成不可（シングルトン）

## 7. パフォーマンス考慮事項

- 頻繁な位置・サイズ変更時の設定保存を遅延実行
- オーバーレイウィンドウの更新は必要な場合のみ実行
- モニター情報のキャッシュ化
