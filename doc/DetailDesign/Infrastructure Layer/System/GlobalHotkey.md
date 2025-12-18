# GlobalHotkey 詳細設計

## 1. 概要
WindowsのWin32 APIを使用してグローバルホットキーを管理するクラス。システムレベルでのホットキーの登録、解除、イベント検出を担当する。

## 2. クラス定義

```python
class GlobalHotkey:
    """Windowsグローバルホットキー管理クラス"""
    
    def __init__(self):
        self._registered_hotkeys = {}
        self._callback_map = {}
        self._win_message_handler = None

    def initialize(self) -> bool:
        """グローバルホットキーシステムの初期化"""
        try:
            self._win_message_handler = self._create_message_handler()
            return True
        except Exception as e:
            logger.error(f"ホットキーシステムの初期化に失敗: {e}")
            return False

    def register_hotkey(self, 
                       hotkey_id: int, 
                       key: str, 
                       modifiers: list[str]) -> bool:
        """ホットキーの登録"""
        try:
            # モディファイアフラグの変換
            mod_flags = self._convert_modifiers(modifiers)
            # 仮想キーコードの取得
            vk_code = self._get_virtual_keycode(key)
            
            # 既存のホットキーがあれば解除
            if hotkey_id in self._registered_hotkeys:
                self.unregister_hotkey(hotkey_id)
            
            # Win32 APIでホットキーを登録
            if not win32gui.RegisterHotKey(None, hotkey_id, mod_flags, vk_code):
                raise WindowsError(f"ホットキー登録失敗: ID={hotkey_id}")
            
            # 登録情報を保存
            self._registered_hotkeys[hotkey_id] = (vk_code, mod_flags)
            return True
            
        except Exception as e:
            logger.error(f"ホットキー登録エラー: {e}")
            return False

    def unregister_hotkey(self, hotkey_id: int) -> bool:
        """ホットキーの登録解除"""
        try:
            if hotkey_id in self._registered_hotkeys:
                if not win32gui.UnregisterHotKey(None, hotkey_id):
                    raise WindowsError(f"ホットキー解除失敗: ID={hotkey_id}")
                del self._registered_hotkeys[hotkey_id]
                if hotkey_id in self._callback_map:
                    del self._callback_map[hotkey_id]
            return True
        except Exception as e:
            logger.error(f"ホットキー解除エラー: {e}")
            return False

    def set_callback(self, 
                    hotkey_id: int, 
                    callback: Callable[[], None]) -> None:
        """ホットキーのコールバックを設定"""
        self._callback_map[hotkey_id] = callback

    def cleanup(self) -> None:
        """全てのホットキーを解除"""
        for hotkey_id in list(self._registered_hotkeys.keys()):
            self.unregister_hotkey(hotkey_id)
        self._registered_hotkeys.clear()
        self._callback_map.clear()

    def _create_message_handler(self) -> QObject:
        """Windowsメッセージハンドラの作成"""
        class WinEventFilter(QObject):
            def eventFilter(self_filter, watched: QObject, 
                          event: QEvent) -> bool:
                if event.type() == QEvent.Type.WindowSystemEvent:
                    msg = event.message()
                    if msg.message == win32con.WM_HOTKEY:
                        self._handle_hotkey_event(msg.wParam)
                        return True
                return False

        handler = WinEventFilter()
        qApp.installEventFilter(handler)
        return handler

    def _handle_hotkey_event(self, hotkey_id: int) -> None:
        """ホットキーイベントの処理"""
        if hotkey_id in self._callback_map:
            try:
                self._callback_map[hotkey_id]()
            except Exception as e:
                logger.error(f"ホットキーコールバックエラー: {e}")

    def _convert_modifiers(self, modifiers: list[str]) -> int:
        """モディファイアキーの変換"""
        mod_map = {
            "alt": win32con.MOD_ALT,
            "ctrl": win32con.MOD_CONTROL,
            "shift": win32con.MOD_SHIFT,
            "win": win32con.MOD_WIN
        }
        return sum(mod_map.get(mod.lower(), 0) for mod in modifiers)

    def _get_virtual_keycode(self, key: str) -> int:
        """仮想キーコードの取得"""
        vk_map = {
            # 文字キー
            'A': win32con.VK_A, 'B': win32con.VK_B, 'C': win32con.VK_C,
            # ...他のキーマッピング
        }
        return vk_map.get(key.upper(), 0)
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import win32gui
import win32con
from typing import Callable, Dict
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QApplication
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 ホットキーの登録処理
1. モディファイアキーの変換
2. 仮想キーコードの取得
3. 既存ホットキーの解除
4. Win32 APIでの登録
5. 登録情報の保存

### 4.2 イベント検出処理
1. Windowsメッセージの受信
2. ホットキーイベントの識別
3. 対応するコールバックの検索
4. コールバックの実行
5. エラー処理

### 4.3 リソース管理
1. ホットキー登録の追跡
2. コールバックの管理
3. クリーンアップ処理
4. メモリリーク防止
5. エラー状態の管理

## 5. エラー処理

### 5.1 想定されるエラー
- ホットキー登録失敗
- 無効なキー指定
- システムリソース不足
- コールバック実行エラー
- 重複登録

### 5.2 エラー処理方針
- 登録失敗 → エラーログを記録
- 無効なキー → デフォルト値を使用
- リソース不足 → クリーンアップを実行
- コールバックエラー → エラーを抑制
- 重複登録 → 既存の登録を解除

## 6. スレッド安全性

### 6.1 考慮事項
- イベントハンドラの同期
- コールバック実行の保護
- リソースアクセスの制御
- 状態変更の整合性
- 終了処理の安全性

### 6.2 保護メカニズム
- イベントキューの使用
- 排他制御の実装
- 状態の原子的更新
- 安全な終了シーケンス
- リソースの適切な解放

## 7. パフォーマンス考慮事項

### 7.1 最適化ポイント
- イベント処理の効率化
- メモリ使用量の最小化
- コールバック実行の高速化
- リソース管理の最適化
- キャッシュの活用

### 7.2 リソース管理
- 未使用ホットキーの解放
- メモリリークの防止
- システムリソースの解放
- クリーンアップの実施
- 定期的な状態確認

## 8. プラットフォーム依存性

### 8.1 Windows固有の実装
- Win32 API使用
- システムメッセージ処理
- キーコード変換
- エラーコード処理
- リソース管理
