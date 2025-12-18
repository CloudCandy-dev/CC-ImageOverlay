# HotkeyService 詳細設計

## 1. 概要
グローバルホットキーの登録と管理を担当するサービスクラス。Windowsのグローバルホットキー機能を利用して、アプリケーションがフォーカスされていない状態でもホットキーを検出する。

## 2. クラス定義

```python
class HotkeyService:
    """グローバルホットキー管理サービスクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        self._config_manager = config_manager
        self._registered_hotkeys = {}
        self._callback_map = {}
        self._win_event_filter = None

    def initialize(self) -> None:
        """ホットキーサービスの初期化"""
        self._win_event_filter = WindowsEventFilter()
        self._win_event_filter.hotkey_pressed.connect(self._handle_hotkey)
        self._register_default_hotkeys()

    def register_hotkey(self, key: str, modifiers: list[str], 
                       callback: Callable[[], None]) -> bool:
        """ホットキーの登録"""
        try:
            # モディファイアキーの変換
            mod_flags = self._convert_modifiers(modifiers)
            # 仮想キーコードの取得
            vk_code = self._get_virtual_keycode(key)
            
            # ホットキーIDの生成
            hotkey_id = self._generate_hotkey_id(vk_code, mod_flags)
            
            # 既存の登録があれば解除
            if hotkey_id in self._registered_hotkeys:
                self.unregister_hotkey(hotkey_id)
            
            # ホットキーの登録
            if not win32gui.RegisterHotKey(
                None, hotkey_id, mod_flags, vk_code
            ):
                raise WindowsError("ホットキーの登録に失敗しました")
            
            # 登録情報の保存
            self._registered_hotkeys[hotkey_id] = (vk_code, mod_flags)
            self._callback_map[hotkey_id] = callback
            
            return True
            
        except Exception as e:
            logger.error(f"ホットキー登録エラー: {e}")
            return False

    def unregister_hotkey(self, hotkey_id: int) -> bool:
        """ホットキーの登録解除"""
        try:
            if hotkey_id in self._registered_hotkeys:
                win32gui.UnregisterHotKey(None, hotkey_id)
                del self._registered_hotkeys[hotkey_id]
                del self._callback_map[hotkey_id]
                return True
            return False
        except Exception as e:
            logger.error(f"ホットキー登録解除エラー: {e}")
            return False

    def unregister_all(self) -> None:
        """全てのホットキーを登録解除"""
        for hotkey_id in list(self._registered_hotkeys.keys()):
            self.unregister_hotkey(hotkey_id)

    def _register_default_hotkeys(self) -> None:
        """デフォルトホットキーの登録"""
        settings = self._config_manager.get("hotkey_settings", {})
        toggle_overlay = settings.get("toggle_overlay", {
            "key": "O",
            "modifiers": ["Alt", "Shift"]
        })
        self.register_hotkey(
            toggle_overlay["key"],
            toggle_overlay["modifiers"],
            self._on_toggle_overlay
        )

    def _handle_hotkey(self, hotkey_id: int) -> None:
        """ホットキーイベントの処理"""
        if hotkey_id in self._callback_map:
            try:
                self._callback_map[hotkey_id]()
            except Exception as e:
                logger.error(f"ホットキーコールバックエラー: {e}")

    def _convert_modifiers(self, modifiers: list[str]) -> int:
        """モディファイアキーの変換"""
        flags = 0
        for mod in modifiers:
            if mod.lower() == "alt":
                flags |= win32con.MOD_ALT
            elif mod.lower() == "ctrl":
                flags |= win32con.MOD_CONTROL
            elif mod.lower() == "shift":
                flags |= win32con.MOD_SHIFT
            elif mod.lower() == "win":
                flags |= win32con.MOD_WIN
        return flags

    def _get_virtual_keycode(self, key: str) -> int:
        """仮想キーコードの取得"""
        # 単一文字の場合
        if len(key) == 1:
            return ord(key.upper())
        
        # 特殊キーの場合
        key_map = {
            "F1": win32con.VK_F1,
            "F2": win32con.VK_F2,
            # 他の特殊キーも同様に定義
        }
        return key_map.get(key, 0)

    def _generate_hotkey_id(self, vk_code: int, mod_flags: int) -> int:
        """ユニークなホットキーIDの生成"""
        return vk_code | (mod_flags << 8)

    def _on_toggle_overlay(self) -> None:
        """オーバーレイ表示切り替えのデフォルトコールバック"""
        pass  # 実際の処理は外部から設定される
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from typing import Callable
import win32gui
import win32con
from PySide6.QtCore import QObject, Signal
from .config_manager import ConfigManager
from ..services.logging_service import logger
```

## 4. 主要コンポーネント

### 4.1 WindowsEventFilter クラス
```python
class WindowsEventFilter(QObject):
    """Windowsイベントフィルタ"""
    
    hotkey_pressed = Signal(int)  # ホットキーID

    def nativeEventFilter(self, eventType, message):
        if eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == win32con.WM_HOTKEY:
                self.hotkey_pressed.emit(msg.wParam)
        return False, 0
```

## 5. 主要機能の詳細

### 5.1 ホットキー登録プロセス
1. モディファイアキーの変換
2. 仮想キーコードの取得
3. ユニークIDの生成
4. Windowsへの登録
5. コールバックの保存

### 5.2 イベント処理フロー
1. Windowsイベントの受信
2. ホットキーイベントの判別
3. 登録済みコールバックの検索
4. コールバック実行

## 6. エラー処理

### 6.1 想定されるエラー
- 無効なキー指定
- 重複するホットキー
- 登録失敗
- コールバックエラー

### 6.2 エラー処理方針
- 無効なキー → デフォルト値使用
- 重複 → 既存の登録を解除
- 登録失敗 → エラーログ記録
- コールバックエラー → 例外捕捉とログ記録

## 7. 制限事項

### 7.1 Windows依存
- Windows APIに依存
- 他OSは未対応
- システムレベルの権限が必要

### 7.2 キーの制限
- システム予約キーは使用不可
- 特定のキーの組み合わせは制限
- 他アプリとの競合の可能性

## 8. パフォーマンス考慮事項

### 8.1 リソース管理
- 不要なホットキーの解除
- メモリリークの防止
- イベントフィルタの効率化

### 8.2 イベント処理
- イベントの高速判定
- コールバックの軽量化
- エラー処理のオーバーヘッド最小化
