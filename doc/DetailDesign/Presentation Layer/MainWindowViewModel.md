# MainWindowViewModel 詳細設計

## 1. 概要
メインウィンドウのUIロジックと状態管理を担当するビューモデルクラス。設定の管理、オーバーレイの制御、各種マネージャとの連携を行う。

## 2. クラス定義

```python
class MainWindowViewModel(QObject):
    """メインウィンドウビューモデル"""

    # シグナル定義
    windowStateChanged = Signal(dict)      # ウィンドウ状態変更
    overlayStateChanged = Signal(dict)     # オーバーレイ状態変更
    settingsChanged = Signal(str, object)  # 設定変更
    errorOccurred = Signal(str)            # エラー通知

    def __init__(self, config_manager: ConfigManager,
                 overlay_manager: OverlayManager,
                 language_manager: LanguageManager,
                 theme_manager: ThemeManager):
        super().__init__()
        self._config_manager = config_manager
        self._overlay_manager = overlay_manager
        self._language_manager = language_manager
        self._theme_manager = theme_manager
        
        self._window_geometry = QRect()
        self._is_maximized = False
        self._current_image_path = ""
        self._current_memo_text = ""
        self._current_mode = OverlayMode.IMAGE

    async def initialize(self) -> Result[None]:
        """ビューモデルの初期化
        Returns:
            Result[None]: 初期化結果
        """
        try:
            # 設定の読み込み
            settings_result = await self._load_settings()
            if not settings_result.success:
                return settings_result
            
            # 各マネージャの初期化
            init_results = await asyncio.gather(
                self._language_manager.initialize(),
                self._theme_manager.initialize(),
                self._overlay_manager.initialize()
            )
            
            if not all(result.success for result in init_results):
                # 最初に見つかったエラーを返す
                for result in init_results:
                    if not result.success:
                        return result

            # シグナル接続
            await self._setup_signals()
            return Result(success=True, data=None)
            
        except Exception as e:
            error_msg = f"ビューモデルの初期化に失敗: {e}"
            logger.error(error_msg)
            return Result(
                success=False,
                error=error_msg,
                error_code="VIEW_MODEL_INIT_ERROR"
            )
            return True

        except Exception as e:
            logger.error(f"メインウィンドウビューモデルの初期化に失敗: {e}")
            return False

    def set_overlay_mode(self, mode: OverlayMode) -> None:
        """オーバーレイモードの設定"""
        try:
            if mode == self._current_mode:
                return

            self._current_mode = mode
            self._overlay_manager.set_mode(mode)
            self._config_manager.set_value("app_settings.overlay_mode", mode.value)
            self.overlayStateChanged.emit(self._get_overlay_state())

        except Exception as e:
            logger.error(f"オーバーレイモード設定に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def load_image(self, file_path: str) -> bool:
        """画像の読み込み"""
        try:
            if not self._overlay_manager.set_image(file_path):
                return False

            self._current_image_path = file_path
            self._config_manager.set_value(
                "app_settings.last_image_path", file_path
            )
            return True

        except Exception as e:
            logger.error(f"画像読み込みに失敗: {e}")
            self.errorOccurred.emit(str(e))
            return False

    def set_memo_text(self, text: str) -> bool:
        """メモテキストの設定"""
        try:
            if not self._overlay_manager.set_memo_text(text):
                return False

            self._current_memo_text = text
            self._config_manager.set_value(
                "app_settings.last_memo_text", text
            )
            return True

        except Exception as e:
            logger.error(f"メモテキスト設定に失敗: {e}")
            self.errorOccurred.emit(str(e))
            return False

    def set_window_geometry(self, geometry: QRect) -> None:
        """ウィンドウジオメトリの設定"""
        try:
            self._window_geometry = geometry
            self._config_manager.set_value("app_settings.window", {
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height()
            })
            self.windowStateChanged.emit(self._get_window_state())

        except Exception as e:
            logger.error(f"ウィンドウジオメトリ設定に失敗: {e}")
            self.errorOccurred.emit(str(e))

    def toggle_overlay(self) -> None:
        """オーバーレイの表示/非表示切り替え"""
        try:
            self._overlay_manager.toggle_visibility()
        except Exception as e:
            logger.error(f"オーバーレイ表示切り替えに失敗: {e}")
            self.errorOccurred.emit(str(e))

    def _load_window_settings(self) -> None:
        """ウィンドウ設定の読み込み"""
        try:
            window_settings = self._config_manager.get_value(
                "app_settings.window", {}
            )
            self._window_geometry = QRect(
                window_settings.get("x", 100),
                window_settings.get("y", 100),
                window_settings.get("width", 800),
                window_settings.get("height", 600)
            )
            self._is_maximized = window_settings.get("maximized", False)

        except Exception as e:
            logger.error(f"ウィンドウ設定の読み込みに失敗: {e}")
            self._window_geometry = QRect(100, 100, 800, 600)
            self._is_maximized = False

    def _load_overlay_settings(self) -> None:
        """オーバーレイ設定の読み込み"""
        try:
            self._current_image_path = self._config_manager.get_value(
                "app_settings.last_image_path", ""
            )
            self._current_memo_text = self._config_manager.get_value(
                "app_settings.last_memo_text", ""
            )
            mode_value = self._config_manager.get_value(
                "app_settings.overlay_mode", OverlayMode.IMAGE.value
            )
            self._current_mode = OverlayMode(mode_value)

        except Exception as e:
            logger.error(f"オーバーレイ設定の読み込みに失敗: {e}")
            self._current_mode = OverlayMode.IMAGE

    def _setup_signals(self) -> None:
        """シグナル接続の設定"""
        try:
            # オーバーレイマネージャからのシグナル
            self._overlay_manager.visibilityChanged.connect(
                lambda visible: self.overlayStateChanged.emit(
                    self._get_overlay_state()
                )
            )
            # 言語マネージャからのシグナル
            self._language_manager.languageChanged.connect(
                lambda lang: self.settingsChanged.emit("language", lang)
            )
            # テーママネージャからのシグナル
            self._theme_manager.themeChanged.connect(
                lambda theme: self.settingsChanged.emit("theme", theme)
            )

        except Exception as e:
            logger.error(f"シグナル接続の設定に失敗: {e}")

    def _get_window_state(self) -> dict:
        """ウィンドウ状態の取得"""
        return {
            "geometry": self._window_geometry,
            "maximized": self._is_maximized
        }

    def _get_overlay_state(self) -> dict:
        """オーバーレイ状態の取得"""
        return {
            "visible": self._overlay_manager.is_visible,
            "mode": self._current_mode,
            "image_path": self._current_image_path,
            "memo_text": self._current_memo_text
        }
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal, QRect
from ..services.config_manager import ConfigManager
from ..services.logging_service import logger
from ..core.overlay_manager import OverlayManager
from ..settings.language_manager import LanguageManager
from ..settings.theme_manager import ThemeManager
from ..models.overlay_mode import OverlayMode
```

