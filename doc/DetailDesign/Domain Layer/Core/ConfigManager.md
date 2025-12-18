# ConfigManager 詳細設計

## 1. 概要
アプリケーション全体の設定を管理する中核クラス。設定の読み込み、保存、検証を担当し、JSONファイルとの入出力を処理する。

## 2. クラス定義

```python
class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "configs/config.json"):
        self._config_path = config_path
        self._settings = None
        self._save_timer = None
        self._is_dirty = False

    @property
    def settings(self) -> dict:
        """現在の設定を取得"""
        return self._settings

    def initialize(self) -> None:
        """初期化処理"""
        self._load_settings()
        self._validate_settings()

    def save(self) -> None:
        """設定を即時保存"""
        self._save_settings()
        self._is_dirty = False

    def delayed_save(self, delay_ms: int = 3000) -> None:
        """設定を遅延保存"""
        self._is_dirty = True
        if self._save_timer:
            self._save_timer.stop()
        self._save_timer = QTimer()
        self._save_timer.singleShot(delay_ms, self.save)

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any, delayed: bool = True) -> None:
        """設定値を更新"""
        if self._settings.get(key) != value:
            self._settings[key] = value
            if delayed:
                self.delayed_save()
            else:
                self.save()

    def load_overlay_settings(self) -> OverlaySettings:
        """オーバーレイの設定を読み込み"""
        overlay_dict = self._settings.get("overlay_settings", {})
        return OverlaySettings.from_dict(overlay_dict)

    def save_overlay_settings(self, settings: OverlaySettings) -> None:
        """オーバーレイの設定を保存"""
        self._settings["overlay_settings"] = settings.to_dict()
        self.delayed_save()

    def _load_settings(self) -> None:
        """設定ファイルから読み込み"""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._settings = json.load(f)
        except FileNotFoundError:
            self._settings = self._create_default_settings()
            self.save()
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルの解析に失敗: {e}")
            self._settings = self._create_default_settings()
            self.save()

    def _save_settings(self) -> None:
        """設定をファイルに保存"""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"設定の保存に失敗: {e}")

    def _validate_settings(self) -> None:
        """設定値の検証"""
        self._validate_window_settings()
        self._validate_overlay_settings()
        self._validate_hotkey_settings()

    def _create_default_settings(self) -> dict:
        """デフォルト設定を作成"""
        return {
            "app_settings": {
                "window": {
                    "x": 100,
                    "y": 100,
                    "width": 800,
                    "height": 600
                },
                "language": "Japanese.json",
                "theme": "dark.qss",
                "last_image_path": ""
            },
            "overlay_settings": {
                "position": {"x": 0, "y": 0},
                "size": {"width": 400, "height": 300},
                "opacity": 0.8,
                "rotation": 0,
                "monitor": "primary"
            },
            "hotkey_settings": {
                "toggle_overlay": {
                    "key": "O",
                    "modifiers": ["Alt", "Shift"]
                }
            }
        }
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import json
from typing import Any
from PySide6.QtCore import QTimer
from ..entities.overlay_settings import OverlaySettings
from ..services.logging_service import logger
```

## 4. 主要メソッドの処理詳細

### 4.1 初期化処理（initialize）
1. 設定ファイルの存在確認
2. ファイルからの設定読み込み
3. 設定値の検証
4. 必要に応じてデフォルト値の適用

### 4.2 設定の保存処理（save/delayed_save）
1. 設定値の変更フラグ確認
2. 既存の保存タイマーのキャンセル（遅延保存の場合）
3. 設定のJSON形式への変換
4. ファイルへの書き込み

### 4.3 設定の検証（_validate_settings）
1. ウィンドウ設定の範囲チェック
2. オーバーレイ設定の有効性確認
3. ホットキー設定の形式確認
4. 不正な値の補正

## 5. エラー処理

### 5.1 想定されるエラー
- 設定ファイルが存在しない
- 設定ファイルの形式が不正
- ファイルの読み書き権限がない
- 設定値が範囲外

### 5.2 エラー処理方針
- FileNotFoundError → デフォルト設定を作成
- JSONDecodeError → デフォルト設定を使用
- 権限エラー → エラーログを記録
- 不正な値 → デフォルト値に補正

## 6. スレッド安全性

- 設定の読み書きは排他制御を実装
- 遅延保存は非同期で実行
- インスタンスはシングルトンとして実装

## 7. パフォーマンス考慮事項

- 設定の頻繁な保存を防ぐため遅延保存を実装
- 設定のキャッシュ化
- 必要な部分のみを更新する差分保存