## 4. 主要機能の詳細

### 4.1 初期化処理
1. 設定の読み込み
2. マネージャの初期化
3. シグナルの接続
4. 状態の復元
5. エラー処理

### 4.2 状態管理
1. ウィンドウ状態
2. オーバーレイ状態
3. 画像/メモ管理
4. モード制御
5. 設定の永続化

### 4.3 イベント処理
1. ユーザー操作
2. 設定変更
3. エラー通知
4. 状態更新
5. UI更新

## 5. 設定管理

### 5.1 永続化項目
- ウィンドウ位置とサイズ
- 最後に使用した画像パス
- メモテキスト
- オーバーレイモード
- 言語設定
- テーマ設定

### 5.2 設定の同期
- 即時保存
- 自動復元
- 整合性チェック
- デフォルト値
- エラー処理

## 6. エラー処理

### 6.1 想定されるエラー
- 設定読み込み失敗
- マネージャ初期化失敗
- 画像読み込みエラー
- メモリ不足
- ファイルI/Oエラー

### 6.2 エラー処理方針
- エラーログの記録
- デフォルト値の使用
- ユーザーへの通知
- 状態の復旧
- エラー分離

## 7. パフォーマンス

### 7.1 最適化
- 不要な更新の抑制
- メモリ使用量の制御
- 遅延初期化
- キャッシュ活用
- バッチ処理

### 7.2 応答性
- 非同期処理
- UI更新の最適化
- リソース管理
- 状態変更の制御
- イベントの調整

## 8. 拡張性

### 8.1 機能拡張
- プラグインサポート
- カスタム設定
- イベントハンドラ
- 状態監視
- デバッグサポート

### 8.2 カスタマイズ
- ユーザー設定
- ホットキー
- 表示オプション
- 動作モード
- エラー処理
